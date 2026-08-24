"""Bir müşteri destek talebini önceden tanımlı kategori listesine göre sınıflandırır
ve aynı çağrıda talebin aslında bir satış fırsatı (lead) olup olmadığını tespit eder.

Kategori listesi, bilgi tabanımızdaki (knowledge_base_chunks) Bitext kategorileriyle
birebir aynı tutulur; böylece bir talep sınıflandırıldığında, retrieval'ın aynı
kategori altındaki SSS parçalarını bulması daha tutarlı olur.

Lead tespiti neden ayrı bir servis/LLM çağrısı DEĞİL: Gemini'nin ücretsiz planı
günlük sadece 20 istek veriyor (bkz. CLAUDE.md), bu proje bu kotayı defalarca
zorladı. Sınıflandırma zaten talebin tamamını okuyup bir yargıya varıyor; aynı
çağrıya "bu bir satış fırsatı mı" sorusunu eklemek, talep başına ikinci bir
LLM çağrısına göre kotayı iki katına çıkarmaz.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.llm import call_llm

PROMPT_PATH = Path(__file__).parent / "prompts" / "classification_prompt.txt"
BATCH_PROMPT_PATH = Path(__file__).parent / "prompts" / "batch_classification_prompt.txt"

CATEGORIES = [
    "ACCOUNT",
    "ORDER",
    "REFUND",
    "DELIVERY",
    "PAYMENT",
    "INVOICE",
    "SHIPPING",
    "CANCEL",
    "CONTACT",
    "FEEDBACK",
    "SUBSCRIPTION",
]

FALLBACK_CATEGORY = "OTHER"


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    is_lead: bool


def _parse_single_response(raw_response: str) -> ClassificationResult:
    """`KATEGORİ: <kategori>` / `LEAD: EVET|HAYIR` biçimindeki iki satırı ayrıştırır.
    Etiketler `startswith("KATEGOR")`/`startswith("LEAD")` ile eşleştiriliyor —
    Python'un `.upper()`'ı Türkçe'deki noktalı büyük İ'yi üretmediği için ("kategori"
    -> "KATEGORI", dolayısıyla asla "KATEGORİ" değil), tam eşleşme aramak yerine
    İ harfi içermeyen bir önek kullanmak bu tuzağı baştan eler."""
    category = FALLBACK_CATEGORY
    is_lead = False
    for line in raw_response.strip().splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        label = label.strip().upper()
        value = value.strip()
        if label.startswith("KATEGOR"):
            candidate = value.upper()
            category = candidate if candidate in CATEGORIES else FALLBACK_CATEGORY
        elif label.startswith("LEAD"):
            is_lead = value.upper() == "EVET"
    return ClassificationResult(category=category, is_lead=is_lead)


def classify_ticket(subject: str, body: str) -> ClassificationResult:
    """Talebin konu+içeriğine bakarak hem CATEGORIES listesinden bir kategori
    hem de bir lead (satış fırsatı) tespiti döner. LLM listede olmayan bir
    kategori döndürürse FALLBACK_CATEGORY kullanılır."""
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(categories=", ".join(CATEGORIES))
    context = f"Konu: {subject}\nİçerik: {body}"

    raw_response = call_llm(prompt, context)
    return _parse_single_response(raw_response)


def classify_tickets_batch(tickets: list[tuple[int, str, str]]) -> dict[int, ClassificationResult]:
    """`classify_ticket`in toplu (batch) hâli: birden fazla talebi TEK bir LLM
    çağrısında sınıflandırır — geçmişe dönük çok sayıda taleple uğraşırken
    (bkz. backend/classify_backlog.py) günlük istek kotasını tek tek
    sınıflandırmaya göre çok daha az tüketir.

    `tickets`: (ticket_id, subject, body) listesi. Döner: {ticket_id: ClassificationResult}
    — girdideki HER id için bir değer garanti edilir; model bir talebi
    atlarsa/bozuk yazarsa sadece o talep için FALLBACK_CATEGORY + is_lead=False
    kullanılır, tüm batch iptal olmaz.
    """
    prompt_template = BATCH_PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(categories=", ".join(CATEGORIES), count=len(tickets))

    context = "\n".join(
        f"{i}) Konu: {subject}\n   İçerik: {body}"
        for i, (_ticket_id, subject, body) in enumerate(tickets, start=1)
    )

    raw_response = call_llm(prompt, context)

    parsed_by_index: dict[int, ClassificationResult] = {}
    for line in raw_response.strip().splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        number_part, rest = line.split(":", 1)
        try:
            index = int(number_part.strip())
        except ValueError:
            continue
        if not (1 <= index <= len(tickets)):
            continue
        category_part, _, lead_part = rest.partition("|")
        category = category_part.strip().upper()
        parsed_by_index[index] = ClassificationResult(
            category=category if category in CATEGORIES else FALLBACK_CATEGORY,
            is_lead=lead_part.strip().upper() == "EVET",
        )

    results: dict[int, ClassificationResult] = {}
    for i, (ticket_id, _subject, _body) in enumerate(tickets, start=1):
        results[ticket_id] = parsed_by_index.get(
            i, ClassificationResult(category=FALLBACK_CATEGORY, is_lead=False)
        )
    return results
