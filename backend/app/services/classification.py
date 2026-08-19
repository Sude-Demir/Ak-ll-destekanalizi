"""Bir müşteri destek talebini önceden tanımlı kategori listesine göre sınıflandırır.

Kategori listesi, bilgi tabanımızdaki (knowledge_base_chunks) Bitext kategorileriyle
birebir aynı tutulur; böylece bir talep sınıflandırıldığında, retrieval'ın aynı
kategori altındaki SSS parçalarını bulması daha tutarlı olur.
"""

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


def classify_ticket(subject: str, body: str) -> str:
    """Talebin konu+içeriğine bakarak CATEGORIES listesinden bir kategori döner.
    LLM listede olmayan bir şey döndürürse FALLBACK_CATEGORY kullanılır."""
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(categories=", ".join(CATEGORIES))
    context = f"Konu: {subject}\nİçerik: {body}"

    raw_response = call_llm(prompt, context)
    category = raw_response.strip().upper()

    return category if category in CATEGORIES else FALLBACK_CATEGORY


def classify_tickets_batch(tickets: list[tuple[int, str, str]]) -> dict[int, str]:
    """`classify_ticket`in toplu (batch) hâli: birden fazla talebi TEK bir LLM
    çağrısında sınıflandırır — geçmişe dönük çok sayıda taleple uğraşırken
    (bkz. backend/classify_backlog.py) günlük istek kotasını tek tek
    sınıflandırmaya göre çok daha az tüketir.

    `tickets`: (ticket_id, subject, body) listesi. Döner: {ticket_id: kategori}
    — girdideki HER id için bir değer garanti edilir; model bir talebi
    atlarsa/bozuk yazarsa sadece o talep için FALLBACK_CATEGORY kullanılır,
    tüm batch iptal olmaz.
    """
    prompt_template = BATCH_PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(categories=", ".join(CATEGORIES), count=len(tickets))

    context = "\n".join(
        f"{i}) Konu: {subject}\n   İçerik: {body}"
        for i, (_ticket_id, subject, body) in enumerate(tickets, start=1)
    )

    raw_response = call_llm(prompt, context)

    parsed_by_index: dict[int, str] = {}
    for line in raw_response.strip().splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        number_part, category_part = line.split(":", 1)
        try:
            index = int(number_part.strip())
        except ValueError:
            continue
        if 1 <= index <= len(tickets):
            parsed_by_index[index] = category_part.strip().upper()

    results: dict[int, str] = {}
    for i, (ticket_id, _subject, _body) in enumerate(tickets, start=1):
        category = parsed_by_index.get(i)
        results[ticket_id] = category if category in CATEGORIES else FALLBACK_CATEGORY
    return results
