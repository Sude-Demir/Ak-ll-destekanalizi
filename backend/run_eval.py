"""Mevcut sınıflandırma + taslak üretim sistemini `eval_examples` tablosundaki
elle işaretlenmiş örneklere karşı çalıştırıp bir doğruluk raporu üretir.

CLAUDE.md'nin "gerçek müşteri verisiyle, önce eval seti üzerinde test
edilmeden yeni bir prompt/model değişikliği yapma" kuralının kontrol
mekanizması budur — bir prompt/model değişikliği yapmadan önce ve yaptıktan
sonra bu script'i çalıştırıp sonuçları karşılaştır.

Her eval örneği için gerçek Gemini API'ye 2 çağrı yapılır (sınıflandırma +
taslak üretimi), yani 34 örnek ~68 API çağrısı demektir — birkaç dakika sürebilir.

Kullanım (backend/ dizininden, sanal ortam aktifken):
    python run_eval.py
"""

import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import EvalExample, Ticket
from app.services.classification import classify_ticket
from app.services.confidence import ESCALATION_THRESHOLD
from app.services.draft_generation import generate_draft


@dataclass
class EvalResult:
    ticket_id: int
    expected_category: str
    predicted_category: str
    category_correct: bool
    confidence_score: float
    needs_escalation: bool
    draft_text: str


def run_eval(db: Session) -> list[EvalResult]:
    examples = list(db.scalars(select(EvalExample).order_by(EvalExample.id)))
    results = []

    for i, example in enumerate(examples, start=1):
        ticket = db.get(Ticket, example.ticket_id)
        if ticket is None:
            print(f"[{i}/{len(examples)}] UYARI: ticket {example.ticket_id} bulunamadı, atlanıyor")
            continue

        predicted_category = classify_ticket(ticket.subject, ticket.body)
        draft = generate_draft(ticket, db)

        results.append(
            EvalResult(
                ticket_id=ticket.id,
                expected_category=example.expected_category,
                predicted_category=predicted_category,
                category_correct=predicted_category == example.expected_category,
                confidence_score=draft.confidence_score,
                needs_escalation=draft.confidence_score < ESCALATION_THRESHOLD,
                draft_text=draft.draft_text,
            )
        )
        mark = "OK" if predicted_category == example.expected_category else "FARKLI"
        print(f"[{i}/{len(examples)}] ticket {ticket.id}: beklenen={example.expected_category} tahmin={predicted_category} ({mark}) guven={draft.confidence_score:.2f}")

        # Ücretsiz katmanın dakikalık istek kotasını (gemini-2.5-flash için 5
        # istek/dakika) aşmamak için ticket başına kısa bir bekleme.
        if i < len(examples):
            time.sleep(8)

    return results


def print_summary(results: list[EvalResult]) -> None:
    total = len(results)
    correct = sum(1 for r in results if r.category_correct)
    avg_confidence = sum(r.confidence_score for r in results) / total
    escalated = sum(1 for r in results if r.needs_escalation)

    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    print(f"Toplam örnek: {total}")
    print(f"Kategori doğruluğu: {correct}/{total} (%{100 * correct / total:.1f})")
    print(f"Ortalama güven skoru: {avg_confidence:.2f}")
    print(f"Eskalasyona düşen (düşük güven): {escalated}/{total}")

    wrong = [r for r in results if not r.category_correct]
    if wrong:
        print("\nYanlış sınıflandırılanlar:")
        for r in wrong:
            print(f"  ticket {r.ticket_id}: beklenen={r.expected_category} tahmin={r.predicted_category}")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        eval_results = run_eval(session)
        print_summary(eval_results)
    finally:
        session.close()
