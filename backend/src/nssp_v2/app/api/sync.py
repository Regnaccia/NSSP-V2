"""
Router sync on demand (DL-ARCH-V2-011, DL-ARCH-V2-022).

Endpoint:
  POST /api/sync/surface/logistica    — trigger refresh logistica (clienti + destinazioni)
  GET  /api/sync/freshness/logistica  — stato freschezza entita surface logistica
  POST /api/sync/surface/produzione   — trigger refresh articoli (refresh semantico — 8 step)
  GET  /api/sync/freshness/produzione — stato freschezza entita surface produzione
  POST /api/sync/surface/produzioni   — trigger sync produzioni_attive + produzioni_storiche
  GET  /api/sync/freshness/produzioni — stato freschezza entita surface produzioni
  POST /api/sync/surface/magazzino    — trigger sync mag_reale (incrementale)
  GET  /api/sync/freshness/magazzino  — stato freschezza entita surface magazzino

Pattern refresh semantici (DL-ARCH-V2-022):
  Gli endpoint non orchestrano direttamente la lista degli step tecnici.
  Per la surface articoli, la chain reale (8 step, dipendenze condizionali) vive
  in nssp_v2.app.services.refresh_articoli.refresh_articoli().

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
from nssp_v2.app.services.refresh_articoli import (
    ARTICOLI_SYNC_ENTITIES,
    SyncAlreadyRunningError,
    refresh_articoli,
)
from nssp_v2.app.services.sync_runner import SyncRunner
from nssp_v2.shared.config import get_settings
from nssp_v2.shared.db import get_session
from nssp_v2.sync.clienti.source import EasyClienteSource
from nssp_v2.sync.destinazioni.source import EasyDestinazioneSource
from nssp_v2.sync.mag_reale.source import EasyMagRealeSource
from nssp_v2.sync.produzioni_attive.source import EasyProduzioneAttivaSource
from nssp_v2.sync.produzioni_storiche.source import EasyProduzioneStoricaSource
from nssp_v2.sync.models import SyncEntityState

router = APIRouter(prefix="/sync", tags=["sync"])

# Ordine di esecuzione surface logistica (rispetta dipendenze dichiarate)
_LOGISTICA_ENTITIES = ["clienti", "destinazioni"]
# Entita surface produzioni (attive + storiche: nessuna dipendenza tra loro)
_PRODUZIONI_ENTITIES = ["produzioni_attive", "produzioni_storiche"]
# Entita surface magazzino (mag_reale: nessuna dipendenza esterna)
_MAGAZZINO_ENTITIES = ["mag_reale"]
_STALENESS_MINUTES = 60  # default; futura configurazione per entita


# ─── Helper freshness ─────────────────────────────────────────────────────────

def _build_freshness(
    session: Session,
    entity_codes: list[str],
    threshold_seconds: float,
) -> FreshnessResponse:
    now = datetime.now(timezone.utc)
    entity_freshness: list[EntityFreshness] = []

    for entity_code in entity_codes:
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
    return FreshnessResponse(entities=entity_freshness, surface_ready=surface_ready)


# ─── Trigger sync on demand — logistica ──────────────────────────────────────

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


# ─── Freshness state — logistica ──────────────────────────────────────────────

@router.get(
    "/freshness/logistica",
    response_model=FreshnessResponse,
    summary="Stato freschezza entita surface logistica",
)
def freshness_logistica(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Restituisce lo stato di freschezza di clienti e destinazioni."""
    return _build_freshness(session, _LOGISTICA_ENTITIES, _STALENESS_MINUTES * 60)


# ─── Trigger refresh semantico — produzione (surface articoli) ────────────────

