import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import get_db
from main import app


def _fake_ticket_refresh(ticket) -> None:
    ticket.id = 7
    ticket.status = "open"
    ticket.category = None
    ticket.created_at = datetime.datetime.now(datetime.timezone.utc)
    ticket.updated_at = ticket.created_at


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.refresh.side_effect = _fake_ticket_refresh

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def as_user():
    """Testin, `require_auth`'un belirtilen Clerk kullanıcı kimliğiyle giriş
    yapılmış gibi davranmasını sağlar (gerçek Clerk token'ı doğrulanmaz)."""

    def _set(user_id: str) -> None:
        app.dependency_overrides[require_auth] = lambda: user_id

    yield _set
    app.dependency_overrides.pop(require_auth, None)


def test_read_me_reports_registered_agent(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.return_value.scalar_one_or_none.return_value = SimpleNamespace(
        id=1, clerk_user_id="user_agent", name="Sude Demir"
    )

    client = TestClient(app)
    res = client.get("/me")

    assert res.status_code == 200
    assert res.json() == {"clerk_user_id": "user_agent", "is_agent": True, "name": "Sude Demir"}


def test_read_me_reports_customer_when_not_in_agents_table(mock_db, as_user, monkeypatch):
    as_user("user_customer")
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    monkeypatch.setattr(
        "app.routers.me.fetch_user_profile", lambda clerk_user_id: ("Ayşe Yılmaz", "ayse@example.com")
    )

    client = TestClient(app)
    res = client.get("/me")

    assert res.status_code == 200
    assert res.json() == {"clerk_user_id": "user_customer", "is_agent": False, "name": "Ayşe Yılmaz"}


def test_create_my_ticket_uses_clerk_profile_not_client_input(mock_db, as_user, monkeypatch):
    as_user("user_customer")
    monkeypatch.setattr(
        "app.routers.me.fetch_user_profile", lambda clerk_user_id: ("Ayşe Yılmaz", "ayse@example.com")
    )
    mock_db.execute.return_value.scalars.return_value.first.return_value = None

    client = TestClient(app)
    res = client.post("/me/tickets", json={"subject": "Kargo gecikti", "body": "Siparişim gelmedi."})

    assert res.status_code == 200
    created = mock_db.add.call_args[0][0]
    assert created.customer_name == "Ayşe Yılmaz"
    assert created.customer_email == "ayse@example.com"
    assert created.submitted_by_user_id == "user_customer"
    assert created.channel == "portal"
    assert res.json()["answer"] is None


def test_list_my_tickets_query_is_scoped_to_own_clerk_id(mock_db, as_user):
    as_user("user_x")
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    client = TestClient(app)
    res = client.get("/me/tickets")

    assert res.status_code == 200
    assert res.json() == []

    stmt = mock_db.execute.call_args_list[0][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "'user_x'" in compiled


def test_get_my_ticket_404s_for_someone_elses_ticket(mock_db, as_user):
    as_user("user_x")
    mock_db.get.return_value = SimpleNamespace(id=5, submitted_by_user_id="someone_else")

    client = TestClient(app)
    res = client.get("/me/tickets/5")

    assert res.status_code == 404


def test_get_my_ticket_never_queries_pending_or_rejected_drafts(mock_db, as_user):
    """En kritik test: onaylanmamış/reddedilmiş bir taslak müşteriye asla
    gösterilmemeli (bkz. CLAUDE.md "İnsan onaylı akış"). Bunu sadece mock
    dönüş değeriyle değil, gerçekten kurulan sorgunun WHERE koşulunu
    inceleyerek doğruluyoruz."""
    as_user("user_x")
    mock_db.get.return_value = SimpleNamespace(
        id=5,
        submitted_by_user_id="user_x",
        subject="Kargo gecikti",
        body="Siparişim gelmedi.",
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    mock_db.execute.return_value.scalars.return_value.first.return_value = None

    client = TestClient(app)
    res = client.get("/me/tickets/5")

    assert res.status_code == 200
    assert res.json()["answer"] is None

    stmt = mock_db.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "'approved'" in compiled
    assert "'edited'" in compiled
    assert "'pending'" not in compiled
    assert "'rejected'" not in compiled


def test_get_my_ticket_surfaces_approved_answer(mock_db, as_user):
    as_user("user_x")
    mock_db.get.return_value = SimpleNamespace(
        id=5,
        submitted_by_user_id="user_x",
        subject="Kargo gecikti",
        body="Siparişim gelmedi.",
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    mock_db.execute.return_value.scalars.return_value.first.return_value = "Merhaba, siparişiniz yola çıktı."

    client = TestClient(app)
    res = client.get("/me/tickets/5")

    assert res.status_code == 200
    assert res.json()["answer"] == "Merhaba, siparişiniz yola çıktı."
