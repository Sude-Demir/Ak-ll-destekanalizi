"""Bir taslağın ne kadar güvenilir olduğunu, retrieval'da bulunan en yakın SSS
parçasının benzerlik skoruna bakarak hesaplar.

Mantık: bilgi tabanında talebe gerçekten yakın bir içerik varsa taslak o içeriğe
sıkı sıkıya dayanabilir (yüksek güven); en yakın içerik bile alakasızsa taslak
büyük ölçüde LLM'in kendi bilgisine dayanır (düşük güven, eskalasyona aday).
"""

MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0

# Bu eşiğin altındaki taslaklar "dikkatli incele" olarak işaretlenir
# (bkz. needs_escalation, app.schemas.DraftResponseRead.needs_escalation).
ESCALATION_THRESHOLD = 0.5


def compute_confidence(distances: list[float]) -> float:
    """`distances`, retrieval'ın döndürdüğü pgvector kosinüs mesafeleridir (0 =
    birebir aynı yön/en benzer, bkz. app.services.retrieval). Eşleşen hiçbir
    SSS parçası yoksa (distances boşsa) en düşük güven skorunu döner.

    Sadece en yakın (en küçük mesafeli) parça dikkate alınır: taslağın
    dayandığı en iyi kaynak ne kadar alakalıysa güven o kadar yüksektir.
    """
    if not distances:
        return MIN_CONFIDENCE

    closest_distance = min(distances)
    similarity = 1.0 - closest_distance
    return max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, similarity))


def needs_escalation(confidence_score: float) -> bool:
    """Güven skoru eşiğin altındaysa taslağın bir temsilci tarafından normalden
    daha dikkatli incelenmesi gerektiğini belirtir."""
    return confidence_score < ESCALATION_THRESHOLD
