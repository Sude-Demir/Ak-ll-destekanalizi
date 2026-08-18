from unittest.mock import MagicMock, patch

from run_eval import EvalResult, print_summary, run_eval


def _fake_example(ticket_id: int, expected_category: str) -> MagicMock:
    example = MagicMock()
    example.ticket_id = ticket_id
    example.expected_category = expected_category
    return example


def _fake_draft(confidence_score: float, draft_text: str = "taslak") -> MagicMock:
    draft = MagicMock()
    draft.confidence_score = confidence_score
    draft.draft_text = draft_text
    return draft


def test_run_eval_marks_correct_and_incorrect_predictions():
    db = MagicMock()
    examples = [_fake_example(1, "REFUND"), _fake_example(2, "ORDER")]
    ticket1, ticket2 = MagicMock(id=1), MagicMock(id=2)
    db.scalars.return_value = examples
    db.get.side_effect = [ticket1, ticket2]

    with (
        patch("run_eval.classify_ticket", side_effect=["REFUND", "PAYMENT"]),
        patch("run_eval.generate_draft", side_effect=[_fake_draft(0.8), _fake_draft(0.3)]),
    ):
        results = run_eval(db)

    assert results[0].category_correct is True
    assert results[0].needs_escalation is False
    assert results[1].category_correct is False  # ORDER beklenirken PAYMENT tahmin edildi
    assert results[1].needs_escalation is True  # 0.3 < ESCALATION_THRESHOLD (0.5)


def test_run_eval_skips_missing_ticket():
    db = MagicMock()
    db.scalars.return_value = [_fake_example(99, "REFUND")]
    db.get.return_value = None  # ticket bulunamadı

    with (
        patch("run_eval.classify_ticket") as mock_classify,
        patch("run_eval.generate_draft") as mock_generate,
    ):
        results = run_eval(db)

    assert results == []
    mock_classify.assert_not_called()
    mock_generate.assert_not_called()


def test_print_summary_reports_accuracy(capsys):
    results = [
        EvalResult(1, "REFUND", "REFUND", True, 0.8, False, "x"),
        EvalResult(2, "ORDER", "PAYMENT", False, 0.3, True, "y"),
    ]

    print_summary(results)

    out = capsys.readouterr().out
    assert "1/2" in out  # dogruluk: 2 orneginin 1'i dogru
    assert "ticket 2: beklenen=ORDER tahmin=PAYMENT" in out
