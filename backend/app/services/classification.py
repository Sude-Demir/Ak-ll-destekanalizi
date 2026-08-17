"""Bir müşteri destek talebini önceden tanımlı kategori listesine göre sınıflandırır.

Kategori listesi, bilgi tabanımızdaki (knowledge_base_chunks) Bitext kategorileriyle
birebir aynı tutulur; böylece bir talep sınıflandırıldığında, retrieval'ın aynı
kategori altındaki SSS parçalarını bulması daha tutarlı olur.
"""

from pathlib import Path

from app.services.llm import call_llm

PROMPT_PATH = Path(__file__).parent / "prompts" / "classification_prompt.txt"

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
