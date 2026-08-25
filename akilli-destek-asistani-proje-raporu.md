# Akıllı Müşteri Destek Asistanı — Proje Raporu

## Bu Rapor Hakkında

Bu doküman, sıfırdan başlayarak "insan onaylı" (co-pilot modunda) çalışan bir yapay zeka destekli müşteri desteği/satış asistanı geliştirmek isteyenler için hazırlanmıştır. Amaç, gelen müşteri taleplerini otomatik sınıflandıran, şirketin kendi bilgi tabanından yararlanarak yanıt taslağı hazırlayan ve bu taslağı bir temsilcinin onayına sunan bir sistem kurmaktır. Rapor; problemi, çözümü, mimari kararları, her teknoloji seçiminin gerekçesini ve haftalık geliştirme planını içerir.

---

## 1. Yönetici Özeti

Şirketler her gün onlarca-yüzlerce benzer müşteri talebiyle karşılaşır: aynı sorulara farklı kelimelerle verilen cevaplar, tekrar eden şikayetler, benzer satış soruları. Bu tekrar eden işi bir temsilcinin sıfırdan yanıtlaması hem zaman kaybettirir hem de yanıt kalitesini tutarsız hale getirir.

Bu proje, gelen her talebi otomatik olarak sınıflandıran (destek talebi mi, satış fırsatı mı, şikayet mi), şirketin SSS ve dokümantasyonundan ilgili bilgiyi bulup getiren ve bu bilgiye dayanarak bir yanıt taslağı hazırlayan bir sistem kurar. Sistem taslağı otomatik göndermez — bir temsilci taslağı görür, gerekirse düzenler, onaylar ve gönderir. Bu "insan onaylı" yaklaşım hem güvenlik sağlar (yapay zeka yanlış bilgi verirse müşteriye ulaşmadan yakalanır) hem de gerçekçi bir üründür, çünkü çoğu şirket bugün tam otonom bir yapay zekaya müşteri iletişimini tamamen bırakmaya hazır değildir.

Sistem beş temel yetenek üzerine kuruludur: talep alma ve saklama, bilgi tabanından ilgili içeriği getirme (RAG), yapay zeka ile sınıflandırma ve taslak üretimi, güven skoruna dayalı eskalasyon (belirsiz durumları insana yönlendirme) ve bir onay/düzenleme arayüzü.

---

## 2. Problem ve Motivasyon

Müşteri destek ve satış ekiplerinin karşılaştığı üç temel sorun vardır. Birincisi, gelen taleplerin büyük bir kısmı birbirine çok benzer olmasına rağmen her biri sıfırdan yanıtlanır; bu da zaman kaybıdır. İkincisi, doğru bilgiye (fiyatlandırma, iade politikası, teknik detaylar) hızlıca ulaşmak zordur; temsilci bilgiyi ararken müşteri bekler. Üçüncüsü, farklı temsilcilerin aynı soruya verdiği cevaplar tutarsız olabilir, bu da marka deneyimini zedeler.

Yapay zeka burada iyi bir çözüm adayıdır çünkü büyük dil modelleri hem metni anlama hem de ilgili bilgiyi bir bağlamdan (context) çekip doğal bir yanıt üretme konusunda güçlüdür. Ancak modelin "halüsinasyon" görme, yani var olmayan bilgiyi uydurma riski olduğu için, modelin doğrudan müşteriyle konuşmasına değil, önce bir insana taslak sunmasına izin veren bir tasarım tercih edilmiştir.

---

## 3. Hedef Kullanıcı ve Kullanım Senaryosu

