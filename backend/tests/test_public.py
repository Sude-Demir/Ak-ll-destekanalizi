import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from main import app

VALID_PAYLOAD = {
    "customer_name": "Ayşe Yılmaz",
    "customer_email": "ayse@example.com",
    "subject": "Siparişim gelmedi",
    "body": "Siparişim hala gelmedi, ne zaman gelir acaba?",
}

FAKE_COMPANY = SimpleNamespace(id=1, slug="genel", name="Genel Şirket")


def _fake_refresh(ticket) -> None:
    ticket.id = 1
    ticket.status = "open"
    ticket.category = None
    ticket.created_at = datetime.datetime.now(datetime.timezone.utc)
    ticket.updated_at = ticket.created_at


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.refresh.side_effect = _fake_refresh
    db.execute.return_value.scalar_one_or_none.return_value = FAKE_COMPANY

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


def test_get_company_returns_name(mock_db):
    client = TestClient(app)
    res = client.get("/public/companies/genel")

    assert res.status_code == 200
    assert res.json() == {"slug": "genel", "name": "Genel Şirket"}


def test_get_company_404s_for_unknown_slug(mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    client = TestClient(app)
    res = client.get("/public/companies/olmayan-sirket")

    assert res.status_code == 404


def test_submit_support_request_requires_no_auth(mock_db):
    client = TestClient(app)
    res = client.post("/public/companies/genel/tickets", json=VALID_PAYLOAD)

    assert res.status_code == 200
    mock_db.add.assert_called_once()
    created_ticket = mock_db.add.call_args[0][0]
    assert created_ticket.company_id == FAKE_COMPANY.id
    assert created_ticket.customer_name == "Ayşe Yılmaz"
    assert created_ticket.customer_email == "ayse@example.com"
    assert created_ticket.channel == "form"
    mock_db.commit.assert_called_once()


def test_submit_support_request_404s_for_unknown_company(mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    client = TestClient(app)
    res = client.post("/public/companies/olmayan-sirket/tickets", json=VALID_PAYLOAD)

    assert res.status_code == 404
    mock_db.add.assert_not_called()


def test_submit_support_request_rejects_invalid_email(mock_db):
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "customer_email": "gecersiz-eposta"}
    res = client.post("/public/companies/genel/tickets", json=payload)

    assert res.status_code == 422
    mock_db.add.assert_not_called()


def test_submit_support_request_rejects_empty_body(mock_db):
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "body": ""}
    res = client.post("/public/companies/genel/tickets", json=payload)

    assert res.status_code == 422
    mock_db.add.assert_not_called()
