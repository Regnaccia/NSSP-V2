"""
Router sync on demand (DL-ARCH-V2-011).

Endpoint:
  POST /api/sync/surface/logistica   — trigger sync clienti + destinazioni in ordine
  GET  /api/sync/freshness/logistica — stato freschezza entita della surface logistica

Controlli obbligatori (DL-ARCH-V2-011 §4):
- autenticazione Bearer
- Easy connection string configurata (503 se assente)
- prevenzione esecuzioni concorrenti (409 se gia in corso)
- rispetto dipendenze (clienti prima di destinazioni — ordine hardcoded)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nssp_v2.app.deps.auth import get_current_user
from nssp_v2.app.schemas.sync import (
    EntityFreshness,
    FreshnessResponse,
    SyncSurfaceResponse,
)
from nssp_v2.app.services.sync_runner import (
    SyncAlreadyRunningError,
    SyncRunner,
)
from nssp_v2.shared.config import get_settings
from nssp_v2.shared.db import get_session
from nssp_v2.sync.clienti.source import EasyClienteSource
from nssp_v2.sync.destinazioni.source import EasyDestinazioneSource
from nssp_v2.sync.models import SyncEntityState

router = APIRouter(prefix="/sync", tags=["sync"])

# Ordine di esecuzione della surface logistica (rispetta dipendenze dichiarate)
_LOGISTICA_ENTITIES = ["clienti", "destinazioni"]
_STALENESS_MINUTES = 60  # default; futura configurazione per entita


# ─── Trigger sync on demand ───────────────────────────────────────────────────

@router.post(
    "/surface/logistica",
    response_model=SyncSurfaceResponse,
    summary="Trigger sync on demand: clienti + destinazioni",
)
def trigger_logistica(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Esegue la sync on demand di clienti e destinazioni in ordine di dipendenza.

    Controlli backend:
    - Easy connection string deve essere configurata
    - Nessuna sync concorrente sullo stesso perimetro
    - Ordine di esecuzione rispetta la dipendenza destinazioni→clienti

    Restituisce i RunMetadata di ogni sync unit eseguita.
    """
    settings = get_settings()

    if not settings.easy_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Easy non configurato: EASY_CONNECTION_STRING mancante in .env",
        )

    sources = {
        "clienti": EasyClienteSource(settings.easy_connection_string),
        "destinazioni": EasyDestinazioneSource(settings.easy_connection_string),
    }

    runner = SyncRunner()
    try:
        results = runner.run_surface(session, _LOGISTICA_ENTITIES, sources)
    except SyncAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sync gia in esecuzione: {', '.join(sorted(exc.running_entities))}",
        )

    return SyncSurfaceResponse(
        triggered_at=datetime.now(timezone.utc),
        results=results,
    )


# ─── Freshness state ──────────────────────────────────────────────────────────

@router.get(
    "/freshness/logistica",
    response_model=FreshnessResponse,
    summary="Stato freschezza entita surface logistica",
)
def freshness_logistica(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Restituisce lo stato di freschezza di clienti e destinazioni.

    `is_stale = True` se:
    - non esiste ancora una sync completata con successo
    - oppure l'ultima sync di successo e piu vecchia di staleness_threshold_minutes
    """
    now = datetime.now(timezone.utc)
    threshold_seconds = _STALENESS_MINUTES * 60

    entity_freshness: list[EntityFreshness] = []
    for entity_code in _LOGISTICA_ENTITIES:
        state = session.get(SyncEntityState, entity_code)

        if state is None or state.last_success_at is None:
            is_stale = True
            last_success_at = None
            last_status = state.last_status if state else None
        else:
            last_success_at = state.last_success_at
            last_status = state.last_status
            age_seconds = (now - last_success_at).total_seconds()
            is_stale = age_seconds > threshold_seconds

        entity_freshness.append(EntityFreshness(
            entity_code=entity_code,
            last_success_at=last_success_at,
            last_status=last_status,
            is_stale=is_stale,
        ))

    surface_ready = all(not e.is_stale for e in entity_freshness)

    return FreshnessResponse(
        entities=entity_freshness,
        surface_ready=surface_ready,
    )
