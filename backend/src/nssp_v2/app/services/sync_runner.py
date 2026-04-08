"""
Orchestratore sync on demand (DL-ARCH-V2-011).

Responsabilita:
- rispetto delle dipendenze tra entita (DL-ARCH-V2-011 §4)
- prevenzione di esecuzioni concorrenti duplicate (DL-ARCH-V2-011 §4)
- delegazione dell'esecuzione alle sync unit esistenti
- produzione di risultati coerenti con il modello RunMetadata

Le sorgenti (source adapter) sono iniettate dall'invocante.
Questo consente il testing con FakeSource senza modificare la logica di orchestrazione.

Concorrenza: lock in-memory thread-safe.
Adeguato per deployment single-process.
"""

import threading
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from nssp_v2.app.schemas.sync import EntityRunResult
from nssp_v2.sync.articoli.unit import ArticoloSyncUnit
from nssp_v2.sync.clienti.unit import ClienteSyncUnit
from nssp_v2.sync.destinazioni.unit import DestinazioneSyncUnit
from nssp_v2.sync.produzioni_attive.unit import ProduzioneAttivaSyncUnit
from nssp_v2.sync.produzioni_storiche.unit import ProduzioneStoricaSyncUnit

# ─── Mappa entity_code → sync unit class ──────────────────────────────────────

_UNIT_MAP = {
    "clienti": ClienteSyncUnit,
    "destinazioni": DestinazioneSyncUnit,
    "articoli": ArticoloSyncUnit,
    "produzioni_attive": ProduzioneAttivaSyncUnit,
    "produzioni_storiche": ProduzioneStoricaSyncUnit,
}

# ─── Concurrency guard ────────────────────────────────────────────────────────

_RUNNING: set[str] = set()
_LOCK = threading.Lock()


def _try_acquire(entities: list[str]) -> bool:
    """Tenta di acquisire il lock per tutte le entita richieste.

    Restituisce True se acquisito, False se almeno una entita e gia in esecuzione.
    Operazione atomica: acquisisce tutto o niente.
    """
    with _LOCK:
        if any(e in _RUNNING for e in entities):
            return False
        _RUNNING.update(entities)
        return True


def _release(entities: list[str]) -> None:
    """Rilascia il lock per le entita specificate."""
    with _LOCK:
        _RUNNING.difference_update(entities)


def get_running_entities() -> set[str]:
    """Restituisce una copia delle entita attualmente in esecuzione."""
    with _LOCK:
        return set(_RUNNING)


# ─── Runner ───────────────────────────────────────────────────────────────────

class SyncRunner:
    """Orchestratore sync on demand.

    Uso:
        runner = SyncRunner()
        results = runner.run_surface(session, ["clienti", "destinazioni"], sources)
    """

    def run_surface(
        self,
        session: Session,
        ordered_entities: list[str],
        sources: dict[str, Any],
    ) -> list[EntityRunResult]:
        """Esegue la sync delle entita in ordine, rispettando le dipendenze.

        Args:
            session: sessione SQLAlchemy
            ordered_entities: lista entita in ordine di esecuzione (dipendenze prima)
            sources: mappa entity_code -> source adapter

        Returns:
            lista risultati per ogni entita, nello stesso ordine

        Raises:
            SyncAlreadyRunningError: se almeno una entita e gia in esecuzione
            SyncEntityUnknownError: se un entity_code non e registrato
        """
        # Validazione entita
        for entity_code in ordered_entities:
            if entity_code not in _UNIT_MAP:
                raise SyncEntityUnknownError(entity_code)

        # Acquisizione concorrenza
        if not _try_acquire(ordered_entities):
            running = get_running_entities() & set(ordered_entities)
            raise SyncAlreadyRunningError(running)

        results: list[EntityRunResult] = []
        try:
            for entity_code in ordered_entities:
                source = sources.get(entity_code)
                if source is None:
                    # Sorgente mancante: skip con errore
                    now = datetime.now(timezone.utc)
                    results.append(EntityRunResult(
                        entity_code=entity_code,
                        status="error",
                        run_id=None,
                        rows_seen=0,
                        rows_written=0,
                        rows_deleted=0,
                        error_message=f"Sorgente non disponibile per '{entity_code}'",
                        started_at=now,
                        finished_at=now,
                    ))
                    continue

                unit_cls = _UNIT_MAP[entity_code]
                unit = unit_cls()
                meta = unit.run(session, source)

                results.append(EntityRunResult(
                    entity_code=entity_code,
                    status=meta.status,
                    run_id=meta.run_id,
                    rows_seen=meta.rows_seen,
                    rows_written=meta.rows_written,
                    rows_deleted=meta.rows_deleted,
                    error_message=meta.error_message,
                    started_at=meta.started_at,
                    finished_at=meta.finished_at,
                ))

        finally:
            _release(ordered_entities)

        return results


# ─── Eccezioni ────────────────────────────────────────────────────────────────

class SyncAlreadyRunningError(Exception):
    """Una o piu entita richieste sono gia in esecuzione."""

    def __init__(self, running_entities: set[str]) -> None:
        self.running_entities = running_entities
        super().__init__(f"Sync gia in esecuzione per: {', '.join(sorted(running_entities))}")


class SyncEntityUnknownError(Exception):
    """Entity code non registrato nel runner."""

    def __init__(self, entity_code: str) -> None:
        self.entity_code = entity_code
        super().__init__(f"Entity code non registrato: '{entity_code}'")
