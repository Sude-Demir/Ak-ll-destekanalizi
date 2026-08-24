import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import get_db
from app.services.kb_suggestion_generation import KbSuggestionResult
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
    base = dict(id=1, company_id=10, subject="Konu", body="Gövde", category="SHIPPING")
    base.update(overrides)
    return SimpleNamespace(**base)


def _answered_draft(**overrides):
    base = dict(id=9, ticket_id=1, draft_text="Onaylı yanıt metni", status="approved")
    base.update(overrides)
    return SimpleNamespace(**base)


def _suggestion_row(**overrides):
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    base = dict(
        id=7,
        ticket_id=1,
        company_id=10,
        question="Soru?",
        answer="Cevap.",
        category="SHIPPING",
        intent="kargo",
        status="pending",
        kb_chunk_id=None,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_create_kb_suggestion_requires_answered_draft(mock_db, as_user):
    """Hiç onaylı/düzenlenmiş yanıtı olmayan bir talep için öneri üretilemez
    — üretecek bir 'nihai yanıt' yok."""
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar_one_or_none=None),
    ]
    mock_db.get.return_value = _ticket()

    client = TestClient(app)
    res = client.post("/tickets/1/kb-suggestion")

    assert res.status_code == 400


def test_create_kb_suggestion_never_touches_another_companys_ticket(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row(company_id=10))]
    mock_db.get.return_value = _ticket(id=1, company_id=999)

    client = TestClient(app)
    res = client.post("/tickets/1/kb-suggestion")

    assert res.status_code == 404


def test_create_kb_suggestion_builds_from_latest_answered_draft(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar_one_or_none=_answered_draft(draft_text="Kargonuz 2 gün içinde gelir.")),
    ]
    mock_db.get.return_value = _ticket(category="SHIPPING")

    def _refresh(obj):
        obj.id = 7
        obj.created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        obj.updated_at = obj.created_at

    mock_db.refresh.side_effect = _refresh

    suggestion_result = KbSuggestionResult(
        question="Kargom ne zaman gelir?", answer="2 gün içinde gelir.", intent="kargo_takibi"
    )
    with patch("app.routers.kb_suggestions.generate_kb_suggestion", return_value=suggestion_result) as mock_generate:
        client = TestClient(app)
        res = client.post("/tickets/1/kb-suggestion")

    assert res.status_code == 200
    body = res.json()
    assert body["question"] == "Kargom ne zaman gelir?"
    assert body["category"] == "SHIPPING"
    assert body["status"] == "pending"
    mock_generate.assert_called_once_with("Konu", "Gövde", "Kargonuz 2 gün içinde gelir.")


def test_approve_kb_suggestion_creates_knowledge_base_chunk_and_embeds(mock_db, as_user):
    """Onaylanınca gerçek bir knowledge_base_chunks kaydı oluşmalı ve
    soru+cevap embed edilmeli (bkz. scripts/embed_kb.py ile aynı desen)."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.side_effect = [_ticket(), _suggestion_row()]

    with patch("app.routers.kb_suggestions.embed_text", return_value=[0.1, 0.2]) as mock_embed:
        client = TestClient(app)
        res = client.patch("/tickets/1/kb-suggestions/7", json={"status": "approved"})

    assert res.status_code == 200
    assert res.json()["status"] == "approved"
    mock_embed.assert_called_once_with("Soru?\nCevap.")
    mock_db.add.assert_called_once()
    added_chunk = mock_db.add.call_args[0][0]
    assert added_chunk.question == "Soru?"
    assert added_chunk.source == "ticket_suggestion"
    assert added_chunk.embedding == [0.1, 0.2]


def test_approve_kb_suggestion_uses_edited_question_and_answer(mock_db, as_user):
    """Onaylamadan önce soru/cevap düzenlenmişse (DraftStatusUpdate ile aynı
    desen), gerçek SSS kaydı düzenlenmiş metni kullanmalı."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.side_effect = [_ticket(), _suggestion_row()]

    with patch("app.routers.kb_suggestions.embed_text", return_value=[0.1]) as mock_embed:
        client = TestClient(app)
        res = client.patch(
            "/tickets/1/kb-suggestions/7",
            json={"status": "approved", "question": "Düzenlenmiş soru?", "answer": "Düzenlenmiş cevap."},
        )

    assert res.status_code == 200
    assert res.json()["question"] == "Düzenlenmiş soru?"
    mock_embed.assert_called_once_with("Düzenlenmiş soru?\nDüzenlenmiş cevap.")


def test_reject_kb_suggestion_does_not_create_knowledge_base_chunk(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.side_effect = [_ticket(), _suggestion_row()]

    client = TestClient(app)
    res = client.patch("/tickets/1/kb-suggestions/7", json={"status": "rejected"})

    assert res.status_code == 200
    assert res.json()["status"] == "rejected"
    mock_db.add.assert_not_called()
