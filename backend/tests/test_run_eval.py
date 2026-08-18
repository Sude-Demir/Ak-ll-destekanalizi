from unittest.mock import MagicMock, patch

from google.genai import errors

import run_eval
from run_eval import EvalResult, print_summary, run_eval as run_eval_fn


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


def _api_error() -> errors.APIError:
    response = MagicMock()
    response.json.side_effect = Exception("no body")
    response.text = "quota exceeded"
    response.reason = "RESOURCE_EXHAUSTED"
    return errors.ClientError(429, response)


def test_run_eval_marks_correct_and_incorrect_predictions(tmp_path):
    db = MagicMock()
    examples = [_fake_example(1, "REFUND"), _fake_example(2, "ORDER")]
    ticket1, ticket2 = MagicMock(id=1), MagicMock(id=2)
    db.scalars.return_value = examples
    db.get.side_effect = [ticket1, ticket2]

    with (
        patch.object(run_eval, "PROGRESS_FILE", tmp_path / "progress.json"),
        patch("run_eval.time.sleep"),
        patch("run_eval.classify_ticket", side_effect=["REFUND", "PAYMENT"]),
        patch("run_eval.generate_draft", side_effect=[_fake_draft(0.8), _fake_draft(0.3)]),
    ):
        results, completed = run_eval_fn(db)

    assert completed is True
    results.sort(key=lambda r: r.ticket_id)
    assert results[0].category_correct is True
    assert results[0].needs_escalation is False
    assert results[1].category_correct is False  # ORDER beklenirken PAYMENT tahmin edildi
    assert results[1].needs_escalation is True  # 0.3 < ESCALATION_THRESHOLD (0.5)


def test_run_eval_skips_missing_ticket(tmp_path):
    db = MagicMock()
    db.scalars.return_value = [_fake_example(99, "REFUND")]
    db.get.return_value = None  # ticket bulunamadı

    with (
        patch.object(run_eval, "PROGRESS_FILE", tmp_path / "progress.json"),
        patch("run_eval.time.sleep"),
        patch("run_eval.classify_ticket") as mock_classify,
        patch("run_eval.generate_draft") as mock_generate,
    ):
        results, completed = run_eval_fn(db)

    assert results == []
    assert completed is True
    mock_classify.assert_not_called()
    mock_generate.assert_not_called()


def test_run_eval_stops_gracefully_on_api_error_and_keeps_partial_progress(tmp_path):
    db = MagicMock()
    examples = [_fake_example(1, "REFUND"), _fake_example(2, "ORDER")]
    ticket1, ticket2 = MagicMock(id=1), MagicMock(id=2)
    db.scalars.return_value = examples
    db.get.side_effect = [ticket1, ticket2]

    with (
        patch.object(run_eval, "PROGRESS_FILE", tmp_path / "progress.json"),
        patch("run_eval.time.sleep"),
        patch("run_eval.classify_ticket", side_effect=["REFUND", _api_error()]),
        patch("run_eval.generate_draft", side_effect=[_fake_draft(0.8)]),
    ):
        results, completed = run_eval_fn(db)

    assert completed is False
    assert len(results) == 1
    assert results[0].ticket_id == 1


def test_run_eval_resumes_from_saved_progress_without_recalling_llm(tmp_path):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text(
        '[{"ticket_id": 1, "expected_category": "REFUND", "predicted_category": "REFUND", '
        '"category_correct": true, "confidence_score": 0.8, "needs_escalation": false, "draft_text": "x"}]',
        encoding="utf-8",
    )

    db = MagicMock()
    examples = [_fake_example(1, "REFUND"), _fake_example(2, "ORDER")]
    db.scalars.return_value = examples
    db.get.return_value = MagicMock(id=2)

    with (
        patch.object(run_eval, "PROGRESS_FILE", progress_file),
        patch("run_eval.time.sleep"),
        patch("run_eval.classify_ticket", return_value="ORDER") as mock_classify,
        patch("run_eval.generate_draft", return_value=_fake_draft(0.9)),
    ):
        results, completed = run_eval_fn(db)

    assert completed is True
    assert len(results) == 2  # onceki 1 + yeni 1
    mock_classify.assert_called_once()  # ticket 1 icin tekrar cagrilmadi


def test_print_summary_reports_accuracy(capsys):
    results = [
        EvalResult(1, "REFUND", "REFUND", True, 0.8, False, "x"),
        EvalResult(2, "ORDER", "PAYMENT", False, 0.3, True, "y"),
    ]

    print_summary(results, all_completed=True)

    out = capsys.readouterr().out
    assert "1/2" in out  # dogruluk: 2 orneginin 1'i dogru
    assert "ticket 2: beklenen=ORDER tahmin=PAYMENT" in out


def test_print_summary_marks_partial_when_not_completed(capsys):
    results = [EvalResult(1, "REFUND", "REFUND", True, 0.8, False, "x")]

    print_summary(results, all_completed=False)

    out = capsys.readouterr().out
    assert "KISMİ" in out
