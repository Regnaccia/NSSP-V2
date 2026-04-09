"""
Refresh semantico della surface articoli (DL-ARCH-V2-022, TASK-V2-054).

Incapsula la chain completa sync + rebuild per la surface articoli.
Gli endpoint non devono conoscere la lista degli step tecnici: chiamano
refresh_articoli() e restituiscono i risultati step-by-step.

Chain interna (8 step):
  Step 1 — sync articoli
  Step 2 — sync mag_reale
  Step 3 — sync righe_ordine_cliente
  Step 4 — sync produzioni_attive
  Step 5 — rebuild inventory_positions     (sempre)
  Step 6 — rebuild customer_set_aside      (skip se step 3 non OK)
  Step 7 — rebuild commitments             (skip se step 3 o step 4 non OK)
  Step 8 — rebuild availability            (skip se step 5, 6 o 7 non OK)

Dipendenze Easy:
  - tutte le sorgenti Easy sono read-only
  - nessuna scrittura verso Easy in alcun caso

Raises:
  SyncAlreadyRunningError: se una delle entita sync e gia in esecuzione
"""

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from nssp_v2.app.schemas.sync import EntityRunResult
from nssp_v2.app.services.sync_runner import SyncAlreadyRunningError, SyncRunner  # noqa: F401 — re-exported
from nssp_v2.core.availability.queries import rebuild_availability
from nssp_v2.core.commitments.queries import rebuild_commitments
from nssp_v2.core.customer_set_aside.queries import rebuild_customer_set_aside
from nssp_v2.core.inventory_positions.queries import rebuild_inventory_positions
from nssp_v2.sync.articoli.source import EasyArticoloSource
from nssp_v2.sync.mag_reale.source import EasyMagRealeSource
from nssp_v2.sync.produzioni_attive.source import EasyProduzioneAttivaSource
from nssp_v2.sync.righe_ordine_cliente.source import EasyRigheOrdineClienteSource

# Entita sync della surface articoli (ordine rispetta le dipendenze)
ARTICOLI_SYNC_ENTITIES = ["articoli", "mag_reale", "righe_ordine_cliente", "produzioni_attive"]


# ─── Helper: step saltato ────────────────────────────────────────────────────

def _skipped_result(entity_code: str) -> EntityRunResult:
    """Produce un EntityRunResult con status='skipped' per uno step saltato per dipendenza."""
    now = datetime.now(timezone.utc)
    return EntityRunResult(
        entity_code=entity_code,
        status="skipped",
        run_id=None,
        rows_seen=0,
        rows_written=0,
        rows_deleted=0,
        error_message=None,
        started_at=now,
        finished_at=now,
    )


# ─── Helper: wrapper generico per rebuild Core ────────────────────────────────

def _run_rebuild(
    entity_code: str,
    rebuild_fn: Callable[[Session], int],
    session: Session,
) -> EntityRunResult:
    """Esegue un rebuild Core e wrappa l'esito in un EntityRunResult.

    Strategia:
    - chiama rebuild_fn(session) che restituisce il numero di righe create
    - fa commit in caso di successo
    - fa rollback e cattura l'errore in caso di eccezione

    Non fa commit in caso di eccezione: il chiamante puo decidere di continuare
    con la sessione ancora valida.
    """
    started_at = datetime.now(timezone.utc)
    try:
        n = rebuild_fn(session)
        session.commit()
        return EntityRunResult(
            entity_code=entity_code,
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
            entity_code=entity_code,
            status="error",
            run_id=None,
            rows_seen=0,
            rows_written=0,
            rows_deleted=0,
            error_message=str(exc),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )


# ─── Helper nominati per singolo rebuild (testabili individualmente) ─────────

def _run_inventory_rebuild(session: Session) -> EntityRunResult:
    """Esegue il rebuild completo di core_inventory_positions."""
    return _run_rebuild("inventory_positions", rebuild_inventory_positions, session)


def _run_set_aside_rebuild(session: Session) -> EntityRunResult:
    """Esegue il rebuild completo di core_customer_set_aside."""
    return _run_rebuild("customer_set_aside", rebuild_customer_set_aside, session)


def _run_commitments_rebuild(session: Session) -> EntityRunResult:
    """Esegue il rebuild completo di core_commitments."""
    return _run_rebuild("commitments", rebuild_commitments, session)


def _run_availability_rebuild(session: Session) -> EntityRunResult:
    """Esegue il rebuild completo di core_availability."""
    return _run_rebuild("availability", rebuild_availability, session)


# ─── Refresh semantico surface articoli ──────────────────────────────────────

def refresh_articoli(session: Session, conn_string: str) -> list[EntityRunResult]:
    """Esegue il refresh completo della surface articoli e restituisce i risultati step-by-step.

    Chain interna (8 step):
      Step 1 — sync articoli
      Step 2 — sync mag_reale
      Step 3 — sync righe_ordine_cliente
      Step 4 — sync produzioni_attive
      Step 5 — rebuild inventory_positions     (sempre)
      Step 6 — rebuild customer_set_aside      (skip se step 3 non OK)
      Step 7 — rebuild commitments             (skip se step 3 o step 4 non OK)
      Step 8 — rebuild availability            (skip se step 5, 6 o 7 non OK)

    Args:
        session: sessione SQLAlchemy attiva
        conn_string: connection string Easy (read-only)

    Returns:
        lista di 8 EntityRunResult, uno per ogni step

    Raises:
        SyncAlreadyRunningError: se una delle entita sync e gia in esecuzione
    """
    sources = {
        "articoli": EasyArticoloSource(conn_string),
        "mag_reale": EasyMagRealeSource(conn_string),
        "righe_ordine_cliente": EasyRigheOrdineClienteSource(conn_string),
        "produzioni_attive": EasyProduzioneAttivaSource(conn_string),
    }

    # Step 1–4: sync Easy
    runner = SyncRunner()
    results = runner.run_surface(session, ARTICOLI_SYNC_ENTITIES, sources)

    # Prerequisiti per i rebuild condizionali
    sync_status = {r.entity_code: r.status for r in results}
    righe_ok = sync_status.get("righe_ordine_cliente") == "success"
    produzioni_ok = sync_status.get("produzioni_attive") == "success"

    # Step 5: rebuild inventory_positions — sempre (dipende solo da mag_reale)
    inv_result = _run_inventory_rebuild(session)
    results.append(inv_result)

    # Step 6: rebuild customer_set_aside — solo se righe_ordine_cliente e OK
    if righe_ok:
        set_aside_result = _run_set_aside_rebuild(session)
    else:
        set_aside_result = _skipped_result("customer_set_aside")
    results.append(set_aside_result)

    # Step 7: rebuild commitments — solo se righe_ordine_cliente E produzioni_attive sono OK
    if righe_ok and produzioni_ok:
        commitments_result = _run_commitments_rebuild(session)
    else:
        commitments_result = _skipped_result("commitments")
    results.append(commitments_result)

    # Step 8: rebuild availability — solo se tutti e tre i fact precedenti sono OK
    if (
        inv_result.status == "success"
        and set_aside_result.status == "success"
        and commitments_result.status == "success"
    ):
        results.append(_run_availability_rebuild(session))
    else:
        results.append(_skipped_result("availability"))

    return results
