import urllib.error
from unittest.mock import patch

from app.services.slack_notify import send_slack_alert


def test_skips_silently_when_no_webhook_configured():
    with (
        patch("app.services.slack_notify.settings") as mock_settings,
        patch("app.services.slack_notify.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.slack_webhook_url = None
        send_slack_alert("Yeni acil talep: Test")

    mock_urlopen.assert_not_called()


def test_posts_json_body_to_configured_webhook():
    with (
        patch("app.services.slack_notify.settings") as mock_settings,
        patch("app.services.slack_notify.urllib.request.urlopen") as mock_urlopen,
    ):
        mock_settings.slack_webhook_url = "https://hooks.slack.com/services/test"
        send_slack_alert("Yeni acil talep: Test")

    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://hooks.slack.com/services/test"
    assert b"Yeni acil talep" in request.data


def test_swallows_network_errors_without_raising():
    with (
        patch("app.services.slack_notify.settings") as mock_settings,
        patch(
            "app.services.slack_notify.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ),
    ):
        mock_settings.slack_webhook_url = "https://hooks.slack.com/services/test"
        send_slack_alert("Yeni acil talep: Test")  # raise etmemeli