Hedef kullanıcı, küçük-orta ölçekli bir şirketin müşteri destek/satış ekibidir — günde 20-200 arası talep alan, birkaç kişilik bir ekibi olan işletmeler. Tipik bir senaryo şöyle işler: bir müşteri e-posta veya web formu üzerinden bir talep gönderir; sistem bu talebi alır, içeriğini analiz ederek "destek", "satış" veya "şikayet" olarak sınıflandırır; şirketin SSS/dokümantasyon veritabanından ilgili bilgiyi bulur; bu bilgiye dayanarak bir yanıt taslağı yazar; taslağı ve güven skorunu bir panelde temsilciye gösterir; temsilci taslağı olduğu gibi onaylayabilir, düzenleyebilir veya tamamen yeniden yazabilir; onaylanan yanıt gönderilir ve sistem bu etkileşimden öğrenmek üzere kaydedilir.

---

## 4. Ürün Vizyonu ve Kapsam

### 4.1 MVP Kapsamı (İlk Sürüm)

İlk sürümde şunlar olacak: talep alma (başta mock/manuel veri, sonra gerçek e-posta entegrasyonu), SSS tabanlı RAG sistemi, sınıflandırma ve taslak üretimi, güven skoruna dayalı basit eskalasyon mantığı ve onay/düzenleme arayüzü olan bir dashboard.

### 4.2 Kapsam Dışı (Şimdilik)

İlk sürümde şunlar olmayacak: tam otonom gönderim (insan onayı olmadan), çoklu dil desteği, sesli asistan entegrasyonu, gerçek CRM'e (HubSpot vb.) tam entegrasyon, satış lead qualification modülü. Bunlar MVP'den sonra eklenecek genişletmelerdir (bkz. Bölüm 14).

---

## 5. Sistem Mimarisi — Genel Bakış

Sistemin uçtan uca akışı şu şekildedir:

```
[Müşteri Talebi]
      |
      v
[Alım Katmanı] --(e-posta/form/API)--> [Ana Veritabanı: talep kaydedilir]
      |
      v
[Sınıflandırma Modülü] --(LLM çağrısı)--> "destek" / "satış" / "şikayet"
      |
      v
[RAG Modülü] --(vektör arama)--> [Bilgi Tabanı: SSS, dokümantasyon]
      |
      v
[Taslak Üretim Modülü] --(LLM çağrısı: talep + ilgili bağlam)--> [Yanıt Taslağı]
      |
      v
[Güven Skoru Hesaplama] --> düşükse: [İnsana Eskale Et]
      |                              yüksekse: [Onay Kuyruğuna Ekle]
      v
[Dashboard: Temsilci Onay/Düzenleme Arayüzü]
      |
      v
[Onaylanan Yanıt Gönderilir] --> [Kayıt: Eval/Analiz için saklanır]
```

Bu mimari bilinçli olarak modüler tasarlanmıştır: her kutu (sınıflandırma, RAG, taslak üretimi, güven skoru) birbirinden bağımsız olarak geliştirilip test edilebilir. Bu, projeyi haftalık aşamalara bölmeyi kolaylaştırır ve her modülün ayrı ayrı değerlendirilmesine (eval) imkan tanır.

---

## 6. Teknoloji Seçimleri ve Gerekçeleri

Bu bölümde her teknoloji seçiminin **neden** seçildiği açıklanmaktadır; amaç sadece "ne kullanılacağını" değil, "neden bu ve neden alternatifi değil" sorusunu da yanıtlamaktır.

### 6.1 Backend Framework: Python + FastAPI

