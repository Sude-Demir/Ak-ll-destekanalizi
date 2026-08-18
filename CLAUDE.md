# CLAUDE.md

Bu dosya, bu repo üzerinde çalışan Claude Code için proje bağlamını tanımlar. Detaylı gerekçelendirme ve tam plan için `akilli-destek-asistani-proje-raporu.md` dosyasına bakılabilir; bu dosya onun özetlenmiş, kod-odaklı halidir.

## Proje Özeti

"Akıllı Müşteri Destek Asistanı" — gelen müşteri taleplerini (e-posta/form) otomatik sınıflandıran, şirketin kendi bilgi tabanından (SSS/dokümantasyon) ilgili içeriği bulup (RAG) buna dayanan bir yanıt taslağı üreten ve bu taslağı bir temsilcinin onayına sunan bir sistem. Sistem **hiçbir zaman otomatik olarak müşteriye yanıt göndermez** — her yanıt bir insan tarafından onaylanmalı, düzenlenebilir veya reddedilebilir olmalıdır. Bu, projenin en temel ve değiştirilemez tasarım kuralıdır.

## Mevcut Aşama

**Hafta 4 — Güven skoru + onay/düzenleme/red akışı (temel akış tamamlandı).**

Tamamlananlar:
- Hafta 1: uçtan uca "veri gösterme" akışı çalışıyor (FastAPI + Next.js + pgvector'lı Postgres). `tickets` tablosu, gerçek veriyle dolu (Kaggle "Customer Support on Twitter" dataset'inden 300 gerçek müşteri talebi — `scripts/ingest_kaggle_tickets.py`).
- Hafta 2: `knowledge_base_chunks` tablosu (pgvector aktif), Bitext dataset'inden 27 intent için SSS içeriği (`scripts/ingest_kb.py`), Gemini embedding entegrasyonu (`backend/app/services/embeddings.py`, `gemini-embedding-001`, 768 boyut), retrieval fonksiyonu (`backend/app/services/retrieval.py`, pgvector kosinüs mesafesi).
- Hafta 3: `call_llm(prompt, context)` sarmalayıcısı (`backend/app/services/llm.py`, `gemini-2.5-flash`, geçici 503 hatalarında otomatik yeniden deneme). Sınıflandırma servisi (`classification.py`, 11 sabit kategori). Taslak üretim servisi (`draft_generation.py`) — retrieval'dan bulduğu SSS içeriğine dayanarak Türkçe taslak yazıyor, SSS'te karşılığı yoksa bunu taslakta açıkça belirtiyor. Prompt'lar `backend/app/services/prompts/*.txt` içinde, koda gömülü değil.
- `draft_responses` tablosu (`retrieved_context` JSON olarak SSS kaynaklarının tam kopyasını tutuyor — izlenebilirlik). Uç noktalar: `POST /tickets/{id}/draft`, `GET /tickets/{id}/drafts`, `GET /tickets/{id}`.
- Hafta 4: Güven skoru (`backend/app/services/confidence.py`) — retrieval artık pgvector kosinüs mesafesini de döndürüyor (`retrieve_relevant_chunks_with_distances`), en yakın eşleşmenin benzerliği `confidence_score` olarak kaydediliyor. `ESCALATION_THRESHOLD` (0.5) altındaki taslaklar API yanıtında `needs_escalation=true` ile işaretleniyor (`schemas.py`'de computed field). Onay/düzenleme/red akışı: `PATCH /tickets/{id}/drafts/{draft_id}` (`status`: approved/edited/rejected) — dashboard'da her taslağın altında Onayla/Düzenle/Reddet butonları, düşük güvenli taslaklarda "Dikkatli incele" rozeti.
- Frontend: `/dashboard/tickets/[id]` detay sayfası — talep bilgisi, kategori, "Taslak Oluştur" butonu, üretilen taslak + dayandığı SSS kaynakları + güven skoru + onay aksiyonları. Tarayıcıda uçtan uca test edildi.
- 16 birim testi (`backend/tests/`), hepsi geçiyor.

Not: `.env`'deki anahtar adı `GEMINI_API_KEY` (önceki `ANTHROPIC_API_KEY` adlandırması hataydı, düzeltildi).

Sırada: Hafta 4'ün geri kalanı — eval seti (gerçek taleplerden elle işaretlenmiş örnekler, prompt/model değişikliklerini bunlara karşı test etmek için). Sonrası Hafta 5 — gerçek e-posta/form entegrasyonu, Clerk auth.

Roadmap ötesi ürünleşme fikirleri (analytics ekranı, temsilci düzenleme farkının kaydı, multi-tenant kararı) konuşuldu ama henüz uygulanmadı — bkz. proje hafızası `project_urunlesme_fikirleri`.

İlerledikçe bu bölümü güncel aşamayı yansıtacak şekilde elle güncelle.

## Teknoloji Stack'i

- **Backend:** Python + FastAPI
- **Frontend:** Next.js (React, App Router)
- **Veritabanı:** PostgreSQL + pgvector eklentisi (hem ilişkisel veri hem vektör arama aynı veritabanında)
- **LLM:** Google Gemini API
- **Auth:** Clerk (henüz eklenmedi, Hafta 5'te ekleniyor)
- **E-posta:** Postmark veya SendGrid (henüz eklenmedi, Hafta 5'te ekleniyor)
- **Deployment:** Railway (backend + DB), Vercel (frontend) — henüz eklenmedi

## Mimari Prensipler

- **İnsan onaylı akış:** Her AI taslağı bir onay kuyruğuna düşer; otomatik gönderim yoktur.
- **Modülerlik:** Sınıflandırma, RAG/retrieval, taslak üretimi ve güven skoru hesaplama birbirinden bağımsız fonksiyonlar/modüller olarak yazılır, tek bir dev fonksiyona sıkıştırılmaz.
- **İnce soyutlama, ağır framework değil:** LLM çağrıları için `call_llm(prompt, context)` gibi basit, kendi yazdığımız bir fonksiyon kullanılır. Bu, hem mimariyi anlamayı kolaylaştırır hem de sağlayıcı değişikliğini tek noktadan yönetmeyi sağlar.
- **İzlenebilirlik:** Her taslak, hangi bilgi tabanı parçalarına (`retrieved_context`) dayandığını kaydeder. Bu alan asla atlanmamalı — hata ayıklama ve eval için kritik.
- **Erken optimizasyona hayır:** Özel vektör veritabanı, karmaşık agent framework'leri, fine-tuning gibi adımlar MVP'de yok; sadece gerçek ihtiyaç ortaya çıkınca eklenir.

## Klasör Yapısı (önerilen)

```
/backend
  /app
    /routers        # FastAPI route'ları (tickets, drafts, auth vb.)
    /services        # classification.py, retrieval.py, draft_generation.py, confidence.py
    /models          # SQLAlchemy modelleri
    /db              # bağlantı, migration'lar
  main.py
/frontend
  /app               # Next.js sayfaları (dashboard, ticket detay vb.)
  /components
/scripts
  seed_tickets.py     # örnek talep verisini yükler
  ingest_kb.py         # SSS/dokümantasyonu embed edip pgvector'a yazar
CLAUDE.md
akilli-destek-asistani-proje-raporu.md
```

## Veri Modeli (özet — tam şema rapor dosyasında)

`tickets`, `knowledge_base_chunks` (embedding sütunu ile), `draft_responses` (`retrieved_context`, `confidence_score`, `status` alanlarıyla), `agents`, `eval_examples`.

## Kodlama Standartları

- Backend: tip belirteçleri (type hints) kullan, Pydantic modelleriyle giriş/çıkış doğrulaması yap.
- Her yeni servis fonksiyonu (classification, retrieval, draft generation) için en az birkaç birim test yaz.
- LLM prompt'larını kod içine gömmek yerine ayrı `.txt`/`.py` sabitleri olarak tut, böylece değişiklik geçmişi net görünür.
- Gizli anahtarlar (`.env`) asla commit edilmez; `.env.example` ile hangi değişkenlerin gerektiği belgelenir.

## Yol Haritası (özet)

1. Hafta: İskelet — backend/frontend kurulumu, `tickets` tablosu, örnek veri, listeleme ekranı.
2. Hafta: Bilgi tabanı + RAG — pgvector kurulumu, SSS içeriği, embedding + retrieval fonksiyonu.
3. Hafta: Sınıflandırma + taslak üretimi — LLM entegrasyonu, dashboard'da taslak gösterimi.
4. Hafta: Güven skoru + eskalasyon — eşik mantığı, onay/düzenleme/red kaydı, eval seti.
5. Hafta: Gerçek entegrasyon — e-posta, auth, temel analitik.
6. Hafta ve sonrası: Genişletmeler (lead qualification, CRM entegrasyonu, tool-use).

Tam gerekçeler ve detaylar için `akilli-destek-asistani-proje-raporu.md` dosyasına bakılmalı.

## Kesinlikle Yapılmaması Gerekenler

- AI'ın taslağı insan onayı olmadan doğrudan müşteriye göndermesi.
- Gerçek müşteri verisiyle, önce eval seti üzerinde test edilmeden yeni bir prompt/model değişikliği yapmak.
- `.env` dosyasını veya API anahtarlarını commit etmek.
- Bu aşamada (Hafta 1-4) LangChain/LangGraph gibi ağır framework'ler eklemek — Bölüm "Mimari Prensipler"e bakılmalı.
