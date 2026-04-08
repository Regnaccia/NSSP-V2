"""
Read model Core slice `inventory_positions` (TASK-V2-037, DL-ARCH-V2-016).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da core_inventory_positions (mai da sync_mag_reale direttamente)
- il Core e il solo contratto ammesso tra sync e moduli applicativi futuri
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InventoryPositionItem(BaseModel):
    """Posizione inventariale canonica per un singolo articolo (DL-ARCH-V2-016).

    Computed fact: on_hand_qty = total_load_qty - total_unload_qty.
    Non include disponibilita, allocazioni o stock bloccato (V1 scope).
    """

    model_config = ConfigDict(frozen=True)

    article_code: str

    total_load_qty: Decimal
    total_unload_qty: Decimal
    on_hand_qty: Decimal
    movement_count: int

    computed_at: datetime
    source_last_movement_date: datetime | None
