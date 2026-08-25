import datetime as dt
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import get_db
from app.services.classification import ClassificationResult
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


def _result(**method_returns) -> MagicMock:
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def _agent_row(company_id=10):
    return SimpleNamespace(id=1, clerk_user_id="user_agent", company_id=company_id, name="Sude Demir")


def _ticket_row(**overrides):
    base = dict(
        id=1,
        company_id=10,
        subject="Toplu sipariş talebi",
        body="Gövde",
        category=None,
        customer_name="Ada Lovelace",
        customer_email="ada@example.com",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _draft_result():
    return DraftResult(draft_text="Merhaba...", retrieved_context=[], confidence_score=0.8)


def _stub_refresh(mock_db) -> None:
    def _refresh(obj):
        obj.id = 5
        obj.created_at = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        obj.updated_at = obj.created_at

    mock_db.refresh.side_effect = _refresh


def test_create_draft_syncs_to_hubspot_when_classified_as_lead(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row()
    _stub_refresh(mock_db)

    classification = ClassificationResult(category="ORDER", is_lead=True, is_urgent=False)
    with (
        patch("app.routers.drafts.classify_ticket", return_value=classification),
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.send_slack_alert"),
        patch("app.routers.drafts.sync_lead_to_hubspot") as mock_sync,
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    mock_sync.assert_called_once_with("Ada Lovelace", "ada@example.com", "Toplu sipariş talebi")


def test_create_draft_does_not_sync_to_hubspot_when_not_a_lead(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row()
    _stub_refresh(mock_db)

    classification = ClassificationResult(category="ORDER", is_lead=False, is_urgent=True)
    with (
        patch("app.routers.drafts.classify_ticket", return_value=classification),
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.send_slack_alert"),
        patch("app.routers.drafts.sync_lead_to_hubspot") as mock_sync,
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    mock_sync.assert_not_called()


def test_create_draft_does_not_resync_already_classified_ticket(mock_db, as_user):
    """Zaten kategorisi olan bir talep tekrar sınıflandırılmaz — dolayısıyla
    HubSpot'a da tekrar senkronize edilmez (aynı lead için yinelenen deal
    oluşmasın diye)."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row(category="ORDER", is_lead=True)
    _stub_refresh(mock_db)

    with (
        patch("app.routers.drafts.classify_ticket") as mock_classify,
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.sync_lead_to_hubspot") as mock_sync,
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    mock_classify.assert_not_called()
    mock_sync.assert_not_called()
