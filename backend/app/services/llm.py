"""Gemini metin üretim (chat) API'si için ince bir sarmalayıcı.

CLAUDE.md'nin "ince soyutlama, ağır framework değil" prensibine uygun: tüm LLM
çağrıları bu tek `call_llm` fonksiyonu üzerinden geçer. Sağlayıcı değişirse
(örn. başka bir modele geçilirse) tek değiştirilmesi gereken yer burasıdır.
"""

import time

from google import genai
from google.genai import errors

from app.config import settings

# "gemini-flash-latest" takma adını denedik ama şu an aşırı talep nedeniyle 503
# hatası veriyor (Google'ın en yoğun kullanılan takma adı olduğu için). Somut,
# stabil bir sürüm adı kullanıyoruz; kullanımdan kaldırılırsa (embedding
# modelinde olduğu gibi) client.models.list() ile güncel listeye bakılabilir.
CHAT_MODEL = "gemini-2.5-flash"

# Ücretsiz katmanda model zaman zaman "503 UNAVAILABLE / yüksek talep" hatası
# veriyor; bu geçici bir durum olduğu için birkaç kez, artan bekleme süresiyle
# yeniden deniyoruz.
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def call_llm(prompt: str, context: str = "") -> str:
    """`prompt` (görev talimatı) ve `context`i (ilgili veri) birleştirip Gemini'ye
    gönderir, üretilen metni döner. Geçici sunucu hatalarında (503) birkaç kez
    yeniden dener."""
    client = _get_client()
    full_prompt = f"{prompt}\n\n{context}" if context else prompt

    last_error: errors.ServerError | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model=CHAT_MODEL, contents=full_prompt)
            return response.text
        except errors.ServerError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise last_error
