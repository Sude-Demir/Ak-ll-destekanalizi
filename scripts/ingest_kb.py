"""Bitext müşteri destek dataset'inden her intent (niyet) için bir temsilci
soru-cevap çifti seçip `knowledge_base_chunks` tablosuna yükler.

Kaynak: Hugging Face - bitext/Bitext-customer-support-llm-chatbot-training-dataset
Beklenen dosya: scripts/data/bitext_responses.csv (26.872 satır; flags, instruction,
category, intent, response sütunları).

Ne yapar:
  1) bitext_responses.csv'yi okur.
  2) Her (category, intent) çifti için ilk temsilci satırı seçer (26.872 yerine
     27 temiz SSS maddesi elde edilir — aynı konunun yüzlerce ifade biçimini
     tekrar tekrar eklemek yerine).
  3) Seçilen satırları scripts/data/kb_seed.csv dosyasına yazar.
  4) knowledge_base_chunks tablosuna yükler. `embedding` sütunu şimdilik NULL
     kalır; Hafta 3'te embedding üretim fonksiyonu eklendiğinde doldurulacak.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/ingest_kb.py
"""

import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_CSV_PATH = Path(__file__).resolve().parent / "data" / "bitext_responses.csv"
OUTPUT_CSV_PATH = Path(__file__).resolve().parent / "data" / "kb_seed.csv"


def select_one_per_intent(csv_path: Path) -> list[dict]:
    """Her (category, intent) çifti için dataset'teki ilk satırı temsilci olarak seçer."""
    seen_intents: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["intent"] not in seen_intents:
                seen_intents[row["intent"]] = {
                    "category": row["category"],
                    "intent": row["intent"],
                    "question": row["instruction"],
                    "answer": " ".join(row["response"].split()),  # fazla boşluk/satır sonu temizliği
                    "source": "bitext",
                }
    rows = list(seen_intents.values())
    print(f"{len(rows)} farklı intent bulundu, her biri için bir temsilci satır seçildi.")
    return rows


def write_csv(rows: list[dict]) -> None:
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["category", "intent", "question", "answer", "source"]
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} satır {OUTPUT_CSV_PATH} dosyasına yazıldı.")


def load_csv_to_db(rows: list[dict]) -> None:
    load_dotenv(ROOT_DIR / ".env")
    # psycopg2, SQLAlchemy'nin "postgresql+psycopg2://" sürücü ekini tanımaz.
    database_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM knowledge_base_chunks")
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO knowledge_base_chunks (category, intent, question, answer, source)
                    VALUES (%(category)s, %(intent)s, %(question)s, %(answer)s, %(source)s)
                    """,
                    row,
                )
        conn.commit()
        print(f"{len(rows)} satır knowledge_base_chunks tablosuna yüklendi.")
    finally:
        conn.close()


if __name__ == "__main__":
    if not SOURCE_CSV_PATH.exists():
        raise SystemExit(f"{SOURCE_CSV_PATH} bulunamadı.")

    kb_rows = select_one_per_intent(SOURCE_CSV_PATH)
    write_csv(kb_rows)
    load_csv_to_db(kb_rows)
