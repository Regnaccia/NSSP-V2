"""
Router sync on demand (DL-ARCH-V2-011).

Endpoint:
  POST /api/sync/surface/logistica    — trigger sync clienti + destinazioni in ordine
  GET  /api/sync/freshness/logistica  — stato freschezza entita della surface logistica
  POST /api/sync/surface/produzione   — trigger sync articoli + mag_reale + rebuild inventory_positions
  GET  /api/sync/freshness/produzione — stato freschezza entita della surface produzione (articoli + mag_reale)
  POST /api/sync/surface/produzioni   — trigger sync produzioni_attive + produzioni_storiche
  GET  /api/sync/freshness/produzioni — stato freschezza entita della surface produzioni
  POST /api/sync/surface/magazzino    — trigger sync mag_reale (incrementale)
  GET  /api/sync/freshness/magazzino  — stato freschezza entita della surface magazzino

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
    EntityRunResult,
    FreshnessResponse,
    SyncSurfaceResponse,
)
from nssp_v2.app.services.sync_runner import (
    SyncAlreadyRunningError,
    SyncRunner,
)
from nssp_v2.core.inventory_positions.queries import rebuild_inventory_positions
from nssp_v2.shared.config import get_settings
from nssp_v2.shared.db import get_session
from nssp_v2.sync.articoli.source import EasyArticoloSource
from nssp_v2.sync.clienti.source import EasyClienteSource
from nssp_v2.sync.destinazioni.source import EasyDestinazioneSource
from nssp_v2.sync.mag_reale.source import EasyMagRealeSource
from nssp_v2.sync.produzioni_attive.source import EasyProduzioneAttivaSource
from nssp_v2.sync.produzioni_storiche.source import EasyProduzioneStoricaSource
from nssp_v2.sync.models import SyncEntityState

router = APIRouter(prefix="/sync", tags=["sync"])

# Ordine di esecuzione surface logistica (rispetta dipendenze dichiarate)
_LOGISTICA_ENTITIES = ["clienti", "destinazioni"]


# ─── Helper: rebuild inventory_positions ─────────────────────────────────────

def _run_inventory_rebuild(session: Session) -> EntityRunResult:
    """Esegue il rebuild completo di core_inventory_positions e restituisce un EntityRunResult."""
    started_at = datetime.now(timezone.utc)
    try:
        n = rebuild_inventory_positions(session)
        session.commit()
        return EntityRunResult(
            entity_code="inventory_positions",
            status="success",
            run_id=None,
            rows_seen=n,
            rows_written=n,
            rows_deleted=0,
            error_message=None,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        session.rollback()
        return EntityRunResult(
            entity_code="inventory_positions",
            status="error",
            run_id=None,
            rows_seen=0,
            rows_written=0,
            rows_deleted=0,
            error_message=str(exc),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
# Entita surface produzione: articoli + mag_reale (il rebuild inventory_positions segue in sequenza)
_PRODUZIONE_ENTITIES = ["articoli", "mag_reale"]
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
    """Restituisce lo stato di freschezza di clienti e destinazioni."""
    return _build_freshness(session, _LOGISTICA_ENTITIES, _STALENESS_MINUTES * 60)


# ─── Trigger sync on demand — produzione ─────────────────────────────────────

@router.post(
    "/surface/produzione",
    response_model=SyncSurfaceResponse,
    summary="Trigger sync on demand: articoli",
)
def trigger_produzione(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Esegue la sync on demand sequenziale: articoli → mag_reale → rebuild inventory_positions.

    Controlli backend:
    - Easy connection string deve essere configurata
    - Nessuna sync concorrente sul perimetro
    - Il rebuild inventory_positions avviene dopo la sync, sempre (da stato corrente del mirror)
    """
    settings = get_settings()

    if not settings.easy_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Easy non configurato: EASY_CONNECTION_STRING mancante in .env",
        )

    sources = {
        "articoli": EasyArticoloSource(settings.easy_connection_string),
        "mag_reale": EasyMagRealeSource(settings.easy_connection_string),
    }

    runner = SyncRunner()
    try:
        results = runner.run_surface(session, _PRODUZIONE_ENTITIES, sources)
    except SyncAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sync gia in esecuzione: {', '.join(sorted(exc.running_entities))}",
        )

    # Step finale: rebuild deterministic di inventory_positions dal mirror aggiornato
    results.append(_run_inventory_rebuild(session))

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
    """Restituisce lo stato di freschezza degli articoli."""
    return _build_freshness(session, _PRODUZIONE_ENTITIES, _STALENESS_MINUTES * 60)


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
