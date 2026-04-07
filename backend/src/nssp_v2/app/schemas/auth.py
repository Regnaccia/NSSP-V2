"""
Schemi Pydantic per autenticazione e sessione.

Contratto pubblico del layer app verso il frontend browser (DL-ARCH-V2-004).
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class Surface(BaseModel):
    """Superficie applicativa disponibile per un ruolo."""

    role: str
    path: str
    label: str


class LoginResponse(BaseModel):
    """Risposta al login: token + profilo sessione completo."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    roles: list[str]
    access_mode: str
    available_surfaces: list[Surface]


class SessionResponse(BaseModel):
    """Profilo sessione corrente (GET /auth/me)."""

    user_id: int
    username: str
    roles: list[str]
    access_mode: str
    available_surfaces: list[Surface]
