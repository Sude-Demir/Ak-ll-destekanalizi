"""Kaggle 'Customer Support on Twitter' dataset'inden gerçek destek taleplerini
`tickets` tablosuna yükler (seed_tickets.py'deki üretilmiş/sahte veri yerine).

Kaynak: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
Beklenen dosya: scripts/data/twcs.csv (kullanıcı Kaggle'dan kendi hesabıyla indirip
bu yola koyar; dosya ~2,8 milyon satır ve İngilizce'dir).

Ne yapar:
  1) twcs.csv'yi satır satır okur (dosya büyük olduğu için hepsini belleğe almaz).
  2) Sadece "inbound" (müşteriden gelen, şirket yanıtı olmayan) satırları alır.
  3) Reservoir sampling ile SAMPLE_SIZE kadar rastgele satır seçer (sabit seed ile
     tekrarlanabilir).
  4) Twitter'a özgü alanları (author_id, text, created_at, response_tweet_id) bizim
     `tickets` şemamıza eşler. Gerçek isim/e-posta dataset'te yok; bunları uydurmuk
     yerine "Twitter Kullanıcısı #<id>" ve <id>@twitter.invalid gibi açıkça yer
     tutucu (placeholder) değerlerle işaretleriz (.invalid, RFC 2606 gereği gerçek
     olmayan adresler için ayrılmış bir alan adı uzantısıdır).
  5) Mevcut (sahte) tickets kayıtlarını siler, seçilen örneklemi tickets tablosuna
     yükler.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/ingest_kaggle_tickets.py
"""

import csv
import os
import random
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_CSV_PATH = Path(__file__).resolve().parent / "data" / "twcs.csv"
OUTPUT_CSV_PATH = Path(__file__).resolve().parent / "data" / "tickets_seed_kaggle.csv"
SAMPLE_SIZE = 300
RANDOM_SEED = 42

# Twitter'ın created_at formatı, örn: "Tue Oct 31 22:10:47 +0000 2017"
TWITTER_DATE_FORMAT = "%a %b %d %H:%M:%S %z %Y"


def sample_inbound_rows(csv_path: Path, sample_size: int) -> list[dict]:
    """twcs.csv'yi tek geçişte okuyup sadece müşteriden gelen (inbound) satırlardan
    reservoir sampling ile `sample_size` kadarını rastgele seçer. Dosya büyük
    olduğu için tamamını belleğe yüklemez."""
    rng = random.Random(RANDOM_SEED)
    reservoir: list[dict] = []
    seen = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("inbound") != "True":
                continue
            seen += 1
            if len(reservoir) < sample_size:
                reservoir.append(row)
            else:
                j = rng.randint(0, seen - 1)
                if j < sample_size:
                    reservoir[j] = row

    print(f"{seen} inbound satır tarandı, {len(reservoir)} tanesi örnekleme alındı.")
    return reservoir


def to_ticket_row(raw: dict) -> dict:
    text = " ".join(raw["text"].split())  # satır sonlarını/fazla boşlukları temizle
    subject = text if len(text) <= 80 else text[:77] + "..."

    try:
        created_at = datetime.strptime(raw["created_at"], TWITTER_DATE_FORMAT).isoformat()
    except ValueError:
        created_at = None  # ayrıştırılamazsa DB varsayılanı (şimdiki zaman) kullanılır

    has_response = bool(raw.get("response_tweet_id"))

    return {
        "customer_name": f"Twitter Kullanıcısı #{raw['author_id']}",
        "customer_email": f"{raw['author_id']}@twitter.invalid",
        "subject": subject,
        "body": text,
        "channel": "twitter",
        "status": "closed" if has_response else "open",
        "created_at": created_at,
    }


def write_csv(rows: list[dict]) -> None:
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["customer_name", "customer_email", "subject", "body", "channel", "status", "created_at"]
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
            cur.execute("DELETE FROM tickets")
            for row in rows:
                if row["created_at"] is None:
                    cur.execute(
                        """
                        INSERT INTO tickets (customer_name, customer_email, subject, body, channel, status)
                        VALUES (%(customer_name)s, %(customer_email)s, %(subject)s, %(body)s, %(channel)s, %(status)s)
                        """,
                        row,
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO tickets (customer_name, customer_email, subject, body, channel, status, created_at)
                        VALUES (%(customer_name)s, %(customer_email)s, %(subject)s, %(body)s, %(channel)s, %(status)s, %(created_at)s)
                        """,
                        row,
                    )
        conn.commit()
        print(f"{len(rows)} satır tickets tablosuna yüklendi (önceki kayıtlar silindi).")
    finally:
        conn.close()


if __name__ == "__main__":
    if not SOURCE_CSV_PATH.exists():
        raise SystemExit(
            f"{SOURCE_CSV_PATH} bulunamadı. Kaggle'dan twcs.csv dosyasını indirip "
            "bu yola koyduğundan emin ol: "
            "https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter"
        )

    raw_rows = sample_inbound_rows(SOURCE_CSV_PATH, SAMPLE_SIZE)
    ticket_rows = [to_ticket_row(r) for r in raw_rows]
    write_csv(ticket_rows)
    load_csv_to_db(ticket_rows)
