"""
Schemi Pydantic per la surface admin — access management.

Perimetro: lista utenti, creazione, toggle attivo, gestione ruoli.
"""

from pydantic import BaseModel, field_validator

from nssp_v2.app.schemas.auth import Surface

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
