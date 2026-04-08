"""
Sync unit `mag_reale` (TASK-V2-036).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2–§8):
- ENTITY_CODE:         "mag_reale"
- SOURCE_IDENTITY_KEY: "id_movimento"   (= ID_MAGREALE in MAG_REALE/EasyJob)
- ALIGNMENT_STRATEGY:  "append_only"
- CHANGE_ACQUISITION:  "cursor"
- DELETE_HANDLING:     "no_delete_handling"
- DEPENDENCIES:        []

Strategia incrementale:
  cursor = max(id_movimento) attualmente presente in sync_mag_reale (0 per bootstrap)
  La sync unit legge solo i movimenti con id_movimento > cursor.
  I record gia presenti non vengono ne aggiornati ne eliminati.

Normalizzazione tecnica codice_articolo: strip + uppercase (DL-ARCH-V2-016 §8).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.mag_reale.source import MagRealeSourceAdapter, _normalize_codice_articolo
from nssp_v2.sync.contract import RunMetadata


class MagRealeSyncUnit:
    """Sync unit per l'entita `mag_reale`.

    Responsabilita:
    - legge il cursore corrente (max id_movimento) dal mirror interno
    - acquisisce i nuovi movimenti dalla sorgente MAG_REALE (read-only)
    - inserisce i nuovi movimenti in sync_mag_reale (append only)
    - non aggiorna ne elimina i record gia presenti
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    Non calcola giacenze.
    """

    ENTITY_CODE = "mag_reale"
    SOURCE_IDENTITY_KEY = "id_movimento"
    ALIGNMENT_STRATEGY = "append_only"
    CHANGE_ACQUISITION = "cursor"
    DELETE_HANDLING = "no_delete_handling"
    DEPENDENCIES: list[str] = []

    def run(self, session: Session, source: MagRealeSourceAdapter) -> RunMetadata:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        meta = RunMetadata(
            run_id=run_id,
            entity_code=self.ENTITY_CODE,
            started_at=started_at,
        )

        try:
            # Legge il cursore: max id_movimento gia presente (0 per bootstrap vuoto)
            cursor_row = session.query(func.max(SyncMagReale.id_movimento)).scalar()
            cursor = cursor_row if cursor_row is not None else 0

            records = source.fetch_since(cursor)
            meta.rows_seen = len(records)
            now = datetime.now(timezone.utc)

            for rec in records:
                # Verifica idempotenza: salta se gia presente (non dovrebbe accadere con cursor)
                existing = session.query(SyncMagReale).filter(
                    SyncMagReale.id_movimento == rec.id_movimento
                ).first()
                if existing is not None:
                    continue

                obj = SyncMagReale(
                    id_movimento=rec.id_movimento,
                    codice_articolo=_normalize_codice_articolo(rec.codice_articolo),
                    quantita_caricata=rec.quantita_caricata,
                    quantita_scaricata=rec.quantita_scaricata,
                    causale_movimento_codice=rec.causale_movimento_codice,
                    data_movimento=rec.data_movimento,
                    synced_at=now,
                )
                session.add(obj)
                meta.rows_written += 1

            session.flush()
            meta.status = "success"
            meta.finished_at = datetime.now(timezone.utc)

        except Exception as exc:
            session.rollback()
            meta.status = "error"
            meta.error_message = str(exc)
            meta.finished_at = datetime.now(timezone.utc)
            self._persist_metadata(session, meta, success=False)
            session.commit()
            return meta

        self._persist_metadata(session, meta, success=True)
        session.commit()
        return meta

    def _persist_metadata(self, session: Session, meta: RunMetadata, *, success: bool) -> None:
        log = SyncRunLog(
            run_id=meta.run_id,
            entity_code=meta.entity_code,
            started_at=meta.started_at,
            finished_at=meta.finished_at,
            status=meta.status,
            rows_seen=meta.rows_seen,
            rows_written=meta.rows_written,
            rows_deleted=meta.rows_deleted,
            error_message=meta.error_message,
        )
        session.add(log)

        state = session.get(SyncEntityState, self.ENTITY_CODE)
        if state is None:
            state = SyncEntityState(entity_code=self.ENTITY_CODE)
            session.add(state)

        state.last_run_at = meta.started_at
        state.last_status = meta.status
        if success:
            state.last_success_at = meta.finished_at
            state.last_error = None
        else:
            state.last_error = meta.error_message
