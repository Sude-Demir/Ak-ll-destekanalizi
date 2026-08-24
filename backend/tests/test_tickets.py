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


def _agent_row(company_id=10):
    return SimpleNamespace(id=1, clerk_user_id="user_agent", company_id=company_id, name="Sude Demir")


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
        assigned_agent_id=None,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _result(**method_returns) -> MagicMock:
    """`db.execute(...)`'un tek bir çağrısının sonucunu taklit eder — hangi
    metodun (.scalar_one_or_none/.scalar/.all/.one) çağrılacağı önceden
    bilinir, sadece o metodun dönüş değeri set edilir."""
    result = MagicMock()
    for method, value in method_returns.items():
        getattr(result, method).return_value = value
    return result


def _list_tickets_side_effect(agent_row, count=0, items=None, summary=None, category_counts=None):
    """`GET /tickets`'in 5 execute() çağrısı için sırayla dönecek mock
    sonuçlarını üretir: require_agent, count, items, overall summary,
    category_counts (bkz. app.routers.tickets.list_tickets)."""
    items = items or []
    summary = summary or SimpleNamespace(total=0, open_count=0, classified_count=0, resolved_count=0)
    category_counts = category_counts or []
    return [
        _result(scalar_one_or_none=agent_row),
        _result(scalar=count),
        _result(all=items),
        _result(one=summary),
        _result(all=category_counts),
    ]


def test_customer_cannot_list_tickets(mock_db, as_user):
    """`/tickets` bir müşteri hesabından okunamamalı — buradan taleplere ve
    (drafts.py üzerinden) onaylanmamış AI taslaklarına erişilebiliyordu."""
    as_user("user_customer")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=None)]

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 403


def test_registered_agent_can_list_tickets(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_list_tickets_includes_answered_and_pending_draft(mock_db, as_user):
    as_user("user_agent")
    answered = _ticket(id=1)
    unanswered = _ticket(id=2)
    items = [(answered, True, None, None), (unanswered, False, 5, None)]
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row(), count=2, items=items)

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    body = res.json()["items"]
    assert [(t["id"], t["is_answered"], t["pending_draft_id"]) for t in body] == [
        (1, True, None),
        (2, False, 5),
    ]


