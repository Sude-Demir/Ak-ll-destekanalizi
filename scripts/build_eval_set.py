"""Hafta 4 eval seti: gerçek taleplerden elle seçilmiş, "doğru cevap ne olmalı"
notu eklenmiş örnekleri `eval_examples` tablosuna yükler.

CLAUDE.md'nin "Kesinlikle Yapılmaması Gerekenler" kuralı: "gerçek müşteri
verisiyle, önce eval seti üzerinde test edilmeden yeni bir prompt/model
değişikliği yapmak" yasak. Bu script, o kontrolü mümkün kılan taban veriyi
oluşturur.

Örnekler `tickets` tablosundaki 300 gerçek talep arasından, 11 kategorinin
her birinden birkaç tane olacak şekilde elle seçildi (bkz. EXAMPLES). Her
örnek için `expected_answer_summary`, ilgili SSS (knowledge_base_chunks)
içeriğine dayanarak "taslak bunu içermeli" şeklinde yazıldı — LLM çıktısıyla
birebir metin eşleşmesi aranmaz, bu bir kontrol listesi niteliğindedir.
Bilgi tabanında karşılığı olmayan talepler de bilinçli olarak dahil edildi
(örn. 96, 111, 287) — sistemin "SSS'te yok" durumunu doğru tanıyıp
uydurmadığını test etmek için.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/build_eval_set.py
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent

EXAMPLES = [
    # --- ACCOUNT ---
    (139, "ACCOUNT", "SSS'te 'hesap askıya alındı' konusuna doğrudan karşılık yok; taslak müşteriden hesap detaylarını isteyip incelemeyi teklif etmeli, askıya alma sebebini uydurmamalı."),
    (222, "ACCOUNT", "recover_password SSS'ine dayanarak giriş yapıp hesap ayarlarından şifre/PIN sıfırlama adımları önerilmeli; giriş yapamadığı için bu adımların yetersiz kalabileceği kabul edilip destek ekibine yönlendirme yapılmalı."),
    (229, "ACCOUNT", "SSS'te 'hesap devre dışı bırakıldı' konusuna doğrudan karşılık yok; taslak hesap detaylarını isteyip incelemeyi teklif etmeli, kesin bir çözüm vaat etmemeli."),
    (246, "ACCOUNT", "recover_password SSS'ine dayanarak giriş/şifre sıfırlama adımları önerilmeli; numara ve e-postanın bloklanmış olmasının ayrı bir durum olduğu belirtilip ek bilgi istenmeli."),
    (264, "ACCOUNT", "edit_account SSS'ine dayanarak hesap ayarlarından bilgilerin görüntülenip düzenlenebileceği söylenmeli, sorun devam ederse destek ekibine yönlendirme yapılmalı."),
    (317, "ACCOUNT", "registration_problems SSS'ine dayanarak kayıt sürecinde yaşanan sorunun detayları (ne zaman, hangi adımda) istenmeli; bonusun neden görünmediği uydurulmamalı."),
    # --- ORDER ---
    (143, "ORDER", "Talep çok belirsiz ('siparişimle ilgili büyük bir sorun var'); taslak sorunun ne olduğunu ve sipariş numarasını sorarak netleştirme istemeli, varsayımda bulunmamalı."),
    (253, "ORDER", "change_order/complaint SSS'lerine dayanarak hangi ürünlerin eksik/yanlış olduğu ve sipariş numarası istenmeli, iade/değişim süreci başlatılacağı belirtilmeli."),
    (258, "ORDER", "place_order SSS'ine dayanarak sipariş vermek istediği ürünün detayları istenip yardımcı olunacağı belirtilmeli; telefonla sipariş alınmaması ayrı bir kısıtlama olarak not edilebilir."),
    # --- REFUND ---
    (116, "REFUND", "track_refund SSS'ine dayanarak iade durumunun kontrol edileceği belirtilmeli, bunun için işlem/sipariş numarası istenmeli."),
    (135, "REFUND", "get_refund SSS'ine dayanarak durumun detaylarının (hangi işlem, ne zaman) istenmesi gerektiği belirtilmeli."),
    (242, "REFUND", "get_refund SSS'ine dayanarak talebin detaylarının istenmesi gerektiği belirtilmeli; iadenin kesin onaylanacağı vaat edilmemeli."),
    # --- DELIVERY ---
    (120, "DELIVERY", "delivery_period SSS'ine dayanarak takip/sipariş numarası istenip teslimat durumunun araştırılacağı belirtilmeli."),
    (189, "DELIVERY", "delivery_period SSS'ine dayanarak takip numarası istenip durumun kontrol edileceği belirtilmeli."),
    (266, "DELIVERY", "delivery_period SSS'ine dayanarak sipariş/takip numarasıyla güncel tahmini teslimat bilgisinin kontrol edileceği belirtilmeli."),
    (338, "DELIVERY", "delivery_period SSS'ine dayanarak takip numarası istenip son durumun araştırılacağı belirtilmeli."),
    # --- SHIPPING ---
    (83, "SHIPPING", "change_shipping_address SSS'ine dayanarak yeni adres bilgisinin (suite numarası) paylaşılması istenmeli, güncellemenin yapılacağı belirtilmeli."),
    (185, "SHIPPING", "set_up_shipping_address/edit_account SSS'lerine dayanarak hesap ayarlarından adresin güncellenebileceği belirtilmeli."),
    # --- PAYMENT ---
    (94, "PAYMENT", "payment_issue SSS'ine dayanarak ödeme hatasının müşteri hizmetlerine (canlı destek/telefon) bildirilmesi gerektiği belirtilmeli."),
    (158, "PAYMENT", "payment_issue SSS'ine dayanarak durumun detayları istenip destek ekibine iletileceği belirtilmeli; ücretin iade edileceği kesin olarak vaat edilmemeli."),
    (226, "PAYMENT", "payment_issue SSS'ine dayanarak işlem detaylarının paylaşılması istenip destek ekibine yönlendirileceği belirtilmeli."),
    # --- INVOICE ---
    (142, "INVOICE", "check_invoice SSS'ine dayanarak fatura numarası istenip kayıtların kontrol edileceği belirtilmeli."),
    (186, "INVOICE", "check_invoice SSS'ine dayanarak fatura detaylarının incelenmesi için bilgi istenmeli, vergi hatasının nedeni uydurulmamalı."),
    (168, "INVOICE", "check_invoice/get_invoice SSS'lerine dayanarak fatura numarası istenip artışın nedeninin araştırılacağı belirtilmeli."),
    # --- CANCEL ---
    (160, "CANCEL", "check_cancellation_fee SSS'ine dayanarak rezervasyon detayları istenip iptal ücretinin kontrol edileceği belirtilmeli."),
    (375, "CANCEL", "check_cancellation_fee/cancel_order SSS'lerine dayanarak hangi uygulamaların iptal edilmek istendiği ve sipariş/fatura numarası istenmeli."),
    # --- CONTACT ---
    (200, "CONTACT", "Talep çok belirsiz ('acil yardım lazım'); contact_customer_service SSS'ine dayanarak ne konuda yardım istediği sorulmalı, varsayımda bulunulmamalı."),
    (318, "CONTACT", "contact_human_agent SSS'ine dayanarak bir temsilciye bağlanacağı belirtilmeli, sorunun kısaca özetlenmesinin süreci hızlandıracağı söylenmeli."),
    (182, "CONTACT", "contact_customer_service SSS'ine dayanarak destek ekibine ulaşım saatleri/kanalları paylaşılmalı, yaşanan gecikme için özür belirtilmeli."),
    # --- FEEDBACK ---
    (221, "FEEDBACK", "complaint SSS'ine dayanarak şikayetin türü/detayları istenip sürecin başlatılacağı belirtilmeli."),
    (96, "FEEDBACK", "SSS'te uçuş/havayolu konularına doğrudan karşılık yok; taslak bunu açıkça belirtip durumu inceleyeceğini söylemeli, uydurma bilgi vermemeli."),
    (271, "FEEDBACK", "complaint SSS'ine dayanarak yaşanan sorunun detayları istenip şikayetin kayda alınacağı belirtilmeli."),
    (111, "FEEDBACK", "SSS'te uçuş/bagaj konularına doğrudan karşılık yok; taslak bunu açıkça belirtip genel bir özür + detay isteme yaklaşımı sergilemeli, uydurma bilgi vermemeli."),
    # --- SUBSCRIPTION ---
    (287, "SUBSCRIPTION", "SSS'teki tek SUBSCRIPTION kaydı (haber bülteni aboneliğinden çıkma) bu duruma tam karşılık vermiyor; taslak bunu açıkça belirtip hesap/üyelik detaylarının istenmesi gerektiğini söylemeli, üyeliğin neden iptal edildiğini uydurmamalı."),
]


def load_eval_set() -> None:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eval_examples")
            for ticket_id, expected_category, expected_answer_summary in EXAMPLES:
                cur.execute(
                    """
                    INSERT INTO eval_examples (ticket_id, expected_category, expected_answer_summary)
                    VALUES (%s, %s, %s)
                    """,
                    (ticket_id, expected_category, expected_answer_summary),
                )
        conn.commit()
        print(f"{len(EXAMPLES)} eval örneği eval_examples tablosuna yüklendi.")
    finally:
        conn.close()


if __name__ == "__main__":
    load_eval_set()
