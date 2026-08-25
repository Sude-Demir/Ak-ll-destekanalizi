"""Yapılandırılmışsa (SLACK_WEBHOOK_URL) yeni lead/acil talep uyarılarını
Slack'e gönderir — bkz. CLAUDE.md 'özgün 10 özellik' listesi #10.

Bilinçli olarak stdlib `urllib` kullanılıyor (bkz. CLAUDE.md 'ince soyutlama,
ağır framework değil') — tek bir POST isteği için yeni bir HTTP kütüphanesi
bağımlılığı eklemeye gerek yok.
"""

import json
import urllib.error
import urllib.request

from app.config import settings


def send_slack_alert(message: str) -> None:
    """Best-effort: SLACK_WEBHOOK_URL ayarlı değilse hiçbir şey yapmaz;
    ayarlıysa gönderir ama ağ hatası/yanlış URL durumunda sessizce yutar —
    bu bir yan kanal bildirimi, asla ticket/taslak akışını bozmamalı (bkz.
    app.routers.drafts _notify_if_flagged, in-app bildirim zaten ana kanal)."""
    if not settings.slack_webhook_url:
        return

    request = urllib.request.Request(
        settings.slack_webhook_url,
        data=json.dumps({"text": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=5)
    except (urllib.error.URLError, ValueError, TimeoutError):
        pass
