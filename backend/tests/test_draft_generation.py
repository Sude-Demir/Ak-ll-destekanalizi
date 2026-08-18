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
        patch("app.services.draft_generation.call_llm", return_value="Merhaba, iadeniz...") as mock_llm,
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
        patch("app.services.draft_generation.call_llm", return_value="Genel bir cevap."),
    ):
        result = draft_generation.generate_draft(ticket, db=MagicMock())

    assert result.draft_text == "Genel bir cevap."
    assert result.retrieved_context == []
    assert result.confidence_score == 0.0
