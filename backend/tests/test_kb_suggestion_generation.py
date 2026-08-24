from unittest.mock import patch

from app.services.kb_suggestion_generation import KbSuggestionResult, generate_kb_suggestion


def test_generate_kb_suggestion_parses_labeled_response():
    raw = (
        "SORU:\n"
        "Kargom ne zaman gelir?\n"
        "CEVAP:\n"
        "Kargonuz kargoya verildikten sonra ortalama 2-3 iş günü içinde\n"
        "adresinize ulaşır.\n"
        "KOD:\n"
        "kargo_takibi\n"
    )
    with patch("app.services.kb_suggestion_generation.call_llm", return_value=raw):
        result = generate_kb_suggestion("Kargom nerede?", "Kargom hala gelmedi.", "Kargonuz yolda, 2-3 gün içinde gelir.")

    assert result == KbSuggestionResult(
        question="Kargom ne zaman gelir?",
        answer="Kargonuz kargoya verildikten sonra ortalama 2-3 iş günü içinde\nadresinize ulaşır.",
        intent="kargo_takibi",
    )


def test_generate_kb_suggestion_falls_back_when_labels_missing():
    """Model beklenen etiket formatını hiç kullanmazsa (bozuk çıktı), sınıflandırmadaki
    FALLBACK_CATEGORY ile aynı prensiple, tüm işlem iptal olmak yerine makul
    varsayılanlara düşülmeli."""
    with patch("app.services.kb_suggestion_generation.call_llm", return_value="beklenmedik serbest metin"):
        result = generate_kb_suggestion("Konu", "Gövde", "Nihai yanıt metni")

    assert result.question == "Konu"
    assert result.answer == "Nihai yanıt metni"
    assert result.intent == "genel"


def test_generate_kb_suggestion_ignores_colons_inside_answer_content():
    """CEVAP içeriğinde iki nokta üst üste geçmesi (örn. 'Not: ...') satır
    tabanlı etiket eşleşmesini bozmamalı — sadece TAM olarak 'CEVAP:' olan
    bir satır yeni bir bölüm başlatmalı."""
    raw = "SORU:\nSoru metni\nCEVAP:\nNot: bu önemli bir detaydır.\nKOD:\nkod_1\n"
    with patch("app.services.kb_suggestion_generation.call_llm", return_value=raw):
        result = generate_kb_suggestion("Konu", "Gövde", "Yanıt")

    assert result.answer == "Not: bu önemli bir detaydır."
