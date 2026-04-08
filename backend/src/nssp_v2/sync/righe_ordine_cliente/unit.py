"""
Sync unit `righe_ordine_cliente` (TASK-V2-040).

Contratto dichiarato esplicitamente (DL-ARCH-V2-009 §2-§8):
- ENTITY_CODE:         "righe_ordine_cliente"
- SOURCE_IDENTITY_KEY: "(order_reference, line_reference)"  (= (DOC_NUM, NUM_PROGR) in V_TORDCLI)
- ALIGNMENT_STRATEGY:  "upsert"
- CHANGE_ACQUISITION:  "full_scan"
- DELETE_HANDLING:     "no_delete_handling"
- DEPENDENCIES:        []

Strategia full_scan + upsert:
  La sync legge tutte le righe dalla sorgente a ogni esecuzione.
  Per ogni riga: INSERT se non presente, UPDATE se gia presente (keyed su source identity).
  Le righe non piu presenti in sorgente restano nel mirror (no_delete_handling).

Righe descrittive con continues_previous_line=True vengono preservate come record separati.
set_aside_qty (DOC_QTAP) viene salvato come dato sorgente distinto senza business logic.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.righe_ordine_cliente.source import RigaOrdineClienteSourceAdapter
from nssp_v2.sync.contract import RunMetadata


class RigheOrdineClienteSyncUnit:
    """Sync unit per l'entita `righe_ordine_cliente`.

    Responsabilita:
    - acquisisce righe ordine dalla sorgente V_TORDCLI (read-only)
    - allinea il target interno sync_righe_ordine_cliente via upsert
    - preserva le righe descrittive (continues_previous_line=True) come record separati
    - non interpreta set_aside_qty come logica di business
    - persiste run metadata e aggiorna freshness anchor

    Non implementa logiche di business.
    Non modifica ne legge il modello Core.
    """

    ENTITY_CODE = "righe_ordine_cliente"
    SOURCE_IDENTITY_KEY = "(order_reference, line_reference)"
    ALIGNMENT_STRATEGY = "upsert"
    CHANGE_ACQUISITION = "full_scan"
    DELETE_HANDLING = "no_delete_handling"
    DEPENDENCIES: list[str] = []

    def run(self, session: Session, source: RigaOrdineClienteSourceAdapter) -> RunMetadata:
        """Esegue la sync `righe_ordine_cliente`.

        Idempotente: piu esecuzioni con la stessa sorgente producono lo stesso stato.

        Args:
            session: sessione SQLAlchemy aperta dall'invocante
            source:  adapter read-only per la sorgente righe ordine

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

            # Carica le righe gia presenti nel target, keyed su (order_reference, line_reference)
            existing: dict[tuple[str, int], SyncRigaOrdineCliente] = {
                (obj.order_reference, obj.line_reference): obj
                for obj in session.query(SyncRigaOrdineCliente).all()
            }

            for rec in records:
                key = (rec.order_reference, rec.line_reference)
                obj = existing.get(key)

                if obj is None:
                    obj = SyncRigaOrdineCliente(
                        order_reference=rec.order_reference,
                        line_reference=rec.line_reference,
                        order_date=rec.order_date,
                        expected_delivery_date=rec.expected_delivery_date,
                        customer_code=rec.customer_code,
                        destination_code=rec.destination_code,
                        customer_destination_progressive=rec.customer_destination_progressive,
                        customer_order_reference=rec.customer_order_reference,
                        article_code=rec.article_code,
                        article_description_segment=rec.article_description_segment,
                        article_measure=rec.article_measure,
                        ordered_qty=rec.ordered_qty,
                        fulfilled_qty=rec.fulfilled_qty,
                        set_aside_qty=rec.set_aside_qty,
                        net_unit_price=rec.net_unit_price,
                        continues_previous_line=rec.continues_previous_line,
                        synced_at=now,
                    )
                    session.add(obj)
                else:
                    obj.order_date = rec.order_date
                    obj.expected_delivery_date = rec.expected_delivery_date
                    obj.customer_code = rec.customer_code
                    obj.destination_code = rec.destination_code
                    obj.customer_destination_progressive = rec.customer_destination_progressive
                    obj.customer_order_reference = rec.customer_order_reference
                    obj.article_code = rec.article_code
                    obj.article_description_segment = rec.article_description_segment
                    obj.article_measure = rec.article_measure
                    obj.ordered_qty = rec.ordered_qty
                    obj.fulfilled_qty = rec.fulfilled_qty
                    obj.set_aside_qty = rec.set_aside_qty
                    obj.net_unit_price = rec.net_unit_price
                    obj.continues_previous_line = rec.continues_previous_line
                    obj.synced_at = now

                meta.rows_written += 1

            # no_delete_handling: le righe non piu in sorgente restano nel mirror senza modifiche

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
