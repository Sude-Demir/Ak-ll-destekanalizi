# supportIQ

Müşteri destek taleplerini otomatik sınıflandıran, şirketin kendi bilgi tabanından (RAG) yararlanarak bir yanıt **taslağı** hazırlayan ve bunu bir temsilcinin onayına sunan yapay zekâ destekli destek asistanı.

> **Kural:** AI hiçbir taslağı kendi başına müşteriye göndermez. Her yanıt bir insan tarafından onaylanır, düzenlenir veya reddedilir. Bu, projenin değişmeyen tek temel kuralıdır.

## Nasıl çalışıyor

1. Talep gelir (herkese açık form, müşteri portalı veya e-posta).
2. Tek bir LLM çağrısı talebi kategoriye ayırır; ayrıca satış fırsatı mı ve acil mi olduğunu da işaretler.
3. pgvector ile şirketin kendi SSS'inden anlamca en yakın içerik bulunur (RAG).
4. Bu içeriğe dayanan bir yanıt taslağı üretilir; taslak, hangi kaynaklara dayandığını ve bir güven skorunu da taşır.
5. Taslak onay kuyruğuna düşer — bir temsilci onaylar, düzenler ya da reddeder. Onaylanmayan hiçbir şey müşteriye gitmez.

## Özellikler

- Sınıflandırma, güven skoru ve eskalasyon (düşük güvenli taslaklar işaretlenir)
- Çoklu şirket (multi-tenant) mimarisi — her şirketin verisi izole
- Temsilci paneli + müşteri portalı, TR/EN dil desteği
- Lead ve aciliyet/duygu tespiti, talep sahiplenme, konuşma iş parçacığı (follow-up)
- Bilgi tabanı boşluk tespiti, çözülen taleplerden otomatik SSS önerisi
- CSAT geri bildirimi (👍/👎), AI performans trendi, öncelikli onay kuyruğu
- Taslak düzenleme geçmişi (AI'nin orijinal önerisi her zaman saklanır)

## Teknoloji

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Next.js (React) |
| Veritabanı | PostgreSQL + pgvector |
| LLM | Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`) |
| Kimlik doğrulama | Clerk |

