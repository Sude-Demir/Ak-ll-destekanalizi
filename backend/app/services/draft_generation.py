"""Bir müşteri talebi için, bilgi tabanından bulunan ilgili içeriğe dayanan bir
yanıt TASLAĞI üretir.

ÖNEMLİ: Bu fonksiyonun ürettiği taslak hiçbir zaman doğrudan müşteriye
gönderilmez (bkz. CLAUDE.md "İnsan onaylı akış" kuralı) — bir temsilcinin
onay kuyruğuna (draft_responses tablosu, status="pending") düşer.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import KnowledgeBaseChunk, Ticket
from app.services.llm import call_llm
from app.services.retrieval import DEFAULT_TOP_K, retrieve_relevant_chunks

PROMPT_PATH = Path(__file__).parent / "prompts" / "draft_prompt.txt"


@dataclass
class DraftResult:
    draft_text: str
    retrieved_context: list[dict]  # her taslağın hangi SSS parçalarına dayandığının kaydı


def generate_draft(ticket: Ticket, db: Session, top_k: int = DEFAULT_TOP_K) -> DraftResult:
    query_text = f"{ticket.subject}\n{ticket.body}"
    chunks: list[KnowledgeBaseChunk] = retrieve_relevant_chunks(query_text, db, top_k=top_k)

    kb_context = "\n\n".join(
        f"SSS {i}:\nSoru: {c.question}\nCevap: {c.answer}" for i, c in enumerate(chunks, start=1)
    )
    context = f"Müşteri talebi:\n{query_text}\n\nİlgili SSS içeriği:\n{kb_context}"

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    draft_text = call_llm(prompt, context)

    # İzlenebilirlik için: taslak hangi SSS parçalarına dayandı (bkz. CLAUDE.md
    # "Her taslak, hangi bilgi tabanı parçalarına dayandığını kaydeder").
    # id'nin yanında içeriğin bir kopyasını da saklıyoruz; ileride KB güncellenirse
    # bile taslağın o anda gerçekte neye dayandığı kaybolmasın diye.
    retrieved_context = [
        {
            "chunk_id": c.id,
            "category": c.category,
            "intent": c.intent,
            "question": c.question,
            "answer": c.answer,
        }
        for c in chunks
    ]

    return DraftResult(draft_text=draft_text, retrieved_context=retrieved_context)
