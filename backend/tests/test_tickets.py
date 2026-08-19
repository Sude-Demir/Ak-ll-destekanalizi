import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import get_db
from main import app


@pytest.fixture
def mock_db():
    db = MagicMock()

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def as_user():
    def _set(user_id: str) -> None:
        app.dependency_overrides[require_auth] = lambda: user_id

    yield _set
    app.dependency_overrides.pop(require_auth, None)


def _as_agent(mock_db, company_id=10):
    mock_db.execute.return_value.scalar_one_or_none.return_value = SimpleNamespace(
        id=1, clerk_user_id="user_agent", company_id=company_id, name="Sude Demir"
    )


def _ticket(**overrides):
    now = datetime.datetime.now(datetime.timezone.utc)
    base = dict(
        id=1,
        company_id=10,
        customer_name="Ayşe Yılmaz",
        customer_email="ayse@example.com",
        subject="Kargo gecikti",
        body="Siparişim hala gelmedi.",
        channel="email",
        category=None,
        status="open",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_customer_cannot_list_tickets(mock_db, as_user):
    """`/tickets` bir müşteri hesabından okunamamalı — buradan taleplere ve
    (drafts.py üzerinden) onaylanmamış AI taslaklarına erişilebiliyordu."""
    as_user("user_customer")
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 403


def test_registered_agent_can_list_tickets(mock_db, as_user):
    as_user("user_agent")
    _as_agent(mock_db)
    mock_db.execute.return_value.all.return_value = []

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    assert res.json() == []


def test_list_tickets_includes_answered_flag(mock_db, as_user):
    as_user("user_agent")
    _as_agent(mock_db)
    answered = _ticket(id=1)
    unanswered = _ticket(id=2)
    mock_db.execute.return_value.all.return_value = [(answered, True), (unanswered, False)]

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    body = res.json()
    assert [(t["id"], t["is_answered"]) for t in body] == [(1, True), (2, False)]


def test_list_tickets_query_is_scoped_to_own_company(mock_db, as_user):
    """Kiracı izolasyonu: sorgu SQL seviyesinde temsilcinin kendi
    company_id'sine göre filtrelenmiş olmalı."""
    as_user("user_agent")
    _as_agent(mock_db, company_id=42)
    mock_db.execute.return_value.all.return_value = []

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    stmt = mock_db.execute.call_args_list[-1][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "42" in compiled


def test_get_ticket_includes_answered_flag(mock_db, as_user):
    as_user("user_agent")
    _as_agent(mock_db)
    mock_db.get.return_value = _ticket(id=7)
    mock_db.execute.return_value.scalar.return_value = True

    client = TestClient(app)
    res = client.get("/tickets/7")

    assert res.status_code == 200
    assert res.json()["is_answered"] is True


def test_get_ticket_reports_unanswered(mock_db, as_user):
    as_user("user_agent")
    _as_agent(mock_db)
    mock_db.get.return_value = _ticket(id=8)
    mock_db.execute.return_value.scalar.return_value = False

    client = TestClient(app)
    res = client.get("/tickets/8")

    assert res.status_code == 200
    assert res.json()["is_answered"] is False


def test_get_ticket_404s_for_other_companys_ticket(mock_db, as_user):
    """Kiracı izolasyonu: başka bir şirketin talebi, var olduğu bile
    sızdırılmadan 404 vermeli (403 değil)."""
    as_user("user_agent")
    _as_agent(mock_db, company_id=10)
    mock_db.get.return_value = _ticket(id=99, company_id=999)

    client = TestClient(app)
    res = client.get("/tickets/99")

    assert res.status_code == 404


def test_get_ticket_answered_query_is_scoped_to_this_ticket_only(mock_db, as_user):
    """Regresyon testi: 'is_answered' sorgusu SADECE istenen talebe bakmalı.
    Önceki bir hatada, dış sorguda bir Ticket satırı olmadığı için exists()
    kendi kendine tüm 'tickets' tablosuyla ilişkilendiriyordu — yani "herhangi
    bir talebin onaylı taslağı var mı" sorusuna dönüşüyordu, istenen talebe
    değil."""
    as_user("user_agent")
    _as_agent(mock_db, company_id=10)
    mock_db.get.return_value = _ticket(id=7, company_id=10)
    mock_db.execute.return_value.scalar.return_value = False

    client = TestClient(app)
    res = client.get("/tickets/7")

    assert res.status_code == 200
    stmt = mock_db.execute.call_args_list[-1][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tickets" not in compiled.lower()
    assert "7" in compiled
