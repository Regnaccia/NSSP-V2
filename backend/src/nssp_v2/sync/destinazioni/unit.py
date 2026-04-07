"""
Sync unit `destinazioni` (DL-ARCH-V2-009).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2–§8):
- ENTITY_CODE:          "destinazioni"
- SOURCE_IDENTITY_KEY:  "codice_destinazione"  (= PDES_COD in POT_DESTDIV/EasyJob)
- ALIGNMENT_STRATEGY:   "upsert"
- CHANGE_ACQUISITION:   "full_scan"
- DELETE_HANDLING:      "mark_inactive"
- DEPENDENCIES:         ["clienti"]  (DL-ARCH-V2-009 §8, EASY_DESTINAZIONI.md §Dependencies)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.sync.destinazioni.models import SyncDestinazione
from nssp_v2.sync.destinazioni.source import DestinazioneSourceAdapter
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.contract import RunMetadata


class DestinazioneSyncUnit:
    """Sync unit per l'entita `destinazioni`.

    Responsabilita:
    - acquisisce destinazioni dalla sorgente (read-only)
    - allinea il target interno sync_destinazioni via upsert
    - marca inattive le destinazioni non piu presenti in sorgente
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    Dipende da `clienti` (deve essere sincronizzata dopo).
    """

    # ─── Contratto obbligatorio DL-ARCH-V2-009 ───────────────────────────────

    ENTITY_CODE = "destinazioni"
    SOURCE_IDENTITY_KEY = "codice_destinazione"
    ALIGNMENT_STRATEGY = "upsert"
    CHANGE_ACQUISITION = "full_scan"
    DELETE_HANDLING = "mark_inactive"
    DEPENDENCIES: list[str] = ["clienti"]

    # ─── Esecuzione ──────────────────────────────────────────────────────────

    def run(self, session: Session, source: DestinazioneSourceAdapter) -> RunMetadata:
        """Esegue la sync `destinazioni`.

        Idempotente: piu esecuzioni con la stessa sorgente producono lo stesso stato.

        Args:
            session:  sessione SQLAlchemy aperta dall'invocante
            source:   adapter read-only per la sorgente destinazioni

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

            existing: dict[str, SyncDestinazione] = {
                obj.codice_destinazione: obj
                for obj in session.query(SyncDestinazione).all()
            }

            seen_codes: set[str] = set()

            for rec in records:
                seen_codes.add(rec.codice_destinazione)
                obj = existing.get(rec.codice_destinazione)
                if obj is None:
                    obj = SyncDestinazione(
                        codice_destinazione=rec.codice_destinazione,
                        codice_cli=rec.codice_cli,
                        numero_progressivo_cliente=rec.numero_progressivo_cliente,
                        indirizzo=rec.indirizzo,
                        nazione_codice=rec.nazione_codice,
                        citta=rec.citta,
                        provincia=rec.provincia,
                        telefono_1=rec.telefono_1,
                        attivo=True,
                        synced_at=now,
                    )
                    session.add(obj)
                else:
                    obj.codice_cli = rec.codice_cli
                    obj.numero_progressivo_cliente = rec.numero_progressivo_cliente
                    obj.indirizzo = rec.indirizzo
                    obj.nazione_codice = rec.nazione_codice
                    obj.citta = rec.citta
                    obj.provincia = rec.provincia
                    obj.telefono_1 = rec.telefono_1
                    obj.attivo = True
                    obj.synced_at = now
                meta.rows_written += 1

            # Delete handling: mark_inactive per destinazioni non piu in sorgente
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
