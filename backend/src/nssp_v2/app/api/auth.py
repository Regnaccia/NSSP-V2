"""
Router autenticazione browser.

Endpoint:
  POST /auth/login  — login nominale, restituisce token + profilo sessione
  GET  /auth/me     — profilo sessione corrente (richiede token valido)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.app.models.access import User, UserRole
from nssp_v2.app.schemas.auth import LoginRequest, LoginResponse, SessionResponse, Surface
from nssp_v2.shared.db import get_session
from nssp_v2.shared.security import (
    create_access_token,
    get_available_surfaces,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_session_response(user_id: int, username: str, roles: list[str]) -> dict:
    surfaces = get_available_surfaces(roles)
    return {
        "user_id": user_id,
        "username": username,
        "roles": roles,
        "access_mode": "browser",
        "available_surfaces": [Surface(**s) for s in surfaces],
    }


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.scalars(
        select(User)
        .where(User.username == body.username, User.attivo == True)  # noqa: E712
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    ).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )

    roles = [ur.role.name for ur in user.user_roles]
    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "roles": roles,
            "access_mode": "browser",
        }
    )

    return LoginResponse(
        access_token=token,
        **_build_session_response(user.id, user.username, roles),
    )


@router.get("/me", response_model=SessionResponse)
def me(payload: dict = Depends(get_current_user)):
    roles = payload.get("roles", [])
    return SessionResponse(
        **_build_session_response(
            user_id=int(payload["sub"]),
            username=payload["username"],
            roles=roles,
        )
    )
