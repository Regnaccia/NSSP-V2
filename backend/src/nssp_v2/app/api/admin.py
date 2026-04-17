"""
Router surface admin — access management e warning config.

Endpoint:
  GET  /api/admin/users                          — lista utenti
  POST /api/admin/users                          — crea utente
  PATCH /api/admin/users/{id}/active             — attiva/disattiva utente
  PUT  /api/admin/users/{id}/roles               — sostituisce i ruoli dell'utente
  GET  /api/admin/warnings/config                — lista config visibilita warning (TASK-V2-077)
  PUT  /api/admin/warnings/config/{warning_type} — aggiorna visibilita per un tipo warning
  GET  /api/admin/stock-logic/config             — configurazione logiche stock V1 (TASK-V2-090)
  PUT  /api/admin/stock-logic/config             — aggiorna configurazione logiche stock V1
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
from nssp_v2.core.stock_policy import (
    KNOWN_MONTHLY_BASE_STRATEGIES,
    CAPACITY_LOGIC_KEY,
    StockLogicConfig,
    get_stock_logic_config,
    set_stock_logic_config,
)
from nssp_v2.core.production_proposals import (
    KNOWN_PROPOSAL_LOGICS,
    ProposalLogicConfig,
    get_proposal_logic_config,
    set_proposal_logic_config,
)
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
    # Filtra aree non ammesse (non rifiuta: il contratto dichiarato e "accettate ma ignorate")
    valid_areas = [a for a in body.visible_to_areas if a in KNOWN_AREAS]
    return set_warning_config(session, warning_type, valid_areas)


# ─── Stock logic config (TASK-V2-090) ─────────────────────────────────────────

class StockLogicConfigResponse(StockLogicConfig):
    """Risposta estesa della configurazione logiche stock V1.

    Aggiunge `known_strategies` alla risposta per consentire alla UI
    di costruire il selettore senza hardcoding lato frontend.
    """
    known_strategies: list[str]


class SetStockLogicConfigRequest(BaseModel):
    """Body PUT /admin/stock-logic/config (TASK-V2-090).

    monthly_base_strategy_key: deve essere in KNOWN_MONTHLY_BASE_STRATEGIES.
    monthly_base_params: parametri specifici della strategy (dict JSON).
    capacity_logic_params: parametri della logica capacity fissa (dict JSON, solitamente {}).
    """
    monthly_base_strategy_key: str
    monthly_base_params: dict
    capacity_logic_params: dict


class ProposalLogicConfigResponse(ProposalLogicConfig):
    known_logics: list[str]


class SetProposalLogicConfigRequest(BaseModel):
    default_logic_key: str
    logic_params_by_key: dict[str, dict]
    disabled_logic_keys: list[str] = []


@router.get("/stock-logic/config", response_model=StockLogicConfigResponse)
def get_stock_logic_config_endpoint(
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Restituisce la configurazione attiva delle logiche stock V1 con registry delle strategy ammesse."""
    config = get_stock_logic_config(session)
    return StockLogicConfigResponse(
        **config.model_dump(),
        known_strategies=KNOWN_MONTHLY_BASE_STRATEGIES,
    )


@router.put("/stock-logic/config", response_model=StockLogicConfigResponse)
def put_stock_logic_config(
    body: SetStockLogicConfigRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Aggiorna la configurazione delle logiche stock V1.

    monthly_base_strategy_key deve essere in KNOWN_MONTHLY_BASE_STRATEGIES.
    capacity_logic_key e sempre '{}' e non e modificabile.
    422 se la strategy non e nel registry.
    """.format(CAPACITY_LOGIC_KEY)
    try:
        config = set_stock_logic_config(
            session,
            monthly_base_strategy_key=body.monthly_base_strategy_key,
            monthly_base_params=body.monthly_base_params,
            capacity_logic_params=body.capacity_logic_params,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return StockLogicConfigResponse(
        **config.model_dump(),
        known_strategies=KNOWN_MONTHLY_BASE_STRATEGIES,
    )


@router.get("/proposal-logic/config", response_model=ProposalLogicConfigResponse)
def get_proposal_logic_config_endpoint(
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    config = get_proposal_logic_config(session)
    return ProposalLogicConfigResponse(
        **config.model_dump(),
        known_logics=KNOWN_PROPOSAL_LOGICS,
    )


@router.put("/proposal-logic/config", response_model=ProposalLogicConfigResponse)
def put_proposal_logic_config(
    body: SetProposalLogicConfigRequest,
    _: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    try:
        config = set_proposal_logic_config(
            session,
            default_logic_key=body.default_logic_key,
            logic_params_by_key=body.logic_params_by_key,
            disabled_logic_keys=body.disabled_logic_keys,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return ProposalLogicConfigResponse(
        **config.model_dump(),
        known_logics=KNOWN_PROPOSAL_LOGICS,
    )
