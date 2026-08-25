from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import SessionLocal, get_db
from app.models import Company, Notification, Ticket
from app.routers.notifications import _list_own_notifications, _mark_all_read
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


# --- Router seviyesi testler (mock DB) ---


def test_customer_cannot_list_notifications(mock_db, as_user):
    as_user("user_customer")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

    client = TestClient(app)
    res = client.get("/notifications")

    assert res.status_code == 403


def test_list_notifications_query_is_scoped_to_own_company(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row(company_id=42)),
        _result(all=[]),
    ]

    client = TestClient(app)
    res = client.get("/notifications")

    assert res.status_code == 200
    stmt = mock_db.execute.call_args_list[1][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "42" in compiled


def test_mark_all_read_scopes_update_to_own_company(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row(company_id=42)),
        MagicMock(),  # update(...) sonucu, kullanılmıyor
        _result(all=[]),
    ]

    client = TestClient(app)
    res = client.post("/notifications/read-all")

    assert res.status_code == 200
    update_stmt = mock_db.execute.call_args_list[1][0][0]
    compiled = str(update_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "42" in compiled


# --- Fonksiyon seviyesi testler (gerçek DB, bkz. tests/test_analytics.py deseni) ---


@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def two_companies(db_session):
    mine = Company(slug="test-notif-mine", name="Mine Co")
    other = Company(slug="test-notif-other", name="Other Co")
    db_session.add_all([mine, other])
    db_session.commit()
    yield mine, other
    db_session.delete(mine)
    db_session.delete(other)
    db_session.commit()


def _ticket(db_session, company_id, **overrides):
    base = dict(
        company_id=company_id,
        customer_name="Test Müşteri",
        customer_email="test@example.com",
        subject="Test talep",
        body="Test gövde",
        channel="email",
    )
    base.update(overrides)
    ticket = Ticket(**base)
    db_session.add(ticket)
    db_session.commit()
    return ticket


def test_list_notifications_never_crosses_company_boundary(db_session, two_companies):
    mine, other = two_companies
    my_ticket = _ticket(db_session, mine.id, subject="Bana ait talep")
    other_ticket = _ticket(db_session, other.id, subject="Başka şirketin talebi")
    my_notification = Notification(company_id=mine.id, ticket_id=my_ticket.id, type="lead")
    other_notification = Notification(company_id=other.id, ticket_id=other_ticket.id, type="urgent")
    db_session.add_all([my_notification, other_notification])
    db_session.commit()

    try:
        items = _list_own_notifications(mine.id, db_session)
        assert len(items) == 1
        assert items[0].ticket_subject == "Bana ait talep"
        assert items[0].type == "lead"
    finally:
        db_session.delete(my_notification)
        db_session.delete(other_notification)
        db_session.delete(my_ticket)
        db_session.delete(other_ticket)
        db_session.commit()


def test_mark_all_read_only_touches_own_company_unread(db_session, two_companies):
    mine, other = two_companies
    my_ticket = _ticket(db_session, mine.id)
    other_ticket = _ticket(db_session, other.id)
    my_notification = Notification(company_id=mine.id, ticket_id=my_ticket.id, type="lead")
    other_notification = Notification(company_id=other.id, ticket_id=other_ticket.id, type="lead")
    db_session.add_all([my_notification, other_notification])
    db_session.commit()

    try:
        _mark_all_read(mine.id, db_session)
        db_session.refresh(my_notification)
        db_session.refresh(other_notification)
        assert my_notification.read_at is not None
        assert other_notification.read_at is None
    finally:
        db_session.delete(my_notification)
        db_session.delete(other_notification)
        db_session.delete(my_ticket)
        db_session.delete(other_ticket)
        db_session.commit()


# --- drafts.py entegrasyonu: sınıflandırma lead/acil işaretlerse bildirim oluşur ---


def _ticket_row(**overrides):
    base = dict(
        id=1,
        company_id=10,
        subject="Konu",
        body="Gövde",
        category=None,
        customer_name="Test Müşteri",
        customer_email="test@example.com",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _draft_result():
    from app.services.draft_generation import DraftResult

    return DraftResult(draft_text="Merhaba...", retrieved_context=[], confidence_score=0.8)


def _stub_refresh(mock_db) -> None:
    """`db.refresh(draft)` gerçek DB'de id/created_at/updated_at'i doldurur;
    mock'ta bunu taklit etmezsek DraftResponseRead serileştirmesi patlar
    (bkz. tests/test_drafts.py'deki aynı desen)."""
    import datetime as dt

    def _refresh(obj):
        obj.id = 5
        obj.created_at = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        obj.updated_at = obj.created_at

    mock_db.refresh.side_effect = _refresh


def test_create_draft_notifies_when_classification_flags_lead_and_urgent(mock_db, as_user):
    """Bir talep ilk kez sınıflandırılırken lead VE acil olarak işaretlenirse
    iki bildirim (lead + urgent) oluşmalı ve Slack'e de haber verilmeli."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row()
    _stub_refresh(mock_db)

    from app.services.classification import ClassificationResult

    classification = ClassificationResult(category="ORDER", is_lead=True, is_urgent=True)
    with (
        patch("app.routers.drafts.classify_ticket", return_value=classification),
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.send_slack_alert") as mock_slack,
        patch("app.routers.drafts.sync_lead_to_hubspot"),
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    notification_types = {
        call.args[0].type for call in mock_db.add.call_args_list if isinstance(call.args[0], Notification)
    }
    assert notification_types == {"lead", "urgent"}
    mock_slack.assert_called_once()
    assert "Konu" in mock_slack.call_args[0][0]


def test_create_draft_skips_notification_when_not_flagged(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row()
    _stub_refresh(mock_db)

    from app.services.classification import ClassificationResult

    classification = ClassificationResult(category="ORDER", is_lead=False, is_urgent=False)
    with (
        patch("app.routers.drafts.classify_ticket", return_value=classification),
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.send_slack_alert") as mock_slack,
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    assert not any(isinstance(call.args[0], Notification) for call in mock_db.add.call_args_list)
    mock_slack.assert_not_called()


def test_create_draft_does_not_reclassify_or_renotify_already_categorized_ticket(mock_db, as_user):
    """Zaten kategorisi olan bir talep tekrar sınıflandırılmaz — dolayısıyla
    ikinci bir taslak isteğinde tekrar bildirim de üretilmemeli."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket_row(category="ORDER", is_lead=True, is_urgent=False)
    _stub_refresh(mock_db)

    with (
        patch("app.routers.drafts.classify_ticket") as mock_classify,
        patch("app.routers.drafts.generate_draft", return_value=_draft_result()),
        patch("app.routers.drafts.send_slack_alert") as mock_slack,
    ):
        client = TestClient(app)
        res = client.post("/tickets/1/draft")

    assert res.status_code == 200
    mock_classify.assert_not_called()
    mock_slack.assert_not_called()
    assert not any(isinstance(call.args[0], Notification) for call in mock_db.add.call_args_list)
