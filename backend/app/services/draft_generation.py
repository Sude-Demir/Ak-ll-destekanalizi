"""Bir müşteri talebi için, bilgi tabanından bulunan ilgili içeriğe dayanan bir
yanıt TASLAĞI üretir.

ÖNEMLİ: Bu fonksiyonun ürettiği taslak hiçbir zaman doğrudan müşteriye
gönderilmez (bkz. CLAUDE.md "İnsan onaylı akış" kuralı) — bir temsilcinin
onay kuyruğuna (draft_responses tablosu, status="pending") düşer.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseChunk, Ticket
from app.services.confidence import compute_confidence
from app.services.llm import call_llm_with_tools
from app.services.retrieval import DEFAULT_TOP_K, retrieve_relevant_chunks_with_distances

PROMPT_PATH = Path(__file__).parent / "prompts" / "draft_prompt.txt"

# Bir taslak yazarı, tek bir müşterinin geçmişte kaç talep açtığına bakarken
# bunu makul bir sayıda tutmalı — tüm geçmişi context'e boğmak ne gerekli ne
# de ucuz (her ek satır, LLM'e giden token sayısını artırır).
MAX_CUSTOMER_HISTORY_ITEMS = 5


@dataclass
class DraftResult:
    draft_text: str
    retrieved_context: list[dict]  # her taslağın hangi SSS parçalarına dayandığının kaydı
    confidence_score: float  # bkz. app.services.confidence.compute_confidence
    # Model, taslağı yazarken get_customer_ticket_history aracını gerçekten
    # çağırdı mı (bkz. aşağıdaki generate_draft) — izlenebilirlik için.
    used_customer_history: bool = False


def generate_draft(ticket: Ticket, db: Session, top_k: int = DEFAULT_TOP_K) -> DraftResult:
    query_text = f"{ticket.subject}\n{ticket.body}"
    chunks_with_distances = retrieve_relevant_chunks_with_distances(
        query_text, ticket.company_id, db, top_k=top_k
    )
    chunks: list[KnowledgeBaseChunk] = [chunk for chunk, _distance in chunks_with_distances]
    confidence_score = compute_confidence([distance for _chunk, distance in chunks_with_distances])

    kb_context = "\n\n".join(
        f"SSS {i}:\nSoru: {c.question}\nCevap: {c.answer}" for i, c in enumerate(chunks, start=1)
    )
    context = f"Müşteri talebi:\n{query_text}\n\nİlgili SSS içeriği:\n{kb_context}"

    # Modele gerçek bir "araç" (tool) sunulur — statik SSS metninin ötesinde,
    # bu müşterinin bu şirkete başka ne yazdığına KENDİSİ karar verip bakabilir
    # (bkz. app.services.llm.call_llm_with_tools). ticket/db, fonksiyonun
    # closure'ından (kapatma) alınıyor; modelin bunları parametre olarak
    # doldurmasına gerek yok/izin verilmiyor — model sadece "bu aracı çağır"
    # diyebilir, hangi müşteri/şirket olduğuna biz karar veriyoruz.
    used_customer_history = False

    def get_customer_ticket_history() -> str:
        """Bu talebi açan müşterinin, bu şirkete daha önce yazdığı DİĞER
        taleplerin kısa bir listesini döner (varsa konu ve kategorileriyle).
        Müşterinin aynı sorunu tekrar tekrar yazıp yazmadığını anlamak ya da
        geçmişte bu müşteriyle ilgili bir bağlam olup olmadığını görmek
        istediğinde bu aracı çağır."""
        nonlocal used_customer_history
        used_customer_history = True

        other_tickets = db.execute(
            select(Ticket)
            .filter(
                Ticket.customer_email == ticket.customer_email,
                Ticket.company_id == ticket.company_id,
                Ticket.id != ticket.id,
            )
            .order_by(Ticket.created_at.desc())
            .limit(MAX_CUSTOMER_HISTORY_ITEMS)
        ).scalars().all()

        if not other_tickets:
            return "Bu müşterinin bu şirkete başka bir talebi bulunmuyor."

        lines = [f"- {t.subject} (kategori: {t.category or 'sınıflandırılmadı'})" for t in other_tickets]
        return "Bu müşterinin bu şirkete başka talepleri:\n" + "\n".join(lines)

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    draft_text = call_llm_with_tools(prompt, context, tools=[get_customer_ticket_history])

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

    return DraftResult(
        draft_text=draft_text,
        retrieved_context=retrieved_context,
        confidence_score=confidence_score,
        used_customer_history=used_customer_history,
    )