@router.post(
    "/surface/produzione",
    response_model=SyncSurfaceResponse,
    summary="Trigger refresh semantico surface articoli",
)
def trigger_produzione(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Esegue il refresh semantico della surface articoli (DL-ARCH-V2-022).

    La chain tecnica interna (8 step, con dipendenze condizionali) e incapsulata
    in refresh_articoli() e non e visibile da questo endpoint.

    Controlli backend:
    - Easy connection string deve essere configurata
    - Nessuna sync concorrente sul perimetro articoli
    """
    settings = get_settings()

    if not settings.easy_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Easy non configurato: EASY_CONNECTION_STRING mancante in .env",
        )

    try:
        results = refresh_articoli(session, settings.easy_connection_string)
    except SyncAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sync gia in esecuzione: {', '.join(sorted(exc.running_entities))}",
        )

    return SyncSurfaceResponse(
        triggered_at=datetime.now(timezone.utc),
        results=results,
    )


# ─── Freshness state — produzione ─────────────────────────────────────────────

@router.get(
    "/freshness/produzione",
    response_model=FreshnessResponse,
    summary="Stato freschezza entita surface produzione",
)
def freshness_produzione(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Restituisce lo stato di freschezza degli articoli e dei loro prerequisiti."""
    return _build_freshness(session, ARTICOLI_SYNC_ENTITIES, _STALENESS_MINUTES * 60)


# ─── Trigger sync on demand — produzioni ─────────────────────────────────────

@router.post(
    "/surface/produzioni",
    response_model=SyncSurfaceResponse,
    summary="Trigger sync on demand: produzioni_attive + produzioni_storiche",
)
def trigger_produzioni(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Esegue la sync on demand di produzioni_attive e produzioni_storiche.

    Controlli backend:
    - Easy connection string deve essere configurata
    - Nessuna sync concorrente sullo stesso perimetro
    - Entita eseguite in ordine: produzioni_attive, produzioni_storiche (nessuna dipendenza tra loro)
    """
    settings = get_settings()

    if not settings.easy_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Easy non configurato: EASY_CONNECTION_STRING mancante in .env",
        )

    sources = {
        "produzioni_attive": EasyProduzioneAttivaSource(settings.easy_connection_string),
        "produzioni_storiche": EasyProduzioneStoricaSource(settings.easy_connection_string),
    }

    runner = SyncRunner()
    try:
        results = runner.run_surface(session, _PRODUZIONI_ENTITIES, sources)
    except SyncAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sync gia in esecuzione: {', '.join(sorted(exc.running_entities))}",
        )

    return SyncSurfaceResponse(
        triggered_at=datetime.now(timezone.utc),
        results=results,
    )


# ─── Freshness state — produzioni ─────────────────────────────────────────────

@router.get(
    "/freshness/produzioni",
    response_model=FreshnessResponse,
    summary="Stato freschezza entita surface produzioni",
)
def freshness_produzioni(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Restituisce lo stato di freschezza di produzioni_attive e produzioni_storiche."""
    return _build_freshness(session, _PRODUZIONI_ENTITIES, _STALENESS_MINUTES * 60)


# ─── Trigger sync on demand — magazzino ──────────────────────────────────────

@router.post(
    "/surface/magazzino",
    response_model=SyncSurfaceResponse,
    summary="Trigger sync on demand: mag_reale (incrementale)",
)
def trigger_magazzino(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Esegue la sync on demand incrementale dei movimenti di magazzino.

    Strategia: append_only + cursor — acquisisce solo i nuovi movimenti
    con ID_MAGREALE > max(id_movimento) gia presente nel mirror.
    Per il primo run (bootstrap) acquisisce tutti i movimenti.

    Controlli backend:
    - Easy connection string deve essere configurata
    - Nessuna sync concorrente sul perimetro magazzino
    """
    settings = get_settings()

    if not settings.easy_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Easy non configurato: EASY_CONNECTION_STRING mancante in .env",
        )

    sources = {
        "mag_reale": EasyMagRealeSource(settings.easy_connection_string),
    }

    runner = SyncRunner()
    try:
        results = runner.run_surface(session, _MAGAZZINO_ENTITIES, sources)
    except SyncAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sync gia in esecuzione: {', '.join(sorted(exc.running_entities))}",
        )

    return SyncSurfaceResponse(
        triggered_at=datetime.now(timezone.utc),
        results=results,
    )


# ─── Freshness state — magazzino ─────────────────────────────────────────────

@router.get(
    "/freshness/magazzino",
    response_model=FreshnessResponse,
    summary="Stato freschezza entita surface magazzino",
)
def freshness_magazzino(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Restituisce lo stato di freschezza della surface magazzino (mag_reale)."""
    return _build_freshness(session, _MAGAZZINO_ENTITIES, _STALENESS_MINUTES * 60)
