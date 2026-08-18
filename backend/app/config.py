from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Proje kökündeki .env dosyası (backend/app/config.py -> backend/app -> backend -> kök)
ROOT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Uygulama genelinde kullanılan ortam değişkenleri."""

    database_url: str
    gemini_api_key: str | None = None
    clerk_secret_key: str | None = None

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8")


settings = Settings()
