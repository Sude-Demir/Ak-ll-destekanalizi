from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from app.auth import require_auth
from app.db.database import get_db
from app.services.draft_generation import DraftResult
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


def _ticket(**overrides):
    base = dict(id=1, company_id=10, subject="Konu", body="Gövde", category="ACCOUNT")
    base.update(overrides)
    return SimpleNamespace(**base)


def _result(**method_returns) -> MagicMock:
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def test_customer_cannot_bulk_generate_drafts(mock_db, as_user):
    as_user("user_customer")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

    client = TestClient(app)
    res = client.post("/tickets/bulk-generate-drafts", json={"ticket_ids": [1]})

    assert res.status_code == 403


def test_bulk_generate_never_touches_another_companys_ticket(mock_db, as_user):
    """Kiracı izolasyonu: başka şirkete ait bir ticket_id, o talep gerçekten
    var olsa bile ASLA `created`e girmemeli — own_ticket_ids kümesinde
    olmayan her id doğrudan `skipped`e düşer, db.get hiç çağrılmaz."""
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[])),  # own_ticket_ids: hiçbiri bu şirkete ait değil
    ]

    client = TestClient(app)
    res = client.post("/tickets/bulk-generate-drafts", json={"ticket_ids": [999]})

    assert res.status_code == 200
    body = res.json()
    assert body["created"] == []
    assert body["skipped"] == [999]
    mock_db.get.assert_not_called()


def test_bulk_generate_skips_ticket_with_existing_pending_draft(mock_db, as_user):
    """Zaten pending taslağı olan bir talep için gereksiz yere ikinci bir
    LLM çağrısı yapılmamalı — skipped'e düşer."""
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[1])),
        _result(scalar=True),  # has_pending
    ]

    client = TestClient(app)
    res = client.post("/tickets/bulk-generate-drafts", json={"ticket_ids": [1]})

    assert res.status_code == 200
    body = res.json()
    assert body["created"] == []
    assert body["skipped"] == [1]


def test_bulk_generate_creates_draft_for_ticket_without_one(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[1])),
        _result(scalar=False),  # has_pending = False
    ]
    mock_db.get.return_value = _ticket(id=1)

    draft_result = DraftResult(draft_text="Merhaba...", retrieved_context=[], confidence_score=0.8)
    with (
        patch("app.routers.drafts.classify_ticket", return_value="ACCOUNT"),
        patch("app.routers.drafts.generate_draft", return_value=draft_result),
    ):
        client = TestClient(app)
        res = client.post("/tickets/bulk-generate-drafts", json={"ticket_ids": [1]})

    assert res.status_code == 200
    body = res.json()
    assert body["created"] == [1]
    assert body["skipped"] == []
    assert body["failed"] == []
    mock_db.add.assert_called_once()
    added_draft = mock_db.add.call_args[0][0]
    assert added_draft.status == "pending"
    assert added_draft.draft_text == "Merhaba..."


def test_bulk_generate_marks_quota_error_as_failed_and_continues(mock_db, as_user):
    """Kota/ağ hatası (google.genai.errors.APIError) o talebi `failed`e
    düşürmeli ama işlemi DURDURMAMALI — kısmi başarı toleranslı."""
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalars=_result(all=[1])),
        _result(scalar=False),
    ]
    mock_db.get.return_value = _ticket(id=1)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "error": {"message": "quota exceeded", "code": 429, "status": "RESOURCE_EXHAUSTED"}
    }
    quota_error = genai_errors.APIError(429, mock_response)
    with (
        patch("app.routers.drafts.classify_ticket", return_value="ACCOUNT"),
        patch("app.routers.drafts.generate_draft", side_effect=quota_error),
    ):
        client = TestClient(app)
        res = client.post("/tickets/bulk-generate-drafts", json={"ticket_ids": [1]})

    assert res.status_code == 200
    body = res.json()
    assert body["created"] == []
    assert body["failed"] == [1]
    mock_db.add.assert_not_called()
