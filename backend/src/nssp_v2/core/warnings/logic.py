"""
Logiche di dominio Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029, TASK-V2-091).

Struttura:
- is_negative_stock: condizione NEGATIVE_STOCK — inventory_qty < 0
- is_invalid_stock_capacity: condizione INVALID_STOCK_CAPACITY — capacity_effective_qty None o <= 0

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


def is_invalid_stock_capacity(capacity_effective_qty: Decimal | None) -> bool:
    """Condizione INVALID_STOCK_CAPACITY: capacity_effective_qty None o <= 0.

    Un articolo con planning_mode by_article ma capacity non calcolabile (o zero)
    non puo produrre un target_stock_qty significativo.
    Questo caso segnala un problema di dato o di configurazione (mancano
    contenitori_magazzino, peso_grammi, o max_container_weight_kg).

    Restituisce True se:
    - capacity_effective_qty e None (nessun dato capacity disponibile)
    - capacity_effective_qty <= 0 (capacity zero o negativa — invalida)
    """
    if capacity_effective_qty is None:
        return True
    return capacity_effective_qty <= Decimal("0")
