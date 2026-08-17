"""knowledge_base_chunks tablosunda embedding'i boş (NULL) olan satırları Gemini
embedding API'siyle doldurur.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/embed_kb.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.database import SessionLocal  # noqa: E402
from app.models import KnowledgeBaseChunk  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        chunks = (
            db.query(KnowledgeBaseChunk)
            .filter(KnowledgeBaseChunk.embedding.is_(None))
            .all()
        )
        print(f"{len(chunks)} kayıt embed edilecek.")
        for i, chunk in enumerate(chunks, start=1):
            # Soru + cevabı birlikte embed ediyoruz ki hem "müşteri ne sordu"
            # hem "buna nasıl cevap verilir" anlamı vektöre yansısın.
            text = f"{chunk.question}\n{chunk.answer}"
            chunk.embedding = embed_text(text)
            print(f"  [{i}/{len(chunks)}] {chunk.intent} embed edildi.")
        db.commit()
        print(f"{len(chunks)} kayıt güncellendi.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
