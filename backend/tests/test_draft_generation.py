from unittest.mock import MagicMock, patch

from app.services import draft_generation


def _fake_chunk(chunk_id: int, category: str, intent: str) -> MagicMock:
    chunk = MagicMock()
    chunk.id = chunk_id
    chunk.category = category
    chunk.intent = intent
    chunk.question = f"question-{intent}"
    chunk.answer = f"answer-{intent}"
    return chunk


def test_generate_draft_returns_text_and_traceable_context():
    ticket = MagicMock(subject="İadem gelmedi", body="Param ne zaman iade edilecek?")
    fake_chunks_with_distances = [(_fake_chunk(1, "REFUND", "get_refund"), 0.1)]

    with (
        patch(
            "app.services.draft_generation.retrieve_relevant_chunks_with_distances",
            return_value=fake_chunks_with_distances,
        ) as mock_retrieve,
        patch(
            "app.services.draft_generation.call_llm_with_tools", return_value="Merhaba, iadeniz..."
        ) as mock_llm,
    ):
        result = draft_generation.generate_draft(ticket, db=MagicMock())

    assert result.draft_text == "Merhaba, iadeniz..."
    assert result.retrieved_context == [
        {
            "chunk_id": 1,
            "category": "REFUND",
            "intent": "get_refund",
            "question": "question-get_refund",
            "answer": "answer-get_refund",
        }
    ]
    assert result.confidence_score == 0.9  # 1 - 0.1
    mock_retrieve.assert_called_once()
    mock_llm.assert_called_once()


def test_generate_draft_with_no_matching_chunks_still_returns_result():
    ticket = MagicMock(subject="?", body="?")

    with (
        patch("app.services.draft_generation.retrieve_relevant_chunks_with_distances", return_value=[]),
        patch("app.services.draft_generation.call_llm_with_tools", return_value="Genel bir cevap."),
    ):
        result = draft_generation.generate_draft(ticket, db=MagicMock())

    assert result.draft_text == "Genel bir cevap."
    assert result.retrieved_context == []
    assert result.confidence_score == 0.0


def test_generate_draft_reports_tool_not_used_when_model_never_calls_it():
    """Model taslağı yazarken get_customer_ticket_history aracını hiç
    çağırmazsa (fake call_llm_with_tools bunu simüle eder — gerçek modelin
    çağırdığı senaryo aşağıdaki testte), used_customer_history False kalmalı."""
    ticket = MagicMock(subject="?", body="?")

    with (
        patch("app.services.draft_generation.retrieve_relevant_chunks_with_distances", return_value=[]),
        patch("app.services.draft_generation.call_llm_with_tools", return_value="Genel bir cevap."),
    ):
        result = draft_generation.generate_draft(ticket, db=MagicMock())

    assert result.used_customer_history is False


def test_customer_history_tool_queries_other_tickets_of_same_customer():
    """google-genai SDK'sının otomatik fonksiyon çağırma özelliği gerçek
    modeli gerektirdiği için, burada modelin aracı ÇAĞIRDIĞI senaryoyu
    simüle ediyoruz: call_llm_with_tools'a iletilen `tools` listesindeki
    fonksiyonu doğrudan biz çağırıp, doğru müşteri/şirkete göre filtrelenmiş
    bir sorgu ürettiğini ve used_customer_history'yi True'ya çevirdiğini
    doğruluyoruz."""
    ticket = MagicMock(id=1, customer_email="ayse@example.com", company_id=10, subject="?", body="?")

    other_ticket = MagicMock(subject="Kargo nerede?", category="DELIVERY")
    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [other_ticket]

    def fake_call_llm_with_tools(prompt, context, tools):
        (get_customer_ticket_history,) = tools
        tool_output = get_customer_ticket_history()
        assert "Kargo nerede?" in tool_output
        return "Taslak metni"

    with (
        patch("app.services.draft_generation.retrieve_relevant_chunks_with_distances", return_value=[]),
        patch("app.services.draft_generation.call_llm_with_tools", side_effect=fake_call_llm_with_tools),
    ):
        result = draft_generation.generate_draft(ticket, db=mock_db)

    assert result.used_customer_history is True
    filters = mock_db.execute.call_args[0][0]
    compiled = str(filters.compile(compile_kwargs={"literal_binds": True}))
    assert "ayse@example.com" in compiled
    assert "10" in compiled


def test_customer_history_tool_handles_no_other_tickets():
    ticket = MagicMock(id=1, customer_email="ayse@example.com", company_id=10, subject="?", body="?")

    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    def fake_call_llm_with_tools(prompt, context, tools):
        (get_customer_ticket_history,) = tools
        tool_output = get_customer_ticket_history()
        assert "başka bir talebi bulunmuyor" in tool_output
        return "Taslak metni"

    with (
        patch("app.services.draft_generation.retrieve_relevant_chunks_with_distances", return_value=[]),
        patch("app.services.draft_generation.call_llm_with_tools", side_effect=fake_call_llm_with_tools),
    ):
        draft_generation.generate_draft(ticket, db=mock_db)
