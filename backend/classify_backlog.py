"""Kategorisi boş kalan geçmiş talepleri Gemini ile TOPLU (batch) sınıflandırır.

Kategori ataması normalde sadece biri "Taslak Oluştur"a bastığında oluyor
(bkz. app/routers/drafts.py). 300 talep toplu içe aktarıldığı için
(scripts/ingest_kaggle_tickets.py) hiçbirine taslak üretilmedi, dolayısıyla
hiçbirinin kategorisi dolmadı.

Onları TEK TEK sınıflandırmak (300 ayrı Gemini çağrısı) ücretsiz planın
günlük 20 istek sınırıyla ~15 gün sürerdi. Bunun yerine app/services/
classification.py'deki classify_tickets_batch ile talepleri BATCH_SIZE'lık
gruplar hâlinde TEK çağrıda sınıflandırıyoruz — toplam çağrı sayısı
~15-20'ye iner.

Kota yine de bir günde bitmeyebilir; script ilerlemeyi classify_progress.json'a
kaydeder (gitignore'da), kota dolup script durursa bir dahaki çalıştırmada
zaten tamamlanmış talepleri atlar (bkz. run_eval.py'deki aynı desen).

Kullanım (backend/ dizininden, sanal ortam aktifken):
    python classify_backlog.py                # hepsini işler
    python classify_backlog.py --limit 20      # önce küçük bir deneme (tek batch)
"""

import argparse
import json
import time
from pathlib import Path

from google.genai import errors
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import Ticket
from app.services.classification import classify_tickets_batch

PROGRESS_FILE = Path(__file__).parent / "classify_progress.json"
BATCH_SIZE = 20
SLEEP_BETWEEN_BATCHES_SECONDS = 5


def _load_done_ids() -> set[int]:
    if not PROGRESS_FILE.exists():
        return set()
    return set(json.loads(PROGRESS_FILE.read_text(encoding="utf-8")))


def _save_done_ids(done_ids: set[int]) -> None:
    PROGRESS_FILE.write_text(json.dumps(sorted(done_ids)), encoding="utf-8")


def run_backfill(db: Session, limit: int | None = None) -> None:
    stmt = select(Ticket).filter(Ticket.category.is_(None)).order_by(Ticket.id)
    tickets = list(db.scalars(stmt))

    done_ids = _load_done_ids()
    remaining = [t for t in tickets if t.id not in done_ids]
    if limit is not None:
        remaining = remaining[:limit]

    if not remaining:
        print("Kategorisi boş talep kalmadı.")
        return

    print(f"{len(remaining)} talep sınıflandırılacak (zaten yapılmış {len(done_ids)} atlanıyor).\n")

    batches = [remaining[i : i + BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]

    for i, batch in enumerate(batches, start=1):
        items = [(t.id, t.subject, t.body) for t in batch]
        try:
            results = classify_tickets_batch(items)
        except errors.APIError as e:
            print(f"\nAPI hatası (muhtemelen günlük kota doldu): {e}")
            print(
                f"Durduruldu: {len(done_ids)} talep tamamlandı. "
                "Script'i tekrar çalıştırınca kaldığı yerden devam edecek."
            )
            return

        for ticket in batch:
            classification = results[ticket.id]
            ticket.category = classification.category
            ticket.is_lead = classification.is_lead
            ticket.is_urgent = classification.is_urgent
            done_ids.add(ticket.id)
        db.commit()
        _save_done_ids(done_ids)

        print(f"[{i}/{len(batches)}] {len(batch)} talep sınıflandırıldı (toplam tamamlanan: {len(done_ids)})")

        if i < len(batches):
            time.sleep(SLEEP_BETWEEN_BATCHES_SECONDS)

    print(f"\nBitti: {len(done_ids)} talep sınıflandırıldı.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="En fazla kaç talep işlensin (test için)")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        run_backfill(session, limit=args.limit)
    finally:
        session.close()
