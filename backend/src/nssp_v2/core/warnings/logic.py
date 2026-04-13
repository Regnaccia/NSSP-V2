"""
Logiche di dominio Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029).

Struttura:
- is_negative_stock: condizione NEGATIVE_STOCK — inventory_qty < 0

Regole:
- il warning NEGATIVE_STOCK non e un need produttivo
- non genera automaticamente produzione
- la giacenza negativa e un'anomalia inventariale separata dalla logica planning
- la logica e pura e testabile in isolamento (DL-ARCH-V2-023 §principio)
"""

from decimal import Decimal


def is_negative_stock(inventory_qty: Decimal | None) -> bool:
    """Condizione NEGATIVE_STOCK: inventory_qty < 0.

    Restituisce False se inventory_qty e None.

    Un articolo con giacenza fisica negativa ha un'anomalia inventariale
    (movimenti fantasma, rettifiche non ancora sincronizzate).
    Non e un need produttivo: Planning Candidates usa stock_effective = max(0, stock_calculated).
    """
    if inventory_qty is None:
        return False
    return inventory_qty < Decimal("0")
