import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db.database import get_db
from main import app


def _fake_refresh(ticket) -> None:
    """Gerçek DB'de commit+refresh sonrası dolan otomatik alanları simüle eder
    (id, status default'u, timestamp'ler) — MagicMock db bunları kendiliğinden
    doldurmaz."""
    ticket.id = 1
    ticket.status = "open"
    ticket.created_at = datetime.datetime.now(datetime.timezone.utc)
    ticket.updated_at = ticket.created_at


FAKE_COMPANY = SimpleNamespace(id=1, slug="genel", name="Genel Şirket")

VALID_PAYLOAD = {
    "From": "musteri@example.com",
    "FromFull": {"Email": "musteri@example.com", "Name": "Ayşe Yılmaz"},
    "Subject": "Siparişim gelmedi",
    "TextBody": "Siparişim hala gelmedi, ne zaman gelir acaba?",
    "MailboxHash": "genel",
}


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


@pytest.fixture
def webhook_credentials(monkeypatch):
    monkeypatch.setattr(settings, "webhook_username", "postmark")
    monkeypatch.setattr(settings, "webhook_password", "gizli-sifre")
    return ("postmark", "gizli-sifre")


def test_inbound_email_without_auth_is_rejected(mock_db, webhook_credentials):
    client = TestClient(app)
    res = client.post("/webhooks/inbound-email", json=VALID_PAYLOAD)

    assert res.status_code == 401
    mock_db.add.assert_not_called()


def test_inbound_email_with_wrong_auth_is_rejected(mock_db, webhook_credentials):
    client = TestClient(app)
    res = client.post("/webhooks/inbound-email", json=VALID_PAYLOAD, auth=("postmark", "yanlis-sifre"))

    assert res.status_code == 401
    mock_db.add.assert_not_called()


def test_inbound_email_with_valid_auth_creates_ticket(mock_db, webhook_credentials):
    client = TestClient(app)
    res = client.post("/webhooks/inbound-email", json=VALID_PAYLOAD, auth=webhook_credentials)

    assert res.status_code == 200
    mock_db.add.assert_called_once()
    created_ticket = mock_db.add.call_args[0][0]
    assert created_ticket.company_id == FAKE_COMPANY.id
    assert created_ticket.customer_name == "Ayşe Yılmaz"
    assert created_ticket.customer_email == "musteri@example.com"
    assert created_ticket.subject == "Siparişim gelmedi"
    assert created_ticket.channel == "email"
    mock_db.commit.assert_called_once()


def test_inbound_email_falls_back_to_email_when_name_missing(mock_db, webhook_credentials):
    payload = {**VALID_PAYLOAD, "FromFull": {"Email": "musteri@example.com", "Name": ""}}
    client = TestClient(app)
    res = client.post("/webhooks/inbound-email", json=payload, auth=webhook_credentials)

    assert res.status_code == 200
    created_ticket = mock_db.add.call_args[0][0]
    assert created_ticket.customer_name == "musteri@example.com"


def test_inbound_email_with_unknown_mailbox_hash_is_rejected(mock_db, webhook_credentials):
    """MailboxHash hiçbir şirketin slug'ıyla eşleşmiyorsa (ör. yanlış
    kurulmuş bir inbound adresi) talep oluşturulmamalı."""
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    payload = {**VALID_PAYLOAD, "MailboxHash": "olmayan-sirket"}
    client = TestClient(app)
    res = client.post("/webhooks/inbound-email", json=payload, auth=webhook_credentials)

    assert res.status_code == 400
    mock_db.add.assert_not_called()
