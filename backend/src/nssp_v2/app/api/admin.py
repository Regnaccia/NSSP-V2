"""
Router surface admin — access management e warning config.

Endpoint:
  GET  /api/admin/users                          — lista utenti
  POST /api/admin/users                          — crea utente
  PATCH /api/admin/users/{id}/active             — attiva/disattiva utente
  PUT  /api/admin/users/{id}/roles               — sostituisce i ruoli dell'utente
  GET  /api/admin/warnings/config                — lista config visibilita warning (TASK-V2-077)
  PUT  /api/admin/warnings/config/{warning_type} — aggiorna visibilita per un tipo warning
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nssp_v2.app.deps.admin import require_admin
from nssp_v2.app.models.access import Role, User, UserRole
from nssp_v2.app.schemas.admin import (
    CreateUserRequest,
    SetActiveRequest,
    SetRolesRequest,
    UpdateWarningConfigRequest,
    UserListItem,
)
from nssp_v2.app.schemas.auth import Surface
from nssp_v2.app.services.admin_policy import assert_not_last_active_admin
from nssp_v2.core.warnings import (
    KNOWN_WARNING_TYPES,
    WarningTypeConfigItem,
    list_warning_configs,
    set_warning_config,
)
from nssp_v2.core.warnings.config import KNOWN_AREAS
from nssp_v2.shared.db import get_session
from nssp_v2.shared.security import get_available_surfaces, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

_LOAD_ROLES = selectinload(User.user_roles).selectinload(UserRole.role)


def _active_admin_ids(session: Session) -> list[int]:
    """Restituisce gli ID degli utenti attivi con ruolo admin."""
    users = session.scalars(
        select(User).where(User.attivo == True).options(_LOAD_ROLES)  # noqa: E712
    ).all()
    return [u.id for u in users if any(ur.role.name == "admin" for ur in u.user_roles)]


def _to_item(user: User) -> UserListItem:
    roles = [ur.role.name for ur in user.user_roles]
    return UserListItem(
        id=user.id,
        username=user.username,
        attivo=user.attivo,
        roles=roles,
        available_surfaces=[Surface(**s) for s in get_available_surfaces(roles)],
    )


@router.get("/users", response_model=list[UserListItem])
def list_users(
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    users = session.scalars(
        select(User).order_by(User.username).options(_LOAD_ROLES)
    ).all()
    return [_to_item(u) for u in users]


@router.post("/users", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    existing = session.scalars(
        select(User).where(User.username == body.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' già in uso",
        )

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        attivo=True,
    )
    session.add(user)
    session.flush()

    for role_name in body.roles:
        role = session.scalars(select(Role).where(Role.name == role_name)).first()
        if role:
            session.add(UserRole(user_id=user.id, role_id=role.id))

    session.commit()
    session.refresh(user)

    # Ricarica con ruoli
    user = session.scalars(
        select(User).where(User.id == user.id).options(_LOAD_ROLES)
    ).one()
    return _to_item(user)


@router.patch("/users/{user_id}/active", response_model=UserListItem)
def set_user_active(
    user_id: int,
    body: SetActiveRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    user = session.scalars(
        select(User).where(User.id == user_id).options(_LOAD_ROLES)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    # Policy: impossibile disattivare l'ultimo admin attivo
    if not body.attivo and any(ur.role.name == "admin" for ur in user.user_roles):
        assert_not_last_active_admin(user_id, _active_admin_ids(session))

    user.attivo = body.attivo
    session.commit()
    session.refresh(user)

    user = session.scalars(
        select(User).where(User.id == user_id).options(_LOAD_ROLES)
    ).one()
    return _to_item(user)


@router.put("/users/{user_id}/roles", response_model=UserListItem)
def set_user_roles(
    user_id: int,
    body: SetRolesRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    user = session.scalars(
        select(User).where(User.id == user_id).options(_LOAD_ROLES)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    had_admin = any(ur.role.name == "admin" for ur in user.user_roles)
    will_have_admin = "admin" in body.roles

    # Policy: impossibile rimuovere ruolo admin dall'ultimo admin attivo
    if had_admin and not will_have_admin and user.attivo:
        assert_not_last_active_admin(user_id, _active_admin_ids(session))

    # Sostituisce tutti i ruoli
    for ur in list(user.user_roles):
        session.delete(ur)
    session.flush()

    for role_name in body.roles:
        role = session.scalars(select(Role).where(Role.name == role_name)).first()
        if role:
            session.add(UserRole(user_id=user.id, role_id=role.id))

    session.commit()

    user = session.scalars(
        select(User).where(User.id == user_id).options(_LOAD_ROLES)
    ).one()
    return _to_item(user)


# ─── Warning config (TASK-V2-077) ─────────────────────────────────────────────

@router.get("/warnings/config", response_model=list[WarningTypeConfigItem])
def get_warnings_config(
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Lista la configurazione di visibilita per tutti i tipi warning noti."""
    return list_warning_configs(session)


@router.put("/warnings/config/{warning_type}", response_model=WarningTypeConfigItem)
def update_warning_config(
    warning_type: str,
    body: UpdateWarningConfigRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Aggiorna le aree/reparti in cui un tipo warning e visibile.

    warning_type deve essere un tipo noto (es. NEGATIVE_STOCK).
    visible_to_areas e la lista aggiornata di codici area (magazzino, produzione, logistica).
    Valori non in KNOWN_AREAS vengono accettati ma ignorati nelle surface operative.
    """
    if warning_type not in KNOWN_WARNING_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo warning non ammesso: {warning_type}. Ammessi: {KNOWN_WARNING_TYPES}",
        )
    unknown = [a for a in body.visible_to_areas if a not in KNOWN_AREAS]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Aree non ammesse: {unknown}. Ammesse: {KNOWN_AREAS}",
        )
    return set_warning_config(session, warning_type, body.visible_to_areas)
