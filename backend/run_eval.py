"""Mevcut sınıflandırma + taslak üretim sistemini `eval_examples` tablosundaki
elle işaretlenmiş örneklere karşı çalıştırıp bir doğruluk raporu üretir.

CLAUDE.md'nin "gerçek müşteri verisiyle, önce eval seti üzerinde test
edilmeden yeni bir prompt/model değişikliği yapma" kuralının kontrol
mekanizması budur — bir prompt/model değişikliği yapmadan önce ve yaptıktan
sonra bu script'i çalıştırıp sonuçları karşılaştır.

Her eval örneği için gerçek Gemini API'ye 2 çağrı yapılır (sınıflandırma +
taslak üretimi), yani 34 örnek ~68 API çağrısı demektir. Gemini'nin ücretsiz
planında gemini-2.5-flash için GÜNLÜK sadece 20 istek hakkı var — yani tek
günde tamamlanamayabilir. Bu yüzden script ilerlemeyi `eval_progress.json`'a
kaydeder; kota dolup script durursa, tekrar çalıştırıldığında kaldığı yerden
devam eder (zaten tamamlanmış örnekleri tekrar API'ye sormaz).

Kullanım (backend/ dizininden, sanal ortam aktifken):
    python run_eval.py
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from google.genai import errors
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import EvalExample, Ticket
from app.services.classification import classify_ticket
from app.services.confidence import ESCALATION_THRESHOLD
from app.services.draft_generation import generate_draft

PROGRESS_FILE = Path(__file__).parent / "eval_progress.json"


@dataclass
class EvalResult:
    ticket_id: int
    expected_category: str
    predicted_category: str
    category_correct: bool
    confidence_score: float
    needs_escalation: bool
    draft_text: str


def _load_progress() -> dict[int, EvalResult]:
    if not PROGRESS_FILE.exists():
        return {}
    raw = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {r["ticket_id"]: EvalResult(**r) for r in raw}


def _save_progress(results_by_ticket: dict[int, EvalResult]) -> None:
    payload = [asdict(r) for r in results_by_ticket.values()]
    PROGRESS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_eval(db: Session) -> tuple[list[EvalResult], bool]:
    """Döner: (sonuçlar, hepsi_tamamlandı_mı). Kota/başka bir API hatası
    çıkarsa o ana kadarki sonuçlarla birlikte False döner — script'i tekrar
    çalıştırmak kaldığı yerden devam eder."""
    examples = list(db.scalars(select(EvalExample).order_by(EvalExample.id)))
    results_by_ticket = _load_progress()
    already_done = len(results_by_ticket)
    if already_done:
        print(f"Önceki koşudan {already_done} örnek zaten tamamlanmış, onlar atlanıyor.\n")

    all_completed = True
    for i, example in enumerate(examples, start=1):
        if example.ticket_id in results_by_ticket:
            continue

        ticket = db.get(Ticket, example.ticket_id)
        if ticket is None:
            print(f"[{i}/{len(examples)}] UYARI: ticket {example.ticket_id} bulunamadı, atlanıyor")
            continue

        try:
            predicted_category = classify_ticket(ticket.subject, ticket.body).category
            draft = generate_draft(ticket, db)
        except errors.APIError as e:
            print(f"\nAPI hatası (muhtemelen günlük kota doldu): {e}")
            print(f"Durduruldu: {len(results_by_ticket)}/{len(examples)} örnek tamamlandı, ilerleme kaydedildi.")
            print("Script'i tekrar çalıştırınca kaldığı yerden devam edecek.")
            all_completed = False
            break

        result = EvalResult(
            ticket_id=ticket.id,
            expected_category=example.expected_category,
            predicted_category=predicted_category,
            category_correct=predicted_category == example.expected_category,
            confidence_score=draft.confidence_score,
            needs_escalation=draft.confidence_score < ESCALATION_THRESHOLD,
            draft_text=draft.draft_text,
        )
        results_by_ticket[ticket.id] = result
        _save_progress(results_by_ticket)

        mark = "OK" if result.category_correct else "FARKLI"
        print(f"[{i}/{len(examples)}] ticket {ticket.id}: beklenen={example.expected_category} tahmin={predicted_category} ({mark}) guven={draft.confidence_score:.2f}")

        # Ücretsiz katmanın dakikalık istek kotasını aşmamak için ticket başına kısa bir bekleme.
        if i < len(examples):
            time.sleep(8)

    return list(results_by_ticket.values()), all_completed


def print_summary(results: list[EvalResult], all_completed: bool) -> None:
    total = len(results)
    if total == 0:
        print("Henüz hiç örnek tamamlanmadı.")
        return

    correct = sum(1 for r in results if r.category_correct)
    avg_confidence = sum(r.confidence_score for r in results) / total
    escalated = sum(1 for r in results if r.needs_escalation)

    print("\n" + "=" * 60)
    print("ÖZET" + ("" if all_completed else " (KISMİ — henüz tüm eval seti tamamlanmadı)"))
    print("=" * 60)
    print(f"Tamamlanan örnek: {total}")
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
        eval_results, completed = run_eval(session)
        print_summary(eval_results, completed)
    finally:
        session.close()
