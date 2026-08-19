from unittest.mock import patch

from app.services import classification


def test_classify_ticket_returns_known_category():
    with patch("app.services.classification.call_llm", return_value="REFUND") as mock_call:
        category = classification.classify_ticket(
            subject="İadem ne zaman yapılacak?",
            body="10 gün önce iade talebi oluşturdum, hâlâ paramı alamadım.",
        )

    assert category == "REFUND"
    args, kwargs = mock_call.call_args
    assert "REFUND" in args[0]  # kategori listesi prompt'a enjekte edilmiş olmalı


def test_classify_ticket_falls_back_when_response_not_in_list():
    with patch("app.services.classification.call_llm", return_value="BLAH BLAH"):
        category = classification.classify_ticket(subject="?", body="?")

    assert category == classification.FALLBACK_CATEGORY


def test_classify_ticket_normalizes_case_and_whitespace():
    with patch("app.services.classification.call_llm", return_value="  refund\n"):
        category = classification.classify_ticket(subject="?", body="?")

    assert category == "REFUND"


def _tickets(n):
    return [(i, f"Konu {i}", f"İçerik {i}") for i in range(1, n + 1)]


def test_classify_tickets_batch_maps_each_line_to_its_ticket():
    response = "1: REFUND\n2: ORDER\n3: DELIVERY"
    with patch("app.services.classification.call_llm", return_value=response) as mock_call:
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {1: "REFUND", 2: "ORDER", 3: "DELIVERY"}
    args, _kwargs = mock_call.call_args
    assert "3" in args[0]  # {count} prompt'a enjekte edilmiş olmalı


def test_classify_tickets_batch_falls_back_for_missing_line():
    response = "1: REFUND\n3: DELIVERY"  # 2 numara eksik
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {1: "REFUND", 2: classification.FALLBACK_CATEGORY, 3: "DELIVERY"}


def test_classify_tickets_batch_falls_back_for_invalid_category():
    response = "1: REFUND\n2: BLAH BLAH\n3: DELIVERY"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {1: "REFUND", 2: classification.FALLBACK_CATEGORY, 3: "DELIVERY"}


def test_classify_tickets_batch_ignores_noise_lines():
    response = "Elbette, işte sonuçlar:\n1: REFUND\n2: ORDER\n\n3: DELIVERY"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {1: "REFUND", 2: "ORDER", 3: "DELIVERY"}