**Neden Python/FastAPI:** Yapay zeka ekosistemi (LLM SDK'ları, embedding kütüphaneleri, veri işleme araçları) ağırlıklı olarak Python üzerine kuruludur; bu da entegrasyonları basitleştirir. FastAPI, hafif, hızlı ve modern bir framework olup otomatik API dokümantasyonu (Swagger) üretir — bu, geliştirme sürecinde API'yi test etmeyi kolaylaştırır. Node.js/Express de alternatif olabilirdi, ancak AI/ML tarafındaki kütüphane desteği (özellikle embedding ve veri işleme) Python'da daha olgundur.

### 6.2 LLM Sağlayıcı: Claude veya OpenAI API

**Neden bir API sağlayıcısı (kendi model eğitmek yerine):** Bu ölçekte bir proje için kendi büyük dil modelini eğitmek hem maliyetli hem gereksizdir. Mevcut modeller (Claude, GPT ailesi) hem sınıflandırma hem metin üretimi görevlerinde zaten çok güçlüdür. API üzerinden çağırmak, altyapı yönetimi (GPU, model barındırma) derdinden kurtarır ve saniyeler içinde entegrasyon sağlar. İki sağlayıcı arasında seçim yaparken maliyet, gecikme süresi (latency) ve kod tabanınızın hangisine daha alışkın olduğu belirleyici olabilir; ikisi de benzer bir API şekli (mesaj gönder, yanıt al) sunar, bu yüzden başlangıçta hangisini seçtiğiniz kritik değildir — soyutlama katmanı (aşağıda 6.9) ile ileride değiştirilebilir.

### 6.3 Vektör Veritabanı: PostgreSQL + pgvector

**Neden pgvector (ayrı bir vektör veritabanı yerine):** RAG sistemi kurarken metinleri "embedding" adı verilen sayısal vektörlere çevirip benzerlik araması yapmanız gerekir. Piyasada Pinecone, Weaviate, Chroma gibi özel vektör veritabanları var, ancak bu ölçekte (birkaç bin-on binlerce doküman parçası) bunlara ihtiyaç yoktur. PostgreSQL zaten ana veritabanınız olacağı için (bkz. 6.4), pgvector eklentisiyle vektör aramasını da aynı veritabanında yapmak, ayrı bir sistemi öğrenme/yönetme/senkronize etme yükünü ortadan kaldırır. Veri büyüdükçe (milyonlarca doküman) özel bir vektör veritabanına geçiş düşünülebilir, ama MVP için bu gereksiz bir erken optimizasyon olur.

### 6.4 Ana Veritabanı: PostgreSQL

**Neden PostgreSQL:** Talepler, kullanıcılar, yanıtlar, eval kayıtları gibi ilişkisel veriler için olgun, güvenilir ve geniş topluluk desteğine sahip bir veritabanıdır. pgvector eklentisiyle hem klasik ilişkisel veriyi hem vektör aramasını tek sistemde tutmak, mimariyi basitleştirir (bkz. 6.3).

### 6.5 Frontend: React (Next.js)

**Neden React/Next.js:** Dashboard, temsilcilerin talepleri görüp taslakları onaylayacağı ana arayüzdür; bu yüzden hızlı, interaktif bir arayüz gerekir. Next.js hem frontend hem basit API route'ları aynı proje içinde barındırma imkanı sunar, bu da başlangıç aşamasında ayrı bir frontend/backend deployment karmaşasından kaçınmayı sağlar (backend'i FastAPI'de tutup Next.js'i sadece arayüz için kullanmak da geçerli bir alternatiftir).

### 6.6 Kimlik Doğrulama (Auth): Clerk veya Auth0

**Neden hazır bir auth servisi (kendi yazmak yerine):** Kullanıcı girişi, şifre sıfırlama, oturum yönetimi gibi işlevleri sıfırdan güvenli şekilde yazmak zaman alır ve güvenlik riski taşır. Clerk veya Auth0 gibi servisler bu işi dakikalar içinde, endüstri standardı güvenlikle çözer. MVP aşamasında zaman en değerli kaynağınız olduğu için bu alanda "tekerleği yeniden icat etmemek" mantıklıdır.

### 6.7 Deployment/Hosting: Railway veya Vercel + Fly.io

**Neden bu servisler:** Vercel, Next.js frontend'ini dakikalar içinde canlıya almanıza olanak tanır. Railway veya Fly.io, FastAPI backend'i ve PostgreSQL veritabanını yönetmek için basit, düşük maliyetli seçeneklerdir. Bunlar "sunucu yönetimi" derdini ortadan kaldırır (sunucu kurulumu, SSL sertifikası, ölçeklendirme gibi konularla uğraşmazsınız), bu da MVP'yi hızlıca canlıya almanızı sağlar. Şirket büyüdükçe AWS/GCP gibi daha esnek ama daha karmaşık altyapılara geçiş düşünülebilir.

