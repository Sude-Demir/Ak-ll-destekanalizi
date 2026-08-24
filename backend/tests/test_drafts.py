import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

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


def _result(**method_returns) -> MagicMock:
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def _agent_row(company_id=10):
    return SimpleNamespace(id=1, clerk_user_id="user_agent", company_id=company_id, name="Sude Demir")


def _ticket(**overrides):
    base = dict(id=1, company_id=10, subject="Konu", body="Gövde", category="ACCOUNT")
    base.update(overrides)
    return SimpleNamespace(**base)


def _draft_row(**overrides):
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    base = dict(
        id=5,
        ticket_id=1,
        draft_text="AI'nin ilk yazdığı metin",
        ai_original_text="AI'nin ilk yazdığı metin",
        retrieved_context=[],
        confidence_score=0.9,
        used_customer_history=False,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_create_draft_sets_ai_original_text_to_generated_text(mock_db, as_user):
    """Yeni üretilen bir taslakta ai_original_text, draft_text ile aynı
    değeri taşımalı — ikisi de o anki AI çıktısının kopyası (bkz.
    CLAUDE.md 'Temsilcinin taslağı düzenleme farkını kaydetme')."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket(id=1, category="ACCOUNT")

    def _refresh(obj):
        obj.id = 1
        obj.created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        obj.updated_at = obj.created_at

    mock_db.refresh.side_effect = _refresh

    draft_result = DraftResult(draft_text="AI'nin ürettiği ilk metin", retrieved_context=[], confidence_score=0.8)
    with patch("app.routers.drafts.generate_draft", return_value=draft_result):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    body = res.json()
    assert body["draft_text"] == "AI'nin ürettiği ilk metin"
    assert body["ai_original_text"] == "AI'nin ürettiği ilk metin"


def test_edit_draft_updates_draft_text_but_keeps_ai_original_text(mock_db, as_user):
    """Bir temsilci taslağı düzenleyip onaylayınca draft_text değişir, ama
    ai_original_text AI'nin ilk yazdığı hâliyle sabit kalmalı."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.side_effect = [_ticket(id=1), _draft_row()]

    client = TestClient(app)
    res = client.patch(
        "/tickets/1/drafts/5",
        json={"status": "edited", "draft_text": "Temsilcinin düzenlediği metin"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["draft_text"] == "Temsilcinin düzenlediği metin"
    assert body["ai_original_text"] == "AI'nin ilk yazdığı metin"
    assert body["status"] == "edited"


def test_approve_draft_leaves_text_fields_untouched(mock_db, as_user):
    """Düzenlemeden doğrudan onaylamak ne draft_text'i ne ai_original_text'i
    değiştirmemeli."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.side_effect = [_ticket(id=1), _draft_row()]

    client = TestClient(app)
    res = client.patch("/tickets/1/drafts/5", json={"status": "approved"})

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "approved"
    assert body["draft_text"] == "AI'nin ilk yazdığı metin"
    assert body["ai_original_text"] == "AI'nin ilk yazdığı metin"
