"""
Core slice `ordini_cliente` (TASK-V2-041, DL-ARCH-V2-018).

Esporta il contratto canonico riusabile per stream futuri (commitments, disponibilita, UI).
"""

from nssp_v2.core.ordini_cliente.queries import (
    list_customer_order_lines,
    get_order_lines_by_order,
    get_order_line,
)
from nssp_v2.core.ordini_cliente.read_models import CustomerOrderLineItem

__all__ = [
    "list_customer_order_lines",
    "get_order_lines_by_order",
    "get_order_line",
    "CustomerOrderLineItem",
]