### 6.8 E-posta Entegrasyonu: Postmark veya SendGrid

**Neden bir e-posta API'si:** Gerçek müşteri e-postalarını almak ve yanıt göndermek için bir e-posta servis sağlayıcısı (ESP) gerekir. Bu servisler hem gelen e-postaları webhook ile sisteminize iletir hem de giden e-postaların teslim oranını (deliverability) yönetir — bunu kendi SMTP sunucunuzla yapmak hem zor hem de e-postaların spam'e düşme riskini artırır.

### 6.9 LLM Çağrıları İçin Soyutlama Katmanı

**Neden framework yerine kendi kodunuz:** LangChain/LangGraph gibi framework'ler agent sistemleri kurmayı hızlandırabilir, ancak orta seviye bir öğrenme aşamasında bu framework'lerin "sihirli" soyutlamaları, altta ne olduğunu anlamayı zorlaştırabilir. Bu yüzden MVP'de LLM API'sini doğrudan çağıran, ince bir kendi soyutlama katmanınızı (örneğin `call_llm(prompt, context)` gibi basit bir fonksiyon) yazmanız önerilir. Bu hem mimariyi gerçekten anlamanızı sağlar hem de ileride sağlayıcı değiştirmek istediğinizde (Claude'dan GPT'ye ya da tam tersi) tek bir yeri değiştirmeniz yeterli olur. Proje büyüyüp çoklu adımlı, dallanan agent akışlarına ihtiyaç duyduğunuzda (Bölüm 14'teki genişletmeler gibi) LangGraph gibi bir framework'e geçiş o zaman daha anlamlı olur.

---

## 7. Veri Modeli

Ana veritabanı şeması aşağıdaki gibi tasarlanabilir (basitleştirilmiş):

```
tickets (talepler)
  id, customer_email, subject, body, channel, status,
  category (destek/satış/şikayet), confidence_score,
  created_at, resolved_at

knowledge_base_chunks (bilgi tabanı parçaları)
  id, source_document, content, embedding (vector),
  created_at

draft_responses (yanıt taslakları)
  id, ticket_id, generated_text, retrieved_context (hangi
  chunk'lar kullanıldı), confidence_score, status
  (bekliyor/onaylandı/düzenlendi/reddedildi), created_at

agents (temsilciler)
  id, name, email, role

eval_examples (değerlendirme örnekleri)
  id, sample_ticket_text, ideal_response, notes
```

Bu şema, her taslağın hangi bilgi parçalarına dayandığını (`retrieved_context`) kaydettiği için hem hata ayıklamayı (model neden bu bilgiyi kullandı?) hem de ileride "bu bilgi kaynağı doğru mu, güncel mi" denetimini kolaylaştırır — bu, gerçek üretim sistemlerinde sıkça atlanan ama çok değerli bir tasarım detayıdır.

---

## 8. Uygulama Akışı — Adım Adım

Bir talep sisteme girdiğinde şu adımlar sırayla işler:

1. **Alım:** Talep e-posta webhook'u veya form üzerinden gelir, `tickets` tablosuna ham haliyle kaydedilir, durumu "yeni" olarak işaretlenir.
2. **Sınıflandırma:** Talebin metni bir LLM çağrısına gönderilir; model "destek", "satış" veya "şikayet" kategorilerinden birini ve kısa bir gerekçe döner. Bu, tek başına küçük ve hızlı bir prompt ile yapılabilir (ayrı bir model eğitmeye gerek yoktur).
3. **Bilgi Getirme (Retrieval):** Talebin metni embedding'e çevrilir, `knowledge_base_chunks` tablosunda pgvector ile en benzer 3-5 parça bulunur.
4. **Taslak Üretimi:** Talep metni + bulunan bilgi parçaları + (varsa) önceki iletişim geçmişi, bir prompt içinde LLM'e gönderilir; model bir yanıt taslağı üretir.
5. **Güven Skoru Hesaplama:** Retrieval sonucunun benzerlik skoru düşükse (yani ilgili bilgi bulunamadıysa) veya model kendi yanıtında belirsizlik ifade ediyorsa, güven skoru düşük hesaplanır.
6. **Yönlendirme:** Güven skoru eşiğin altındaysa talep "acil insan incelemesi" kuyruğuna, üstündeyse normal "onay bekliyor" kuyruğuna eklenir.
7. **İnsan Onayı:** Temsilci dashboard'da taslağı görür, olduğu gibi onaylayabilir, düzenleyebilir veya sıfırdan yazabilir.
8. **Gönderim ve Kayıt:** Onaylanan yanıt müşteriye gönderilir; hem orijinal AI taslağı hem son gönderilen hali kaydedilir — bu veri, ileride modelin ne kadar "doğru" taslak ürettiğini ölçmek için altın değerindedir.

---

## 9. RAG (Retrieval-Augmented Generation) Detayları

RAG, modelin "ezberinden" değil, sizin sağladığınız güncel ve doğru bilgiden yanıt üretmesini sağlayan tekniktir. Neden gereklidir: büyük dil modelleri şirketinizin özel SSS'sini, fiyatlandırmasını veya iç politikalarını bilmez; bu bilgiyi her seferinde prompt içinde modele "hatırlatmanız" gerekir.

Süreç şöyle işler: önce bilgi tabanınızdaki dokümanları (SSS, ürün dokümantasyonu, politika metinleri) küçük parçalara (chunk) bölersiniz — genellikle 200-500 kelimelik parçalar iyi bir başlangıç noktasıdır, çünkü çok büyük parçalar alakasız bilgi taşır, çok küçük parçalar ise bağlamı kaybeder. Her parça bir "embedding modeli" ile sayısal bir vektöre çevrilir ve pgvector'da saklanır. Bir talep geldiğinde, talebin kendisi de aynı embedding modeliyle vektöre çevrilir ve veritabanında "kosinüs benzerliği" gibi bir yöntemle en yakın parçalar bulunur. Bu parçalar, LLM'e gönderilen prompt'a "işte ilgili bilgi, buna dayanarak yanıtla" şeklinde eklenir.

Başlangıçta bilgi tabanınız küçük (10-20 SSS maddesi) olacağı için retrieval kalitesi kolayca gözle kontrol edilebilir; içerik büyüdükçe (yüzlerce doküman) retrieval kalitesini ölçmek için ayrı bir değerlendirme yapmanız gerekecektir (bkz. Bölüm 12).

---

## 10. Sınıflandırma ve Güven Skoru Mantığı

Sınıflandırma için karmaşık bir makine öğrenmesi modeli eğitmeye gerek yoktur — bir LLM'e "bu metni destek/satış/şikayet olarak sınıflandır ve nedenini kısaca açıkla" şeklinde bir prompt yeterlidir. Bu yaklaşım, az veri ile başlamak için idealdir; ileride binlerce etiketli örnek biriktiğinde, daha hızlı ve ucuz çalışması için küçük, uzmanlaşmış bir sınıflandırma modeli eğitmek (fine-tuning) düşünülebilir, ama bu bir MVP kaygısı değildir.

Güven skoru, iki sinyalin birleşiminden oluşturulabilir: birincisi retrieval benzerlik skoru (ilgili bilgi bulunabildi mi), ikincisi modelin kendi ifadesindeki belirsizlik (modele "bu yanıttan ne kadar eminsin, 1-10 arası puanla" diye sorulabilir, ya da yanıt içinde "emin değilim", "bilgim yok" gibi ifadeler aranabilir). Bu iki sinyal birleştirilip bir eşik belirlenir (örneğin ikisi de düşükse "insana yönlendir"); bu eşik başta kaba bir tahminle başlar, gerçek kullanım verisiyle zamanla kalibre edilir.

---

## 11. İnsan Onay Döngüsü (Human-in-the-Loop) Tasarımı

Bu tasarımın en kritik güvenlik unsuru budur: sistem hiçbir zaman doğrudan müşteriye otomatik yanıt göndermez, her yanıt bir insan tarafından onaylanır. Dashboard arayüzü şu bilgileri göstermelidir: orijinal müşteri talebi, AI'ın önerdiği kategori, kullanılan bilgi kaynakları (hangi SSS maddeleri temel alındı), üretilen taslak metni ve güven skoru. Temsilci üç işlemden birini yapabilir: olduğu gibi onaylamak, düzenleyip onaylamak veya reddedip sıfırdan yazmak. Bu üç eylem ayrı ayrı kaydedilmelidir çünkü "ne sıklıkla düzenleme gerekiyor" metriği, sistemin gerçek kalitesini ölçmenin en dürüst yoludur.

---

## 12. Değerlendirme (Eval) Stratejisi

Bir yapay zeka sisteminin "iyi çalıştığını" iddia etmek kolay, kanıtlamak zordur. Bu yüzden baştan küçük bir değerlendirme seti oluşturulmalıdır: 15-20 örnek müşteri talebi ve bunlara sizin yazacağınız "ideal" yanıtlar. Prompt'u, RAG mantığını veya model seçimini her değiştirdiğinizde, sistemin bu sete karşı ürettiği yanıtları ideal yanıtlarla karşılaştırırsınız. Karşılaştırma başta manuel (siz okuyup puanlarsınız) olabilir; sistem büyüdükçe otomatik değerlendirme (örneğin başka bir LLM'e "bu iki yanıt ne kadar benzer/kaliteli" diye sordurmak) eklenebilir.

