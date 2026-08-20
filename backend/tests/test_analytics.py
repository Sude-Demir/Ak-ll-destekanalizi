from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import require_auth
from app.db.database import SessionLocal, get_db
from app.models import Company, DraftResponse, Ticket
from app.routers.analytics import _daily_ticket_counts, _draft_totals, _ticket_totals
from app.schemas import DraftTotals
from main import app

# --- Router seviyesi testler (mock DB, bkz. tests/test_tickets.py deseni) ---


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
    """`db.execute(...)`'un tek bir çağrısının sonucunu taklit eder — hangi
    metodun (.scalar_one_or_none/.one/.all) çağrılacağı önceden bilinir,
    sadece o metodun dönüş değeri set edilir."""
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def test_non_agent_cannot_access_analytics(mock_db, as_user):
    as_user("user_customer")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

    client = TestClient(app)
    res = client.get("/analytics")

    assert res.status_code == 403


def test_get_analytics_returns_expected_shape(mock_db, as_user):
    as_user("user_agent")
    ticket_row = SimpleNamespace(total=5, answered=2, without_draft=1)
    draft_row = SimpleNamespace(
        total=4, pending=1, approved=2, edited=0, rejected=1, average_confidence=0.7, escalated=1
    )
    daily_rows = [SimpleNamespace(day="2017-11-30", count=3), SimpleNamespace(day="2017-12-01", count=2)]
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(one=ticket_row),
        _result(one=draft_row),
        _result(all=daily_rows),
    ]

    client = TestClient(app)
    res = client.get("/analytics")

    assert res.status_code == 200
    body = res.json()
    assert body["tickets"] == {"total": 5, "answered": 2, "without_draft": 1}
    assert body["drafts"]["average_confidence"] == 0.7
    assert body["drafts"]["approval_rate"] == pytest.approx(2 / 3)  # (approved+edited)/(approved+edited+rejected)
    assert body["daily_ticket_counts"] == [
        {"date": "2017-11-30", "count": 3},
        {"date": "2017-12-01", "count": 2},
    ]


def test_analytics_queries_are_scoped_to_own_company(mock_db, as_user):
    """Kiracı izolasyonu: her toplu sorgu SQL seviyesinde temsilcinin kendi
    company_id'sine göre filtrelenmiş olmalı."""
    as_user("user_agent")
    ticket_row = SimpleNamespace(total=0, answered=0, without_draft=0)
    draft_row = SimpleNamespace(
        total=0, pending=0, approved=0, edited=0, rejected=0, average_confidence=None, escalated=0
    )
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row(company_id=42)),
        _result(one=ticket_row),
        _result(one=draft_row),
        _result(all=[]),
    ]

    client = TestClient(app)
    res = client.get("/analytics")

    assert res.status_code == 200
    # İlk çağrı require_agent'ın kendi sorgusu; sonraki üçü bizim toplu
    # sorgularımız — hepsi company_id=42 taşımalı.
    for call in mock_db.execute.call_args_list[1:]:
        stmt = call[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "42" in compiled


# --- approval_rate hesaplaması (saf birim testi, DB gerekmez) ---


def _draft_totals_with(**overrides) -> DraftTotals:
    base = dict(total=0, pending=0, approved=0, edited=0, rejected=0, average_confidence=None, escalated=0)
    base.update(overrides)
    return DraftTotals(**base)


def test_approval_rate_excludes_pending_from_denominator():
    totals = _draft_totals_with(pending=5, approved=3, edited=1, rejected=1)
    assert totals.approval_rate == pytest.approx((3 + 1) / (3 + 1 + 1))


def test_approval_rate_is_none_when_nothing_decided():
    totals = _draft_totals_with(pending=5)
    assert totals.approval_rate is None


# --- Fonksiyon seviyesi testler (gerçek DB, bkz. tests/test_retrieval.py deseni) ---


@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def two_companies(db_session):
    mine = Company(slug="test-analytics-mine", name="Mine Co")
    other = Company(slug="test-analytics-other", name="Other Co")
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


def _draft(db_session, ticket_id, **overrides):
    base = dict(ticket_id=ticket_id, draft_text="Test taslak", retrieved_context=[], status="pending")
    base.update(overrides)
    draft = DraftResponse(**base)
    db_session.add(draft)
    db_session.commit()
    return draft


def test_ticket_totals_counts_answered_and_without_draft(db_session, two_companies):
    mine, other = two_companies
    answered_ticket = _ticket(db_session, mine.id)
    _draft(db_session, answered_ticket.id, status="approved")
    unanswered_with_draft = _ticket(db_session, mine.id)
    _draft(db_session, unanswered_with_draft.id, status="pending")
    without_draft = _ticket(db_session, mine.id)
    other_companys_ticket = _ticket(db_session, other.id)

    try:
        totals = _ticket_totals(mine.id, db_session)
        assert totals.total == 3  # other_companys_ticket hariç
        assert totals.answered == 1
        assert totals.without_draft == 1
    finally:
        for t in (answered_ticket, unanswered_with_draft, without_draft, other_companys_ticket):
            db_session.query(DraftResponse).filter(DraftResponse.ticket_id == t.id).delete()
            db_session.delete(t)
        db_session.commit()


def test_draft_totals_treats_null_confidence_as_escalated(db_session, two_companies):
    mine, _other = two_companies
    ticket = _ticket(db_session, mine.id)
    _draft(db_session, ticket.id, status="pending", confidence_score=None)
    _draft(db_session, ticket.id, status="approved", confidence_score=0.9)

    try:
        totals = _draft_totals(mine.id, db_session)
        assert totals.total == 2
        assert totals.escalated == 1  # sadece confidence_score=None olan
        assert totals.average_confidence == pytest.approx(0.9)  # avg() NULL'ları yok sayar
    finally:
        db_session.query(DraftResponse).filter(DraftResponse.ticket_id == ticket.id).delete()
        db_session.delete(ticket)
        db_session.commit()


def test_draft_totals_never_crosses_company_boundary(db_session, two_companies):
    mine, other = two_companies
    my_ticket = _ticket(db_session, mine.id)
    _draft(db_session, my_ticket.id, status="approved")
    other_ticket = _ticket(db_session, other.id)
    _draft(db_session, other_ticket.id, status="approved")

    try:
        totals = _draft_totals(mine.id, db_session)
        assert totals.total == 1
    finally:
        for t in (my_ticket, other_ticket):
            db_session.query(DraftResponse).filter(DraftResponse.ticket_id == t.id).delete()
            db_session.delete(t)
        db_session.commit()


def test_daily_ticket_counts_groups_by_day_and_company(db_session, two_companies):
    import datetime

    mine, other = two_companies
    day = datetime.datetime(2017, 11, 20, tzinfo=datetime.timezone.utc)
    same_day = _ticket(db_session, mine.id, created_at=day)
    another_ticket = _ticket(db_session, mine.id, created_at=day)
    other_companys_ticket = _ticket(db_session, other.id, created_at=day)

    try:
        counts = _daily_ticket_counts(mine.id, db_session)
        matching = [c for c in counts if c.date == day.date()]
        assert len(matching) == 1
        assert matching[0].count == 2  # other_companys_ticket sayılmamalı
    finally:
        for t in (same_day, another_ticket, other_companys_ticket):
            db_session.delete(t)
        db_session.commit()
