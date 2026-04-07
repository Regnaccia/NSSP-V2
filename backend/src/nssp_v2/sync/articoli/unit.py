"""
Sync unit `articoli` (TASK-V2-018).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2–§8):
- ENTITY_CODE:          "articoli"
- SOURCE_IDENTITY_KEY:  "codice_articolo"  (= ART_COD in ANAART/EasyJob)
- ALIGNMENT_STRATEGY:   "upsert"
- CHANGE_ACQUISITION:   "full_scan"
- DELETE_HANDLING:      "mark_inactive"
- DEPENDENCIES:         []  (nessuna: articoli non dipende da altre sync unit)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.articoli.source import ArticoloSourceAdapter
from nssp_v2.sync.contract import RunMetadata


class ArticoloSyncUnit:
    """Sync unit per l'entita `articoli`.

    Responsabilita:
    - acquisisce articoli dalla sorgente (read-only)
    - allinea il target interno sync_articoli via upsert
    - marca inattivi gli articoli non piu presenti in sorgente
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    """

    # ─── Contratto obbligatorio DL-ARCH-V2-009 ───────────────────────────────

    ENTITY_CODE = "articoli"
    SOURCE_IDENTITY_KEY = "codice_articolo"
    ALIGNMENT_STRATEGY = "upsert"
    CHANGE_ACQUISITION = "full_scan"
    DELETE_HANDLING = "mark_inactive"
    DEPENDENCIES: list[str] = []

    # ─── Esecuzione ──────────────────────────────────────────────────────────

    def run(self, session: Session, source: ArticoloSourceAdapter) -> RunMetadata:
        """Esegue la sync `articoli`.

        Idempotente: piu esecuzioni con la stessa sorgente producono lo stesso stato.

        Args:
            session:  sessione SQLAlchemy aperta dall'invocante
            source:   adapter read-only per la sorgente articoli

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
            existing: dict[str, SyncArticolo] = {
                obj.codice_articolo: obj
                for obj in session.query(SyncArticolo).all()
            }

            seen_codes: set[str] = set()

            for rec in records:
                seen_codes.add(rec.codice_articolo)
                obj = existing.get(rec.codice_articolo)
                if obj is None:
                    obj = SyncArticolo(
                        codice_articolo=rec.codice_articolo,
                        descrizione_1=rec.descrizione_1,
                        descrizione_2=rec.descrizione_2,
                        unita_misura_codice=rec.unita_misura_codice,
                        source_modified_at=rec.source_modified_at,
                        categoria_articolo_1=rec.categoria_articolo_1,
                        materiale_grezzo_codice=rec.materiale_grezzo_codice,
                        quantita_materiale_grezzo_occorrente=rec.quantita_materiale_grezzo_occorrente,
                        quantita_materiale_grezzo_scarto=rec.quantita_materiale_grezzo_scarto,
                        misura_articolo=rec.misura_articolo,
                        codice_immagine=rec.codice_immagine,
                        contenitori_magazzino=rec.contenitori_magazzino,
                        peso_grammi=rec.peso_grammi,
                        attivo=True,
                        synced_at=now,
                    )
                    session.add(obj)
                else:
                    obj.descrizione_1 = rec.descrizione_1
                    obj.descrizione_2 = rec.descrizione_2
                    obj.unita_misura_codice = rec.unita_misura_codice
                    obj.source_modified_at = rec.source_modified_at
                    obj.categoria_articolo_1 = rec.categoria_articolo_1
                    obj.materiale_grezzo_codice = rec.materiale_grezzo_codice
                    obj.quantita_materiale_grezzo_occorrente = rec.quantita_materiale_grezzo_occorrente
                    obj.quantita_materiale_grezzo_scarto = rec.quantita_materiale_grezzo_scarto
                    obj.misura_articolo = rec.misura_articolo
                    obj.codice_immagine = rec.codice_immagine
                    obj.contenitori_magazzino = rec.contenitori_magazzino
                    obj.peso_grammi = rec.peso_grammi
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
