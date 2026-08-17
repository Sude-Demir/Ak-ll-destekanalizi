"""Gemini embedding API için ince bir sarmalayıcı (wrapper).

CLAUDE.md'nin "ince soyutlama, ağır framework değil" prensibine uygun: embedding
sağlayıcısını (Gemini -> başka bir servis) değiştirmek istersek tek bu dosyayı
değiştirmemiz yeterli olur.
"""

from google import genai
from google.genai import types

from app.config import settings

# gemini-embedding-001 varsayılan olarak 3072 boyutlu vektör üretir; pgvector
# tablosunu daha küçük/hızlı tutmak için Matryoshka kısaltmasıyla 768'e indiriyoruz
# (bkz. backend/app/models/knowledge_base_chunk.py EMBEDDING_DIM).
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_text(text: str) -> list[float]:
    """Verilen metni Gemini'nin embedding modeliyle sayısal vektöre (768 boyutlu) çevirir."""
    client = _get_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
    )
    return result.embeddings[0].values
