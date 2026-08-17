"""Örnek destek talebi verisi üretir ve `tickets` tablosuna yükler.

İki adımda çalışır:
  1) scripts/data/tickets_seed.csv dosyasına 80 adet örnek destek talebi yazar.
  2) Bu CSV'yi okuyup `tickets` tablosuna INSERT eder.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/seed_tickets.py
"""

import csv
import os
import random
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = Path(__file__).resolve().parent / "data" / "tickets_seed.csv"
TICKET_COUNT = 80
RANDOM_SEED = 42

CUSTOMER_NAMES = [
    "Ayşe Yılmaz", "Mehmet Kaya", "Fatma Demir", "Ahmet Çelik", "Zeynep Şahin",
    "Mustafa Yıldız", "Elif Aydın", "Emre Öztürk", "Hatice Arslan", "Can Doğan",
    "Merve Kılıç", "Burak Aslan", "Selin Çetin", "Onur Kurt", "Buse Koç",
    "Kerem Yavuz", "Deniz Aksoy", "Gizem Polat", "Yusuf Şimşek", "Ece Güneş",
    "Barış Er", "Ceren Bulut", "Tolga Türk", "Nazlı Özdemir", "Serkan Acar",
    "İrem Keskin", "Volkan Tan", "Aylin Sezer", "Furkan Uçar", "Pınar Bal",
]

CHANNELS = ["email", "form"]

# open ağırlıklı; henüz gerçek bir eskalasyon/işleme akışı yok (Hafta 4'te eklenecek)
STATUSES = ["open", "open", "open", "pending", "pending", "closed"]

# (subject, body) şablonları. {} yer tutucular her kayıt için rastgele doldurulur.
TICKET_TEMPLATES = [
    (
        "Faturamda hatalı ücretlendirme var",
        "Merhaba, {ay} ayına ait faturamda {tutar} TL fazladan ücret görüyorum. "
        "Sipariş numaram #{siparis}. Konuyu inceleyip bana dönüş yapabilir misiniz?",
    ),
    (
        "Şifremi sıfırlayamıyorum",
        "Hesabıma giriş yapmaya çalışıyorum ama şifre sıfırlama e-postası bir türlü gelmiyor. "
        "E-posta adresim kayıtlı olan adresle aynı, spam klasörünü de kontrol ettim.",
    ),
    (
        "Siparişim hâlâ elime ulaşmadı",
        "#{siparis} numaralı siparişimi {gun} gün önce verdim ama kargo durumu hâlâ "
        "'hazırlanıyor' olarak görünüyor. Ne zaman kargoya verilecek?",
    ),
    (
        "Ürünü iade etmek istiyorum",
        "Aldığım ürün beklediğim gibi çıkmadı, iade etmek istiyorum. Sipariş numarası #{siparis}. "
        "İade süreci nasıl işliyor, ücret iadesi ne kadar sürer?",
    ),
    (
        "Hesabımı kapatmak istiyorum",
        "Artık hizmetinizi kullanmıyorum ve hesabımın kalıcı olarak silinmesini istiyorum. "
        "Bu işlemi nasıl başlatabilirim?",
    ),
    (
        "Mobil uygulama sürekli çöküyor",
        "Uygulamayı açtığımda birkaç saniye içinde kapanıyor. Telefonumu yeniden başlattım, "
        "uygulamayı silip tekrar kurdum ama sorun devam ediyor.",
    ),
    (
        "Ödeme yaptım ama sipariş oluşmadı",
        "Kartımdan {tutar} TL çekildi ancak sipariş geçmişimde herhangi bir kayıt görünmüyor. "
        "İşlem referans numarası: {siparis}.",
    ),
    (
        "Kampanya kodu çalışmıyor",
        "Sitede gördüğüm '%20 indirim' kodunu ödeme sayfasında giriyorum ama geçersiz "
        "olduğunu söylüyor. Kod hâlâ aktif görünüyor.",
    ),
    (
        "Fatura bilgilerimi güncellemek istiyorum",
        "Şirket unvanım değişti, faturalarımın yeni unvan ile kesilmesini istiyorum. "
        "Gerekli bilgileri nereye iletmeliyim?",
    ),
    (
        "Ürün açıklamasıyla gelen ürün uyuşmuyor",
        "Sitede belirtilen özellikler ile elime ulaşan ürün birbirini tutmuyor. "
        "Sipariş numarası #{siparis}. Değişim yapılabilir mi?",
    ),
    (
        "Abonelik ücreti beklenmedik şekilde arttı",
        "Bu ay {tutar} TL ödedim, önceki aylara göre belirgin bir artış var. "
        "Fiyat değişikliği hakkında bilgilendirilmedim.",
    ),
    (
        "İki faktörlü doğrulama kodu gelmiyor",
        "Giriş yaparken SMS ile gelmesi gereken doğrulama kodu telefonuma ulaşmıyor. "
        "{gun} gündür bu sorunu yaşıyorum.",
    ),
    (
        "Teslimat adresimi değiştirmek istiyorum",
        "#{siparis} numaralı siparişim henüz kargoya verilmedi, teslimat adresini "
        "değiştirebilir miyim?",
    ),
    (
        "Ürün eksik parça ile geldi",
        "Kargo kutusunda ürünle birlikte gelmesi gereken aksesuarlar yoktu. "
        "Sipariş numarası #{siparis}. Eksik parçaları nasıl temin edebilirim?",
    ),
    (
        "Fatura e-postası hiç gelmedi",
        "{ay} ayı için ödeme yaptım ancak fatura e-postası kutuma hiç düşmedi. "
        "Faturamı nereden indirebilirim?",
    ),
    (
        "Hesabıma başka biri girmiş olabilir",
        "Hesap hareketlerimde tanımadığım bir işlem görüyorum. Şifremi hemen değiştirdim "
        "ama başka ne yapmam gerektiğini bilmiyorum.",
    ),
    (
        "Ürün stokta yokken sipariş alındı",
        "#{siparis} numaralı siparişimi verdikten sonra ürünün stokta olmadığı bilgisini aldım. "
        "Ödemem iade edilecek mi, ne zaman?",
    ),
    (
        "Destek talebime yanıt alamadım",
        "{gun} gün önce açtığım bir destek talebine hâlâ yanıt gelmedi. Konu hakkında "
        "bilgi alabilir miyim?",
    ),
    (
        "Web sitesinde ödeme sayfası açılmıyor",
        "Sepetimdeki ürünleri satın almak istediğimde ödeme sayfası sürekli hata veriyor. "
        "Farklı tarayıcı denedim, sonuç değişmedi.",
    ),
    (
        "Ürün garantisi hakkında bilgi almak istiyorum",
        "{ay} ayında aldığım ürünün garanti süresi ne kadar, arıza durumunda süreç "
        "nasıl işliyor öğrenebilir miyim?",
    ),
]

AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def slugify_email(name: str, index: int) -> str:
    ascii_map = str.maketrans("çğıöşüİ", "cgiosuI")
    local = name.lower().translate(ascii_map).replace(" ", ".")
    return f"{local}{index}@ornekpost.com"


def generate_rows(count: int) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    rows = []
    for i in range(count):
        name = rng.choice(CUSTOMER_NAMES)
        subject, body_template = rng.choice(TICKET_TEMPLATES)
        body = body_template.format(
            tutar=rng.choice([49, 99, 129, 199, 249, 349, 499]),
            siparis=rng.randint(100000, 999999),
            gun=rng.randint(1, 14),
            ay=rng.choice(AYLAR),
        )
        rows.append(
            {
                "customer_name": name,
                "customer_email": slugify_email(name, i),
                "subject": subject,
                "body": body,
                "channel": rng.choice(CHANNELS),
                "status": rng.choice(STATUSES),
            }
        )
    return rows


def write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["customer_name", "customer_email", "subject", "body", "channel", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} satır {CSV_PATH} dosyasına yazıldı.")


def load_csv_to_db() -> None:
    load_dotenv(ROOT_DIR / ".env")
    # psycopg2, SQLAlchemy'nin "postgresql+psycopg2://" sürücü ekini tanımaz.
    database_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO tickets (customer_name, customer_email, subject, body, channel, status)
                    VALUES (%(customer_name)s, %(customer_email)s, %(subject)s, %(body)s, %(channel)s, %(status)s)
                    """,
                    row,
                )
        conn.commit()
        print(f"{len(rows)} satır tickets tablosuna yüklendi.")
    finally:
        conn.close()


if __name__ == "__main__":
    rows = generate_rows(TICKET_COUNT)
    write_csv(rows)
    load_csv_to_db()