Bu alışkanlığın değeri şuradadır: "prompt'u değiştirdim, sanırım daha iyi oldu" gibi öznel izlenimler yerine, somut, tekrar edilebilir bir ölçüm sağlar — bu, gerçek üretim AI sistemlerinde en çok atlanan ama en çok fark yaratan pratiktir.

---

## 13. Geliştirme Yol Haritası

### 1. Hafta — İskelet ve Temel Akış
FastAPI backend ve Next.js frontend projelerini kur; PostgreSQL veritabanını kur ve `tickets` tablosunu oluştur; 50-100 örnek destek talebini (CSV'den) veritabanına yükleyen bir script yaz; dashboard'da talepleri listeleyen basit bir sayfa oluştur. Bu haftanın sonunda: gerçek AI olmadan, uçtan uca "veri gösterme" akışı çalışır durumda olmalı.

### 2. Hafta — Bilgi Tabanı ve RAG
pgvector eklentisini kur; 10-20 maddelik bir SSS/dokümantasyon seti hazırla; bu içerikleri embedding'e çevirip `knowledge_base_chunks` tablosuna kaydeden bir script yaz; bir talep verildiğinde en benzer parçaları getiren bir fonksiyon yaz ve sonuçları manuel gözle kontrol et.

### 3. Hafta — Sınıflandırma ve Taslak Üretimi
LLM API entegrasyonunu kur (soyutlama katmanı ile, bkz. 6.9); sınıflandırma prompt'unu yaz ve test et; taslak üretim prompt'unu yaz (talep + retrieval sonucu + net talimatlar); dashboard'a taslağı gösterip onaylama/düzenleme özelliği ekle.

### 4. Hafta — Güven Skoru ve Eskalasyon
Güven skoru hesaplama mantığını ekle (retrieval benzerliği + model belirsizliği); düşük güvenli talepleri ayrı bir kuyruğa yönlendir; onay/düzenleme/red eylemlerini veritabanına kaydet; 15-20 maddelik eval setini oluştur ve ilk manuel değerlendirmeyi yap.

### 5. Hafta — Gerçek Entegrasyon ve Cilalama
E-posta servisi (Postmark/SendGrid) entegrasyonunu ekleyerek gerçek e-postaları alıp gönderme akışını kur; auth (Clerk/Auth0) ile temsilci girişini ekle; dashboard'a temel analitik ekle (kaç talep işlendi, ortalama düzenleme oranı, ortalama yanıt süresi).

### 6. Hafta ve Sonrası — Genişletme
Bölüm 14'teki genişletmelerden önceliklendirdiklerinizi ekleyin.

---

## 14. Genişletme Fikirleri (MVP Sonrası)

Satış tarafı için lead qualification modülü eklenebilir: talep metninden bütçe, aciliyet ve ilgi sinyalleri çıkarılarak potansiyel müşteriler önceliklendirilir. Gerçek bir CRM'e (HubSpot, Pipedrive) API entegrasyonu yapılarak talep/yanıt geçmişi otomatik senkronize edilebilir. Tool-use eklenerek AI'ın "sipariş durumu sorgula" veya "iade işlemi başlat" gibi gerçek sistem eylemlerini (elbette yine insan onayı ile) gerçekleştirmesi sağlanabilir. Çoklu dil desteği eklenebilir. Zamanla, insan düzenlemelerinden öğrenerek taslak kalitesini artıran bir geri bildirim döngüsü (örneğin sık yapılan düzenlemeleri prompt'a örnek olarak ekleme) kurulabilir.

---

## 15. Riskler ve Dikkat Edilmesi Gerekenler

Bilgi tabanı güncel olmazsa (örneğin fiyatlandırma değişip SSS güncellenmezse) model yanlış ama kendinden emin görünen yanıtlar üretebilir; bu yüzden bilgi tabanının düzenli güncellenmesi süreç olarak planlanmalıdır. Müşteri verileri (e-posta içerikleri, kişisel bilgiler) LLM API'sine gönderileceği için veri gizliliği ve KVKK/GDPR uyumluluğu baştan değerlendirilmelidir — API sağlayıcınızın veri saklama politikalarını incelemeniz gerekir. Güven skoru eşiği çok gevşek ayarlanırsa hatalı taslaklar insana ulaşmadan onaylanma riski taşır (unutmayın: her taslak zaten insana gidiyor, ama "acil inceleme" kuyruğuna mı yoksa normal kuyruğa mı düştüğü fark yaratır); bu eşik gerçek kullanım verisiyle düzenli olarak gözden geçirilmelidir. Son olarak, LLM API maliyetleri talep hacmi arttıkça büyüyebilir; bu yüzden maliyet izleme baştan kurulmalıdır (bkz. Bölüm 16).

---

## 16. Kaba Maliyet Tahmini (MVP Aşaması)

LLM API kullanımı, talep başına birkaç çağrı (sınıflandırma + taslak üretimi) yapıldığı için, ayda birkaç bin talep işleyen küçük bir sistemde tipik olarak aylık birkaç on dolar seviyesindedir — tam rakam kullanılan modele ve talep hacmine göre değişir, bu yüzden API sağlayıcısının güncel fiyatlandırma sayfasından kontrol edilmelidir. Hosting (Railway/Vercel/Fly.io) ve e-posta servisi (Postmark/SendGrid) genellikle ücretsiz/düşük maliyetli başlangıç katmanlarına sahiptir, bu da MVP'yi çok düşük bir bütçeyle canlıya almayı mümkün kılar.

---

## 17. Sonuç ve İlk Adım

Bu proje, hem gerçek bir ürün ortaya koymak hem de RAG, agent tasarımı, güven skorlama ve insan-AI iş birliği gibi güncel AI mühendisliği becerilerini uygulamalı olarak öğrenmek için iyi bir denge sunuyor. En doğru ilk adım, 1. haftanın kapsamıyla sınırlı kalıp gerçek AI entegrasyonunu erteleyerek önce iskeleti (veritabanı + basit dashboard) kurmaktır — bu, projenin geri kalanının üzerine oturacağı sağlam bir temel oluşturur ve erken aşamada "her şeyi aynı anda yapma" tuzağından kaçınmayı sağlar.
