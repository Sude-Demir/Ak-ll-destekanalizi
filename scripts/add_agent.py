"""Bir Clerk kullanıcısını, VAR OLAN bir şirketin temsilcisi (agent) olarak işaretler.

Giriş yapan bir kişinin `/dashboard` mü `/portal` mı göreceğine `agents`
tablosundaki kaydı belirler (bkz. backend/app/auth.py require_agent). Yeni
bir şirketin İLK temsilcisini eklemek için bunun yerine
`scripts/create_company.py` kullanılmalı — bu script sadece mevcut bir
şirkete YENİ temsilci eklemek içindir.

Clerk kullanıcı kimliğini bulmak için: giriş yaptıktan sonra
`GET /me` uç noktasının döndürdüğü `clerk_user_id` alanına bakılabilir,
ya da Clerk panelindeki kullanıcı detay sayfasından okunabilir.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/add_agent.py genel user_2abc... "Sude Demir"
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.database import SessionLocal  # noqa: E402
from app.models import Agent, Company  # noqa: E402


def main(company_slug: str, clerk_user_id: str, name: str) -> None:
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.slug == company_slug).one_or_none()
        if company is None:
            print(f"'{company_slug}' slug'lı bir şirket bulunamadı.")
            return

        existing = db.query(Agent).filter(Agent.clerk_user_id == clerk_user_id).one_or_none()
        if existing is not None:
            print(f"Bu kullanıcı zaten temsilci: {existing.name} (şirket id {existing.company_id})")
            return

        agent = Agent(clerk_user_id=clerk_user_id, company_id=company.id, name=name)
        db.add(agent)
        db.commit()
        print(f"Temsilci eklendi: {name} ({clerk_user_id}) — {company.name}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Kullanım: python scripts/add_agent.py <şirket-slug> <clerk_user_id> "<Ad Soyad>"')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
