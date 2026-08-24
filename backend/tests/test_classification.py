from unittest.mock import patch

from app.services import classification
from app.services.classification import ClassificationResult


def test_classify_ticket_returns_known_category():
    response = "KATEGORİ: REFUND\nLEAD: HAYIR"
    with patch("app.services.classification.call_llm", return_value=response) as mock_call:
        result = classification.classify_ticket(
            subject="İadem ne zaman yapılacak?",
            body="10 gün önce iade talebi oluşturdum, hâlâ paramı alamadım.",
        )

    assert result == ClassificationResult(category="REFUND", is_lead=False)
    args, kwargs = mock_call.call_args
    assert "REFUND" in args[0]  # kategori listesi prompt'a enjekte edilmiş olmalı


def test_classify_ticket_falls_back_when_response_not_in_list():
    with patch("app.services.classification.call_llm", return_value="KATEGORİ: BLAH BLAH\nLEAD: HAYIR"):
        result = classification.classify_ticket(subject="?", body="?")

    assert result.category == classification.FALLBACK_CATEGORY


def test_classify_ticket_normalizes_case_and_whitespace():
    with patch("app.services.classification.call_llm", return_value="  kategori:  refund  \nlead: hayir\n"):
        result = classification.classify_ticket(subject="?", body="?")

    assert result.category == "REFUND"


def test_classify_ticket_detects_lead():
    response = "KATEGORİ: OTHER\nLEAD: EVET"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_ticket(
            subject="Kurumsal teklif",
            body="200 kişilik ekibimiz için toplu alım yapmak istiyoruz, indirim var mı?",
        )

    assert result == ClassificationResult(category="OTHER", is_lead=True)


def test_classify_ticket_defaults_lead_to_false_when_missing():
    with patch("app.services.classification.call_llm", return_value="KATEGORİ: REFUND"):
        result = classification.classify_ticket(subject="?", body="?")

    assert result.is_lead is False


def _tickets(n):
    return [(i, f"Konu {i}", f"İçerik {i}") for i in range(1, n + 1)]


def test_classify_tickets_batch_maps_each_line_to_its_ticket():
    response = "1: REFUND | HAYIR\n2: ORDER | EVET\n3: DELIVERY | HAYIR"
    with patch("app.services.classification.call_llm", return_value=response) as mock_call:
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {
        1: ClassificationResult(category="REFUND", is_lead=False),
        2: ClassificationResult(category="ORDER", is_lead=True),
        3: ClassificationResult(category="DELIVERY", is_lead=False),
    }
    args, _kwargs = mock_call.call_args
    assert "3" in args[0]  # {count} prompt'a enjekte edilmiş olmalı


def test_classify_tickets_batch_falls_back_for_missing_line():
    response = "1: REFUND | HAYIR\n3: DELIVERY | HAYIR"  # 2 numara eksik
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {
        1: ClassificationResult(category="REFUND", is_lead=False),
        2: ClassificationResult(category=classification.FALLBACK_CATEGORY, is_lead=False),
        3: ClassificationResult(category="DELIVERY", is_lead=False),
    }


def test_classify_tickets_batch_falls_back_for_invalid_category():
    response = "1: REFUND | HAYIR\n2: BLAH BLAH | HAYIR\n3: DELIVERY | HAYIR"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result[2] == ClassificationResult(category=classification.FALLBACK_CATEGORY, is_lead=False)


def test_classify_tickets_batch_ignores_noise_lines():
    response = "Elbette, işte sonuçlar:\n1: REFUND | HAYIR\n2: ORDER | HAYIR\n\n3: DELIVERY | HAYIR"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert result == {
        1: ClassificationResult(category="REFUND", is_lead=False),
        2: ClassificationResult(category="ORDER", is_lead=False),
        3: ClassificationResult(category="DELIVERY", is_lead=False),
    }


def test_classify_tickets_batch_defaults_lead_to_false_when_pipe_missing():
    response = "1: REFUND\n2: ORDER\n3: DELIVERY"
    with patch("app.services.classification.call_llm", return_value=response):
        result = classification.classify_tickets_batch(_tickets(3))

    assert all(r.is_lead is False for r in result.values())
