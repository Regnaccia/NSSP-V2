"""
Sync unit `clienti` — prima sync unit della V2 (DL-ARCH-V2-009).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2–§8):
- ENTITY_CODE:          "clienti"
- SOURCE_IDENTITY_KEY:  "codice_cli"  (= CLI_COD in ANACLI/EasyJob)
- ALIGNMENT_STRATEGY:   "upsert"
- CHANGE_ACQUISITION:   "full_scan"
- DELETE_HANDLING:      "mark_inactive"
- DEPENDENCIES:         []  (nessuna: clienti non dipende da altre sync unit)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.sync.clienti.models import SyncCliente
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.clienti.source import ClienteSourceAdapter
from nssp_v2.sync.contract import RunMetadata


class ClienteSyncUnit:
    """Sync unit per l'entita `clienti`.

    Responsabilita:
    - acquisisce clienti dalla sorgente (read-only)
    - allinea il target interno sync_clienti via upsert
    - marca inattivi i clienti non piu presenti in sorgente
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    """

    # ─── Contratto obbligatorio DL-ARCH-V2-009 ───────────────────────────────

    ENTITY_CODE = "clienti"
    SOURCE_IDENTITY_KEY = "codice_cli"
    ALIGNMENT_STRATEGY = "upsert"
    CHANGE_ACQUISITION = "full_scan"
    DELETE_HANDLING = "mark_inactive"
    DEPENDENCIES: list[str] = []

    # ─── Esecuzione ──────────────────────────────────────────────────────────

    def run(self, session: Session, source: ClienteSourceAdapter) -> RunMetadata:
        """Esegue la sync `clienti`.

        Idempotente: piu esecuzioni con la stessa sorgente producono lo stesso stato.

        Args:
            session:  sessione SQLAlchemy aperta dall'invocante
            source:   adapter read-only per la sorgente clienti

        Returns:
            RunMetadata con l'esito dell'esecuzione
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        meta = RunMetadata(
            run_id=run_id,
            entity_code=self.ENTITY_CODE,
            started_at=started_at,
        )

        try:
            records = source.fetch_all()
            meta.rows_seen = len(records)
            now = datetime.now(timezone.utc)

            # Carica i codici gia presenti nel target interno
            existing: dict[str, SyncCliente] = {
                obj.codice_cli: obj
                for obj in session.query(SyncCliente).all()
            }

            seen_codes: set[str] = set()

            for rec in records:
                seen_codes.add(rec.codice_cli)
                obj = existing.get(rec.codice_cli)
                if obj is None:
                    obj = SyncCliente(
                        codice_cli=rec.codice_cli,
                        ragione_sociale=rec.ragione_sociale,
                        attivo=True,
                        synced_at=now,
                    )
                    session.add(obj)
                else:
                    obj.ragione_sociale = rec.ragione_sociale
                    obj.attivo = True
                    obj.synced_at = now
                meta.rows_written += 1

            # Delete handling: mark_inactive per codici non piu presenti in sorgente
            for codice, obj in existing.items():
                if codice not in seen_codes and obj.attivo:
                    obj.attivo = False
                    obj.synced_at = now
                    meta.rows_deleted += 1

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

    # ─── Persistenza metadati ─────────────────────────────────────────────────

    def _persist_metadata(
        self,
        session: Session,
        meta: RunMetadata,
        *,
        success: bool,
    ) -> None:
        """Persiste run log e aggiorna freshness anchor."""
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
