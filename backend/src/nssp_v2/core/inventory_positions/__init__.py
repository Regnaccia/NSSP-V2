"""
Core slice `inventory_positions` (TASK-V2-037, DL-ARCH-V2-016).

Computed fact canonica: giacenza netta per articolo.
Formula: on_hand_qty = sum(quantita_caricata) - sum(quantita_scaricata)
"""

from nssp_v2.core.inventory_positions.queries import (
    rebuild_inventory_positions,
    list_inventory_positions,
    get_inventory_position,
)
from nssp_v2.core.inventory_positions.read_models import InventoryPositionItem

__all__ = [
    "rebuild_inventory_positions",
    "list_inventory_positions",
    "get_inventory_position",
    "InventoryPositionItem",
]
