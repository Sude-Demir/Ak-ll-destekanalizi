import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import get_db
from main import app


def _fake_invite_refresh(invite) -> None:
    invite.id = 1
    invite.accepted_at = getattr(invite, "accepted_at", None)
    invite.created_at = datetime.datetime.now(datetime.timezone.utc)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.refresh.side_effect = _fake_invite_refresh

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


def _agent(clerk_user_id="user_agent", company_id=1, name="Sude Demir"):
    return SimpleNamespace(id=1, clerk_user_id=clerk_user_id, company_id=company_id, name=name)


def _invite(**overrides):
    now = datetime.datetime.now(datetime.timezone.utc)
    base = dict(
        id=1,
        token="abc123",
        company_id=1,
        email="aday@example.com",
        name="Aday Kişi",
        invited_by="user_agent",
        accepted_at=None,
        expires_at=now + datetime.timedelta(days=7),
        created_at=now,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_customer_cannot_create_invite(mock_db, as_user):
    as_user("user_customer")
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    client = TestClient(app)
    res = client.post("/agent-invites", json={"email": "aday@example.com"})

    assert res.status_code == 403
    mock_db.add.assert_not_called()


def test_agent_can_create_invite(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.return_value.scalar_one_or_none.return_value = _agent()

    client = TestClient(app)
    res = client.post("/agent-invites", json={"email": "aday@example.com", "name": "Aday Kişi"})

    assert res.status_code == 200
    created = mock_db.add.call_args[0][0]
    assert created.email == "aday@example.com"
    assert created.invited_by == "user_agent"
    assert created.company_id == 1
    assert res.json()["status"] == "pending"


def test_list_invites_query_is_scoped_to_own_company(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.return_value.scalar_one_or_none.return_value = _agent(company_id=42)
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    client = TestClient(app)
    res = client.get("/agent-invites")

    assert res.status_code == 200
    stmt = mock_db.execute.call_args_list[-1][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "42" in compiled


def test_accept_rejects_expired_invite(mock_db, as_user):
    as_user("user_customer")
    expired = _invite(expires_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
    mock_db.execute.return_value.scalar_one_or_none.return_value = expired

    client = TestClient(app)
    res = client.post("/agent-invites/abc123/accept")

    assert res.status_code == 410
    mock_db.add.assert_not_called()


def test_accept_rejects_already_used_invite(mock_db, as_user):
    as_user("user_customer")
    used = _invite(accepted_at=datetime.datetime.now(datetime.timezone.utc))
    mock_db.execute.return_value.scalar_one_or_none.return_value = used

    client = TestClient(app)
    res = client.post("/agent-invites/abc123/accept")

    assert res.status_code == 400
    mock_db.add.assert_not_called()


def test_accept_rejects_email_mismatch(mock_db, as_user, monkeypatch):
    """En kritik test: linki ele geçiren biri, davet edilen e-postayla eşleşmeyen
    bir hesapla temsilci olamamalı."""
    as_user("user_customer")
    mock_db.execute.return_value.scalar_one_or_none.return_value = _invite(email="aday@example.com")
    monkeypatch.setattr(
        "app.routers.agent_invites.fetch_user_profile",
        lambda clerk_user_id: ("Başka Kişi", "baska@example.com"),
    )

    client = TestClient(app)
    res = client.post("/agent-invites/abc123/accept")

    assert res.status_code == 403
    mock_db.add.assert_not_called()


def test_accept_creates_agent_on_email_match(mock_db, as_user, monkeypatch):
    as_user("user_new_agent")
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [
        _invite(email="aday@example.com"),  # token lookup
        None,  # existing agent lookup -> not an agent yet
    ]
    monkeypatch.setattr(
        "app.routers.agent_invites.fetch_user_profile",
        lambda clerk_user_id: ("Aday Kişi", "aday@example.com"),
    )

    client = TestClient(app)
    res = client.post("/agent-invites/abc123/accept")

    assert res.status_code == 200
    created = mock_db.add.call_args[0][0]
    assert created.clerk_user_id == "user_new_agent"
    assert created.name == "Aday Kişi"
    assert created.company_id == 1  # davetin şirketi, kabul edenin değil
