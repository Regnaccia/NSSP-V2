"""
Dependency FastAPI per accesso riservato al ruolo admin.
"""

from fastapi import Depends, HTTPException, status

from nssp_v2.app.deps.auth import get_current_user


def require_admin(payload: dict = Depends(get_current_user)) -> dict:
    """Verifica che il token Bearer appartenga a un utente con ruolo admin.

    Lancia 403 se il ruolo admin non è presente nel token.
    """
    if "admin" not in payload.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli amministratori",
        )
    return payload
