"""
Query del Core slice `inventory_positions` (TASK-V2-037, DL-ARCH-V2-016).

Regole:
- legge da sync_mag_reale (mai da Easy direttamente)
- scrive solo su core_inventory_positions
- il rebuild e completo e deterministico: delete-all + re-insert
- nessun calcolo di giacenza nel layer sync
- nessuna logica di modulo locale
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.inventory_positions.models import CoreInventoryPosition
from nssp_v2.core.inventory_positions.read_models import InventoryPositionItem
from nssp_v2.sync.mag_reale.models import SyncMagReale


# ─── Rebuild completo ─────────────────────────────────────────────────────────

def rebuild_inventory_positions(session: Session) -> int:
    """Ricostruisce completamente le posizioni inventariali da sync_mag_reale.

    Strategia:
      1. elimina tutte le righe esistenti in core_inventory_positions
      2. aggrega i movimenti per article_code (GROUP BY codice_articolo)
      3. calcola on_hand_qty = sum(quantita_caricata) - sum(quantita_scaricata)
      4. inserisce le nuove righe materializzate

    I movimenti con codice_articolo = NULL vengono ignorati: non possono
    contribuire a una posizione identificabile per articolo.

    Restituisce il numero di righe di giacenza create.
    Non fa commit: il chiamante gestisce la transazione.
    """
    computed_at = datetime.now(timezone.utc)

    # Step 1: delete
    session.query(CoreInventoryPosition).delete(synchronize_session=False)
    session.flush()

    # Step 2: aggrega per articolo da sync_mag_reale
    rows = (
        session.query(
            SyncMagReale.codice_articolo,
            func.sum(
                func.coalesce(SyncMagReale.quantita_caricata, 0)
            ).label("total_load"),
            func.sum(
                func.coalesce(SyncMagReale.quantita_scaricata, 0)
            ).label("total_unload"),
            func.count(SyncMagReale.id).label("movement_count"),
            func.max(SyncMagReale.data_movimento).label("last_movement_date"),
        )
        .filter(SyncMagReale.codice_articolo.isnot(None))
        .group_by(SyncMagReale.codice_articolo)
        .all()
    )

    # Step 3+4: calcola e inserisce
    created = 0
    for row in rows:
        load = Decimal(str(row.total_load))
        unload = Decimal(str(row.total_unload))
        position = CoreInventoryPosition(
            article_code=row.codice_articolo,
            total_load_qty=load,
            total_unload_qty=unload,
            on_hand_qty=load - unload,
            movement_count=row.movement_count,
            computed_at=computed_at,
            source_last_movement_date=row.last_movement_date,
        )
        session.add(position)
        created += 1

    session.flush()
    return created


# ─── Read: lista posizioni inventariali ──────────────────────────────────────

def list_inventory_positions(session: Session) -> list[InventoryPositionItem]:
    """Restituisce tutte le posizioni inventariali ordinate per article_code."""
    rows = (
        session.query(CoreInventoryPosition)
        .order_by(CoreInventoryPosition.article_code)
        .all()
    )
    return [_to_item(r) for r in rows]


def get_inventory_position(
    session: Session,
    article_code: str,
) -> InventoryPositionItem | None:
    """Restituisce la posizione inventariale di un singolo articolo, o None se assente."""
    row = (
        session.query(CoreInventoryPosition)
        .filter(CoreInventoryPosition.article_code == article_code)
        .first()
    )
    return _to_item(row) if row is not None else None


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_item(row: CoreInventoryPosition) -> InventoryPositionItem:
    return InventoryPositionItem(
        article_code=row.article_code,
        total_load_qty=row.total_load_qty,
        total_unload_qty=row.total_unload_qty,
        on_hand_qty=row.on_hand_qty,
        movement_count=row.movement_count,
        computed_at=row.computed_at,
        source_last_movement_date=row.source_last_movement_date,
    )
