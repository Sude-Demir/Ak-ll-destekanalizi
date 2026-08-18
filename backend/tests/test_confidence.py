from app.services import confidence


def test_compute_confidence_with_no_matches_returns_min_confidence():
    assert confidence.compute_confidence([]) == confidence.MIN_CONFIDENCE


def test_compute_confidence_uses_closest_distance():
    # en yakın (en küçük) mesafe 0.2 -> benzerlik 0.8
    assert confidence.compute_confidence([0.2, 0.6, 0.9]) == 0.8


def test_compute_confidence_clamps_to_valid_range():
    # pgvector kosinüs mesafesi teorik olarak 2'ye kadar çıkabilir (zıt yön);
    # bu durumda benzerlik negatif olur, MIN_CONFIDENCE'a sabitlenmeli.
    assert confidence.compute_confidence([1.5]) == confidence.MIN_CONFIDENCE


def test_needs_escalation_below_threshold():
    assert confidence.needs_escalation(confidence.ESCALATION_THRESHOLD - 0.01) is True


def test_needs_escalation_at_or_above_threshold():
    assert confidence.needs_escalation(confidence.ESCALATION_THRESHOLD) is False
    assert confidence.needs_escalation(confidence.ESCALATION_THRESHOLD + 0.1) is False
