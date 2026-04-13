"""
Schemi Pydantic per la surface admin — access management e warning config.

Perimetro: lista utenti, creazione, toggle attivo, gestione ruoli,
           configurazione visibilita warning (TASK-V2-077, DL-ARCH-V2-029).
"""

from pydantic import BaseModel, field_validator

from nssp_v2.app.schemas.auth import Surface
from nssp_v2.core.warnings.config import KNOWN_WARNING_TYPES

# Catalogo ruoli ammessi nel primo slice V2 (DL-ARCH-V2-006 §4)
ALLOWED_ROLES = {"admin", "produzione", "logistica", "magazzino"}


class UserListItem(BaseModel):
    """Rappresentazione utente nella lista admin."""

    id: int
    username: str
    attivo: bool
    roles: list[str]
    available_surfaces: list[Surface]


class CreateUserRequest(BaseModel):
    username: str
    password: str
    roles: list[str] = []

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: list[str]) -> list[str]:
        invalid = set(v) - ALLOWED_ROLES
        if invalid:
            raise ValueError(f"Ruoli non ammessi: {invalid}")
        return list(set(v))  # deduplica


class SetActiveRequest(BaseModel):
    attivo: bool


class SetRolesRequest(BaseModel):
    roles: list[str]

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: list[str]) -> list[str]:
        invalid = set(v) - ALLOWED_ROLES
        if invalid:
            raise ValueError(f"Ruoli non ammessi: {invalid}")
        return list(set(v))


# ─── Warning config (TASK-V2-077, TASK-V2-081) ───────────────────────────────

class UpdateWarningConfigRequest(BaseModel):
    """Richiesta di aggiornamento visibilita per tipo warning — per area/reparto."""

    visible_to_areas: list[str]

    @field_validator("visible_to_areas")
    @classmethod
    def deduplicate(cls, v: list[str]) -> list[str]:
        # Deduplica mantenendo l'ordine
        seen: set[str] = set()
        return [x for x in v if not (x in seen or seen.add(x))]  # type: ignore[arg-type]


class UpdateWarningTypeRequest(BaseModel):
    """Validazione del warning_type nel path — tipi ammessi (TASK-V2-077)."""

    warning_type: str

    @field_validator("warning_type")
    @classmethod
    def validate_warning_type(cls, v: str) -> str:
        if v not in KNOWN_WARNING_TYPES:
            raise ValueError(f"Tipo warning non ammesso: {v}. Ammessi: {KNOWN_WARNING_TYPES}")
        return v
