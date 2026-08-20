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


def _agent_row(company_id=10):
    return SimpleNamespace(id=1, clerk_user_id="user_agent", company_id=company_id, name="Sude Demir")


def _result(**method_returns) -> MagicMock:
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def test_customer_cannot_bulk_approve(mock_db, as_user):
    as_user("user_customer")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

    client = TestClient(app)
    res = client.post("/tickets/bulk-approve", json={"ticket_ids": [1]})

    assert res.status_code == 403


def test_bulk_approve_never_approves_another_companys_ticket(mock_db, as_user):
    """Kiracı izolasyonu: başka şirkete ait bir ticket_id, o talebin gerçekten
    var olup olmadığına bakılmaksızın ASLA `approved`e girmemeli — sadece
    kendi şirketinin talep id'lerinden oluşan `own_ticket_ids` kümesinde
    olmayan her id doğrudan `skipped`e düşer."""
    as_user("user_agent")
    own_draft = SimpleNamespace(id=50, ticket_id=1, status="pending")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[1])),  # own_ticket_ids: sadece talep 1 bu şirkete ait
        _result(scalar_one_or_none=own_draft),  # talep 1'in pending taslağı
    ]

    client = TestClient(app)
    res = client.post("/tickets/bulk-approve", json={"ticket_ids": [1, 999]})

    assert res.status_code == 200
    body = res.json()
    assert body["approved"] == [1]
    assert body["skipped"] == [999]
    assert own_draft.status == "approved"


def test_bulk_approve_skips_ticket_without_pending_draft(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[2])),
        _result(scalar_one_or_none=None),  # talep 2'nin pending taslağı yok
    ]

    client = TestClient(app)
    res = client.post("/tickets/bulk-approve", json={"ticket_ids": [2]})

    assert res.status_code == 200
    body = res.json()
    assert body["approved"] == []
    assert body["skipped"] == [2]
