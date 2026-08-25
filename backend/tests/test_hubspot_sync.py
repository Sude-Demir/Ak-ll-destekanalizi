import json
import urllib.error
from unittest.mock import MagicMock, patch

from app.services.hubspot_sync import sync_lead_to_hubspot


def _response(body: dict | None) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8") if body is not None else b""
    return resp


def test_skips_silently_when_no_token_configured():
    with (
        patch("app.services.hubspot_sync.settings") as mock_settings,
        patch("app.services.hubspot_sync.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.hubspot_access_token = None
        sync_lead_to_hubspot("Ada Lovelace", "ada@example.com", "Toplu sipariş talebi")

    mock_urlopen.assert_not_called()


def test_creates_new_contact_and_deal_then_associates_them():
    with (
        patch("app.services.hubspot_sync.settings") as mock_settings,
        patch("app.services.hubspot_sync.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.hubspot_access_token = "pat-na1-test"
        mock_urlopen.side_effect = [
            _response({"results": []}),  # contact search: bulunamadı
            _response({"id": "contact-1"}),  # contact create
            _response({"results": [{"id": "pipeline-1", "stages": [{"id": "stage-1"}]}]}),  # pipelines
            _response({"id": "deal-1"}),  # deal create
            _response(None),  # associate (boş yanıt)
        ]

        sync_lead_to_hubspot("Ada Lovelace", "ada@example.com", "Toplu sipariş talebi")

    assert mock_urlopen.call_count == 5
    requests = [call.args[0] for call in mock_urlopen.call_args_list]
    assert requests[0].full_url == "https://api.hubapi.com/crm/v3/objects/contacts/search"
    assert requests[1].full_url == "https://api.hubapi.com/crm/v3/objects/contacts"
    assert requests[2].full_url == "https://api.hubapi.com/crm/v3/pipelines/deals"
    assert requests[3].full_url == "https://api.hubapi.com/crm/v3/objects/deals"
    assert requests[4].full_url == "https://api.hubapi.com/crm/v4/objects/deals/deal-1/associations/default/contacts/contact-1"

    deal_body = json.loads(requests[3].data)
    assert deal_body["properties"]["dealname"] == "Toplu sipariş talebi"
    assert deal_body["properties"]["pipeline"] == "pipeline-1"
    assert deal_body["properties"]["dealstage"] == "stage-1"


def test_reuses_existing_contact_instead_of_creating_a_duplicate():
    with (
        patch("app.services.hubspot_sync.settings") as mock_settings,
        patch("app.services.hubspot_sync.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.hubspot_access_token = "pat-na1-test"
        mock_urlopen.side_effect = [
            _response({"results": [{"id": "existing-contact"}]}),  # contact search: bulundu
            _response({"results": [{"id": "pipeline-1", "stages": [{"id": "stage-1"}]}]}),  # pipelines
            _response({"id": "deal-2"}),  # deal create
            _response(None),  # associate
        ]

        sync_lead_to_hubspot("Ada Lovelace", "ada@example.com", "İkinci talep")

    assert mock_urlopen.call_count == 4  # contact create ATLANDI
    last_request = mock_urlopen.call_args_list[-1].args[0]
    assert last_request.full_url.endswith("/associations/default/contacts/existing-contact")


def test_swallows_network_errors_without_raising():
    with (
        patch("app.services.hubspot_sync.settings") as mock_settings,
        patch(
            "app.services.hubspot_sync.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ),
    ):
        mock_settings.hubspot_access_token = "pat-na1-test"
        sync_lead_to_hubspot("Ada Lovelace", "ada@example.com", "Toplu sipariş talebi")  # raise etmemeli


def test_swallows_malformed_response_without_raising():
    """Örneğin pipelines listesi boş dönerse (IndexError) — best-effort, hata
    fırlatmamalı."""
    with (
        patch("app.services.hubspot_sync.settings") as mock_settings,
        patch("app.services.hubspot_sync.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.hubspot_access_token = "pat-na1-test"
        mock_urlopen.side_effect = [
            _response({"results": []}),
            _response({"id": "contact-1"}),
            _response({"results": []}),  # pipelines BOŞ -> IndexError beklenir, yutulmalı
        ]

        sync_lead_to_hubspot("Ada Lovelace", "ada@example.com", "Toplu sipariş talebi")  # raise etmemeli
