"""
Schemi Pydantic per il contratto sync on demand (DL-ARCH-V2-011).
"""

from datetime import datetime

from pydantic import BaseModel


class EntityRunResult(BaseModel):
    """Esito di una singola sync unit nell'ambito di un trigger on demand."""

    entity_code: str
    status: str               # "success" | "error" | "skipped"
    run_id: str | None
    rows_seen: int
    rows_written: int
    rows_deleted: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class SyncSurfaceResponse(BaseModel):
    """Risposta a un trigger sync on demand di surface."""

    triggered_at: datetime
    results: list[EntityRunResult]


class EntityFreshness(BaseModel):
    """Stato di freschezza di una singola entita (DL-ARCH-V2-008 §5)."""

    entity_code: str
    last_success_at: datetime | None
    last_status: str | None
    is_stale: bool              # True se mai sincronizzata o oltre soglia


class FreshnessResponse(BaseModel):
    """Stato di freschezza delle entita della surface logistica."""

    entities: list[EntityFreshness]
    surface_ready: bool         # True se tutte le entita hanno almeno una sync di successo
