"""
Core slice `customer_set_aside` (TASK-V2-044, DL-ARCH-V2-019).

Computed fact canonico: quantita gia inscatolata/appartata per cliente (DOC_QTAP).
Distinto da `commitments` (open_qty) e da `inventory` (stock fisico netto).
Prima provenienza: customer_order (set_aside_qty da customer_order_lines).

Esporta il contratto riusabile per stream futuri (availability, UI).
"""

from nssp_v2.core.customer_set_aside.queries import (
    rebuild_customer_set_aside,
    list_customer_set_aside,
    get_customer_set_aside_by_article,
)
from nssp_v2.core.customer_set_aside.read_models import (
    CustomerSetAsideItem,
    CustomerSetAsideByArticleItem,
)

__all__ = [
    "rebuild_customer_set_aside",
    "list_customer_set_aside",
    "get_customer_set_aside_by_article",
    "CustomerSetAsideItem",
    "CustomerSetAsideByArticleItem",
]
