"""Bir Clerk kullanıcısını temsilci (agent) olarak işaretler.

Giriş yapan bir kişinin `/dashboard` mü `/portal` mı göreceğine `agents`
tablosundaki kaydı belirler (bkz. backend/app/auth.py require_agent). Henüz
bir temsilci davet ekranı yok — ilk temsilciyi (genelde kendi hesabını)
eklemek için bu script kullanılır.

Clerk kullanıcı kimliğini bulmak için: giriş yaptıktan sonra
`GET /me` uç noktasının döndürdüğü `clerk_user_id` alanına bakılabilir,
ya da Clerk panelindeki kullanıcı detay sayfasından okunabilir.

Kullanım (proje kökünden, backend sanal ortamı aktifken):
    source backend/.venv/Scripts/activate
    python scripts/add_agent.py user_2abc... "Sude Demir"
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.database import SessionLocal  # noqa: E402
from app.models import Agent  # noqa: E402


def main(clerk_user_id: str, name: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(Agent).filter(Agent.clerk_user_id == clerk_user_id).one_or_none()
        if existing is not None:
            print(f"Bu kullanıcı zaten temsilci: {existing.name} ({existing.clerk_user_id})")
            return

        agent = Agent(clerk_user_id=clerk_user_id, name=name)
        db.add(agent)
        db.commit()
        print(f"Temsilci eklendi: {name} ({clerk_user_id})")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Kullanım: python scripts/add_agent.py <clerk_user_id> "<Ad Soyad>"')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
