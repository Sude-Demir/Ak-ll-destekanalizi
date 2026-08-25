from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Proje kökündeki .env dosyası (backend/app/config.py -> backend/app -> backend -> kök)
ROOT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Uygulama genelinde kullanılan ortam değişkenleri."""

    database_url: str
    gemini_api_key: str | None = None
    clerk_secret_key: str | None = None
    # Postmark'ın gelen e-posta webhook'unu doğrulamak için (Basic Auth).
    # Webhook URL'sine gömülür: https://<user>:<pass>@.../webhooks/inbound-email
    webhook_username: str | None = None
    webhook_password: str | None = None
    # Yapılandırılırsa, yeni bir lead/acil talep tespit edildiğinde buraya da
    # bir Slack mesajı gönderilir (bkz. app.services.slack_notify). Boşsa
    # bu adım sessizce atlanır — in-app bildirim tek başına yeterli.
    slack_webhook_url: str | None = None

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8")


settings = Settings()
