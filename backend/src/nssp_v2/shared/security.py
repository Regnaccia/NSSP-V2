"""
Utility di sicurezza: hashing password e gestione token JWT.

Non contiene logica di dominio.
Usato da: app layer (auth router, deps).
"""

from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import jwt

from nssp_v2.shared.config import settings

# Mapping statico ruolo -> superficie applicativa (DL-ARCH-V2-004 §7)
_SURFACE_MAP: dict[str, dict[str, str]] = {
    "admin": {"path": "/admin", "label": "Admin"},
    "produzione": {"path": "/produzione", "label": "Produzione"},
    "logistica": {"path": "/logistica", "label": "Logistica"},
    "magazzino": {"path": "/magazzino", "label": "Magazzino"},
}


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decodifica e verifica il token. Lancia JWTError se non valido."""
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )


def get_available_surfaces(roles: list[str]) -> list[dict[str, str]]:
    """Calcola le superfici disponibili dall'insieme di ruoli utente."""
    return [
        {"role": role, **_SURFACE_MAP[role]}
        for role in roles
        if role in _SURFACE_MAP
    ]