def test_list_tickets_query_is_scoped_to_own_company(mock_db, as_user):
    """Kiracı izolasyonu: her sorgu (count/items/summary/category_counts)
    SQL seviyesinde temsilcinin kendi company_id'sine göre filtrelenmiş
    olmalı (require_agent'ın kendi sorgusu hariç)."""
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row(company_id=42))

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    for call in mock_db.execute.call_args_list[1:]:
        stmt = call[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "42" in compiled


def test_list_tickets_search_filters_subject_customer_body(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"q": "iphone"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "iphone" in count_sql.lower()


def test_list_tickets_category_filter_excludes_summary_and_category_counts(mock_db, as_user):
    """Regresyon testi: kategori filtresi sadece count/items sorgularına
    uygulanmalı — overall summary ve category_counts HER ZAMAN şirketin
    TAMAMINI göstermeli (bkz. TicketListRead docstring'i), aksi halde
    CategoryFilterBar/CategoryDistribution filtre uygulanınca yanlış sayı
    gösterir."""
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"category": "REFUND"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    summary_sql = str(mock_db.execute.call_args_list[3][0][0].compile(compile_kwargs={"literal_binds": True}))
    category_counts_sql = str(mock_db.execute.call_args_list[4][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "REFUND" in count_sql
    assert "REFUND" not in summary_sql
    assert "REFUND" not in category_counts_sql


def test_list_tickets_channel_filter(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"channel": "form"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "'form'" in count_sql


def test_list_tickets_answered_filter_true_uses_exists(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"is_answered": "true"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "EXISTS" in count_sql
    assert "NOT (EXISTS" not in count_sql


def test_list_tickets_answered_filter_false_negates_exists(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"is_answered": "false"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "NOT (EXISTS" in count_sql


def test_list_tickets_sort_oldest_orders_ascending(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"sort": "oldest"})

    assert res.status_code == 200
    items_sql = str(mock_db.execute.call_args_list[2][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY tickets.created_at ASC" in items_sql


def test_list_tickets_lead_filter(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"is_lead": "true"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "tickets.is_lead = true" in count_sql


def test_list_tickets_urgent_filter(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"is_urgent": "true"})

    assert res.status_code == 200
    count_sql = str(mock_db.execute.call_args_list[1][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "tickets.is_urgent = true" in count_sql


def test_list_tickets_sort_defaults_to_newest(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets")

    assert res.status_code == 200
    items_sql = str(mock_db.execute.call_args_list[2][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY tickets.created_at DESC" in items_sql


def test_list_tickets_priority_sort_orders_by_urgency_then_confidence(mock_db, as_user):
    """Öncelikli kuyruk: önce acil talepler, sonra pending taslağı en düşük
    güvenli (en belirsiz) olanlar önce gelmeli — HİÇBİR ŞEYİ otomatik
    onaylamaz, sadece sıralamayı belirler."""
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"sort": "priority"})

    assert res.status_code == 200
    items_sql = str(mock_db.execute.call_args_list[2][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY tickets.is_urgent DESC" in items_sql
    assert "NULLS LAST" in items_sql


def test_list_tickets_pagination_applies_offset(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = _list_tickets_side_effect(_agent_row())

    client = TestClient(app)
    res = client.get("/tickets", params={"page": 2})

    assert res.status_code == 200
    items_sql = str(mock_db.execute.call_args_list[2][0][0].compile(compile_kwargs={"literal_binds": True}))
    assert "OFFSET 50" in items_sql
    assert res.json()["page"] == 2


def test_get_ticket_includes_answered_and_pending_draft(mock_db, as_user):
    as_user("user_agent")
    mock_db.get.return_value = _ticket(id=7)
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar=True),
        _result(scalar=5),
    ]

    client = TestClient(app)
    res = client.get("/tickets/7")

    assert res.status_code == 200
    body = res.json()
    assert body["is_answered"] is True
    assert body["pending_draft_id"] == 5


def test_get_ticket_reports_unanswered_and_no_pending_draft(mock_db, as_user):
    as_user("user_agent")
    mock_db.get.return_value = _ticket(id=8)
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar=False),
        _result(scalar=None),
    ]

    client = TestClient(app)
    res = client.get("/tickets/8")

    assert res.status_code == 200
    body = res.json()
    assert body["is_answered"] is False
    assert body["pending_draft_id"] is None


def test_get_ticket_404s_for_other_companys_ticket(mock_db, as_user):
    """Kiracı izolasyonu: başka bir şirketin talebi, var olduğu bile
    sızdırılmadan 404 vermeli (403 değil)."""
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row(company_id=10))]
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
    mock_db.get.return_value = _ticket(id=7, company_id=10)
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row(company_id=10)),
        _result(scalar=False),
        _result(scalar=None),
    ]

    client = TestClient(app)
    res = client.get("/tickets/7")

    assert res.status_code == 200
    stmt = mock_db.execute.call_args_list[1][0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tickets" not in compiled.lower()


def test_claim_ticket_assigns_to_current_agent(mock_db, as_user):
    as_user("user_agent")
    ticket = _ticket(id=5, assigned_agent_id=None)
    mock_db.get.return_value = ticket
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar=False),  # is_answered
        _result(scalar=None),  # pending_draft_id
        _result(scalar="Sude Demir"),  # assigned_agent_name lookup
    ]

    client = TestClient(app)
    res = client.patch("/tickets/5/assignment", json={"claim": True})

    assert res.status_code == 200
    assert ticket.assigned_agent_id == 1  # _agent_row()'un id'si
    body = res.json()
    assert body["assigned_agent_id"] == 1
    assert body["assigned_agent_name"] == "Sude Demir"


def test_unclaim_ticket_clears_assignment(mock_db, as_user):
    as_user("user_agent")
    ticket = _ticket(id=5, assigned_agent_id=9)
    mock_db.get.return_value = ticket
    mock_db.execute.side_effect = [
        _result(scalar_one_or_none=_agent_row()),
        _result(scalar=False),
        _result(scalar=None),
        # assigned_agent_id None olunca assigned_agent_name sorgusu hiç atılmaz.
    ]

    client = TestClient(app)
    res = client.patch("/tickets/5/assignment", json={"claim": False})

    assert res.status_code == 200
    assert ticket.assigned_agent_id is None
    body = res.json()
    assert body["assigned_agent_id"] is None
    assert body["assigned_agent_name"] is None


def test_claim_ticket_404s_for_another_companys_ticket(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row(company_id=10))]
    mock_db.get.return_value = _ticket(id=5, company_id=999)

    client = TestClient(app)
    res = client.patch("/tickets/5/assignment", json={"claim": True})

    assert res.status_code == 404


def test_list_ticket_messages_404s_for_another_companys_ticket(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row(company_id=10))]
    mock_db.get.return_value = _ticket(id=5, company_id=999)

    client = TestClient(app)
    res = client.get("/tickets/5/messages")

    assert res.status_code == 404


def test_create_ticket_message_uses_agent_name_and_sender_type(mock_db, as_user):
    as_user("user_agent")
    mock_db.execute.side_effect = [_result(scalar_one_or_none=_agent_row())]
    mock_db.get.return_value = _ticket(id=5)

    def _refresh(obj):
        obj.id = 1
        obj.created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

    mock_db.refresh.side_effect = _refresh

    client = TestClient(app)
    res = client.post("/tickets/5/messages", json={"body": "Merhaba, talebinizi inceliyoruz."})

    assert res.status_code == 200
    body = res.json()
    assert body["sender_type"] == "agent"
    assert body["sender_name"] == "Sude Demir"  # _agent_row()'un adı
    assert body["body"] == "Merhaba, talebinizi inceliyoruz."
    mock_db.add.assert_called_once()
