"""Bir talep satış fırsatı (lead) olarak işaretlendiğinde HubSpot CRM'e
senkronize eder (bkz. CLAUDE.md Hafta 6 son fikri "CRM entegrasyonu").

Müşteriyi bir HubSpot "contact"ı, talebi de o contact'a bağlı bir "deal"
olarak temsil eder. Bilinçli olarak stdlib `urllib` kullanılıyor (bkz.
CLAUDE.md "ince soyutlama, ağır framework değil") — resmi `hubspot-api-client`
SDK'sı yerine birkaç düz REST çağrısı için ayrı bir bağımlılık eklemeye gerek
yok (aynı tercih app.services.slack_notify'da da yapıldı).

Yapılandırılmışsa (HUBSPOT_ACCESS_TOKEN) çalışır; ayarlı değilse veya
herhangi bir adımda ağ/API hatası olursa best-effort — sessizce atlanır, bu
bir yan kanal senkronizasyonudur, ana ticket/taslak akışını asla bozmamalı
(bkz. app.services.slack_notify ile aynı prensip).
"""

import json
import urllib.error
import urllib.request

from app.config import settings

HUBSPOT_BASE_URL = "https://api.hubapi.com"


def _request(method: str, path: str, body: dict | None = None) -> dict | None:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{HUBSPOT_BASE_URL}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {settings.hubspot_access_token}",
            "Content-Type": "application/json",
        },
    )
    response = urllib.request.urlopen(request, timeout=10)
    raw = response.read()
    response.close()
    return json.loads(raw) if raw else None


def _find_contact_id(email: str) -> str | None:
    """E-postaya göre var olan bir contact arar — aynı müşteri birden fazla
    lead'e sahip olursa HubSpot'ta yinelenen kayıt oluşmasın diye."""
    result = _request(
        "POST",
        "/crm/v3/objects/contacts/search",
        {"filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}]},
    )
    results = (result or {}).get("results", [])
    return results[0]["id"] if results else None


def _create_contact(email: str, name: str) -> str:
    result = _request("POST", "/crm/v3/objects/contacts", {"properties": {"email": email, "firstname": name}})
    return result["id"]


def _default_pipeline_and_stage() -> tuple[str, str]:
    """Hesabın ilk (varsayılan) deal pipeline'ını ve o pipeline'ın ilk
    aşamasını döner — sabit bir pipeline/stage id'si HARDCODE edilmiyor,
    çünkü bu değerler hesaptan hesaba (dil, özelleştirme) değişebilir."""
    result = _request("GET", "/crm/v3/pipelines/deals")
    pipeline = result["results"][0]
    return pipeline["id"], pipeline["stages"][0]["id"]


def _create_deal(deal_name: str) -> str:
    pipeline_id, stage_id = _default_pipeline_and_stage()
    result = _request(
        "POST",
        "/crm/v3/objects/deals",
        {"properties": {"dealname": deal_name, "pipeline": pipeline_id, "dealstage": stage_id}},
    )
    return result["id"]


def _associate_deal_with_contact(deal_id: str, contact_id: str) -> None:
    _request("PUT", f"/crm/v4/objects/deals/{deal_id}/associations/default/contacts/{contact_id}")


def sync_lead_to_hubspot(customer_name: str, customer_email: str, ticket_subject: str) -> None:
    """Müşteriyi (varsa mevcut kaydı kullanır, yoksa oluşturur) ve bu talebi
    temsil eden bir deal oluşturup ikisini ilişkilendirir. HUBSPOT_ACCESS_TOKEN
    ayarlı değilse hiçbir şey yapmaz. Herhangi bir adımda hata olursa sessizce
    yutulur (best-effort, bkz. modül docstring'i)."""
    if not settings.hubspot_access_token:
        return
    try:
        contact_id = _find_contact_id(customer_email) or _create_contact(customer_email, customer_name)
        deal_id = _create_deal(ticket_subject)
        _associate_deal_with_contact(deal_id, contact_id)
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError):
        pass
