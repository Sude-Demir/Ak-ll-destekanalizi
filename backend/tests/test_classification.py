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
