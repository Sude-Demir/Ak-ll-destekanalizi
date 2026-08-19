"""Yeni bir şirket (kiracı) ve onun İLK temsilcisini tek seferde oluşturur.

Bu, sistemde henüz hiç şirketi olmayan biri için "bootstrap" (ilk kurulum)
script'idir — kendiliğinden şirket kaydı (self-servis) ekranı henüz yok.
Şirket oluştuktan sonra ikinci ve sonraki temsilciler `scripts/add_agent.py`
veya panelden davet linki ile eklenebilir.

`slug`, hem herkese açık talep formunun URL'sinde (`/support/{slug}`) hem
gelen e-posta adresinde (`adres+{slug}@inbound.postmarkapp.com`) kullanılır
— küçük harf, rakam ve tireden oluşmalı.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/create_company.py akme-ltd "Akme Ltd" user_2abc... "Sude Demir"
"""

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.database import SessionLocal  # noqa: E402
from app.models import Agent, Company  # noqa: E402

SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


def main(slug: str, company_name: str, clerk_user_id: str, agent_name: str) -> None:
    if not SLUG_PATTERN.match(slug):
        print("Slug sadece küçük harf, rakam ve tireden oluşabilir (örn. 'akme-ltd').")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(Company).filter(Company.slug == slug).one_or_none()
        if existing is not None:
            print(f"'{slug}' slug'lı bir şirket zaten var: {existing.name}")
            return

        existing_agent = db.query(Agent).filter(Agent.clerk_user_id == clerk_user_id).one_or_none()
        if existing_agent is not None:
            print(f"Bu kullanıcı zaten başka bir şirketin temsilcisi (şirket id {existing_agent.company_id}).")
            return

        company = Company(slug=slug, name=company_name)
        db.add(company)
        db.flush()  # commit etmeden company.id'yi almak için

        agent = Agent(clerk_user_id=clerk_user_id, company_id=company.id, name=agent_name)
        db.add(agent)
        db.commit()

        print(f"Şirket oluşturuldu: {company_name} (/support/{slug})")
        print(f"İlk temsilci eklendi: {agent_name} ({clerk_user_id})")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            'Kullanım: python scripts/create_company.py <slug> "<Şirket Adı>" '
            '<clerk_user_id> "<Temsilci Adı>"'
        )
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
