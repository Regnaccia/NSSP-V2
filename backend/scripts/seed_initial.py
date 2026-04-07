"""
Seed iniziale: crea ruoli base e utente admin.

Uso:
    cd backend
    python scripts/seed_initial.py

Prerequisiti:
    - venv attivo con dipendenze installate
    - PostgreSQL attivo e raggiungibile
    - DATABASE_URL configurata (.env o variabile d'ambiente)
    - alembic upgrade head gia eseguito

La password viene hashata con bcrypt (passlib).
"""

import sys
from pathlib import Path

# Permette di eseguire lo script da backend/ senza installare il package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session

from nssp_v2.app.models.access import Role, User, UserRole
from nssp_v2.shared.config import settings
from nssp_v2.shared.db import engine
from nssp_v2.shared.security import hash_password

INITIAL_ROLES = ["admin", "produzione", "logistica", "magazzino"]
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme"  # da cambiare prima dell'uso in produzione


def seed(session: Session) -> None:
    print(f"DATABASE_URL: {settings.database_url}\n")

    # Ruoli
    roles: dict[str, Role] = {}
    for name in INITIAL_ROLES:
        role = session.query(Role).filter_by(name=name).first()
        if not role:
            role = Role(name=name)
            session.add(role)
            print(f"  + ruolo creato: {name}")
        else:
            print(f"  = ruolo gia presente: {name}")
        roles[name] = role
    session.flush()

    # Utente admin
    user = session.query(User).filter_by(username=ADMIN_USERNAME).first()
    if not user:
        user = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            attivo=True,
        )
        session.add(user)
        print(f"\n  + utente creato: {ADMIN_USERNAME}")
    else:
        # Aggiorna l'hash se non è bcrypt (es. hash sha256 da seed precedente)
        if not user.password_hash.startswith("$2"):
            user.password_hash = hash_password(ADMIN_PASSWORD)
            print(f"\n  ~ hash aggiornato a bcrypt: {ADMIN_USERNAME}")
        else:
            print(f"\n  = utente gia presente: {ADMIN_USERNAME}")
    session.flush()

    # Mapping admin -> ruolo admin
    admin_role = roles["admin"]
    mapping = (
        session.query(UserRole)
        .filter_by(user_id=user.id, role_id=admin_role.id)
        .first()
    )
    if not mapping:
        session.add(UserRole(user_id=user.id, role_id=admin_role.id))
        print(f"  + mapping creato: {ADMIN_USERNAME} -> admin")
    else:
        print(f"  = mapping gia presente: {ADMIN_USERNAME} -> admin")

    session.commit()
    print("\nSeed completato.")


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
