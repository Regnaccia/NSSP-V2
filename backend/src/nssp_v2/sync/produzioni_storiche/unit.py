"""
Sync unit `produzioni_storiche` (TASK-V2-029).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2–§8):
- ENTITY_CODE:          "produzioni_storiche"
- SOURCE_IDENTITY_KEY:  "id_dettaglio"  (= ID_DETTAGLIO in SDPRE_PROD/EasyJob)
- ALIGNMENT_STRATEGY:   "upsert"
- CHANGE_ACQUISITION:   "full_scan"
- DELETE_HANDLING:      "mark_inactive"
- DEPENDENCIES:         []
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.produzioni_storiche.source import ProduzioneStoricaSourceAdapter
from nssp_v2.sync.contract import RunMetadata


class ProduzioneStoricaSyncUnit:
    """Sync unit per l'entita `produzioni_storiche`.

    Responsabilita:
    - acquisisce produzioni storiche dalla sorgente SDPRE_PROD (read-only)
    - allinea il target interno sync_produzioni_storiche via upsert
    - marca inattive le produzioni non piu presenti in sorgente
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    """

    ENTITY_CODE = "produzioni_storiche"
    SOURCE_IDENTITY_KEY = "id_dettaglio"
    ALIGNMENT_STRATEGY = "upsert"
    CHANGE_ACQUISITION = "full_scan"
    DELETE_HANDLING = "mark_inactive"
    DEPENDENCIES: list[str] = []

    def run(self, session: Session, source: ProduzioneStoricaSourceAdapter) -> RunMetadata:
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

            existing: dict[int, SyncProduzioneStorica] = {
                obj.id_dettaglio: obj
                for obj in session.query(SyncProduzioneStorica).all()
            }

            seen_ids: set[int] = set()

            for rec in records:
                seen_ids.add(rec.id_dettaglio)
                obj = existing.get(rec.id_dettaglio)
                if obj is None:
                    obj = SyncProduzioneStorica(
                        id_dettaglio=rec.id_dettaglio,
                        cliente_ragione_sociale=rec.cliente_ragione_sociale,
                        codice_articolo=rec.codice_articolo,
                        descrizione_articolo=rec.descrizione_articolo,
                        descrizione_articolo_2=rec.descrizione_articolo_2,
                        numero_riga_documento=rec.numero_riga_documento,
                        quantita_ordinata=rec.quantita_ordinata,
                        quantita_prodotta=rec.quantita_prodotta,
                        materiale_partenza_codice=rec.materiale_partenza_codice,
                        materiale_partenza_per_pezzo=rec.materiale_partenza_per_pezzo,
                        misura_articolo=rec.misura_articolo,
                        numero_documento=rec.numero_documento,
                        codice_immagine=rec.codice_immagine,
                        riferimento_numero_ordine_cliente=rec.riferimento_numero_ordine_cliente,
                        riferimento_riga_ordine_cliente=rec.riferimento_riga_ordine_cliente,
                        note_articolo=rec.note_articolo,
                        attivo=True,
                        synced_at=now,
                    )
                    session.add(obj)
                else:
                    obj.cliente_ragione_sociale = rec.cliente_ragione_sociale
                    obj.codice_articolo = rec.codice_articolo
                    obj.descrizione_articolo = rec.descrizione_articolo
                    obj.descrizione_articolo_2 = rec.descrizione_articolo_2
                    obj.numero_riga_documento = rec.numero_riga_documento
                    obj.quantita_ordinata = rec.quantita_ordinata
                    obj.quantita_prodotta = rec.quantita_prodotta
                    obj.materiale_partenza_codice = rec.materiale_partenza_codice
                    obj.materiale_partenza_per_pezzo = rec.materiale_partenza_per_pezzo
                    obj.misura_articolo = rec.misura_articolo
                    obj.numero_documento = rec.numero_documento
                    obj.codice_immagine = rec.codice_immagine
                    obj.riferimento_numero_ordine_cliente = rec.riferimento_numero_ordine_cliente
                    obj.riferimento_riga_ordine_cliente = rec.riferimento_riga_ordine_cliente
                    obj.note_articolo = rec.note_articolo
                    obj.attivo = True
                    obj.synced_at = now
                meta.rows_written += 1

            for id_dettaglio, obj in existing.items():
                if id_dettaglio not in seen_ids and obj.attivo:
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

    def _persist_metadata(self, session, meta, *, success):
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
