"""
Core slice `commitments` (TASK-V2-042, DL-ARCH-V2-017).

Computed fact canonico: quantita impegnata da domanda operativa non ancora chiusa.
Prima provenienza: customer_order (open_qty da customer_order_lines).

Esporta il contratto riusabile per stream futuri (availability, UI).
"""

from nssp_v2.core.commitments.queries import (
    rebuild_commitments,
    list_commitments,
    get_commitments_by_article,
)
from nssp_v2.core.commitments.read_models import CommitmentItem, CommitmentsByArticleItem

__all__ = [
    "rebuild_commitments",
    "list_commitments",
    "get_commitments_by_article",
    "CommitmentItem",
    "CommitmentsByArticleItem",
]
