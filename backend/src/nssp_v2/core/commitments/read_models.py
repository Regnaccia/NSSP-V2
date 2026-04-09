"""
Read model Core slice `commitments` (TASK-V2-042, DL-ARCH-V2-017).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da core_commitments (mai da sync o Easy direttamente)
- il Core e il solo contratto ammesso tra sync e moduli applicativi futuri
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CommitmentItem(BaseModel):
    """Impegno attivo per una singola riga sorgente (DL-ARCH-V2-017).

    Un record per ogni domanda operativa ancora aperta.
    source_reference permette di risalire all'entita canonica sorgente.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str
    source_type: str        # "customer_order" nel primo slice V1
    source_reference: str   # "{order_reference}/{line_reference}" per customer_order
    committed_qty: Decimal
    computed_at: datetime


class CommitmentsByArticleItem(BaseModel):
    """Impegno aggregato per articolo (DL-ARCH-V2-017 §5).

    Somma di tutti i committed_qty attivi per lo stesso article_code,
    indipendentemente dalla provenienza (source_type).

    V1: un solo source_type (customer_order); il modello e pronto per futuri aggregati multi-sorgente.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str
    total_committed_qty: Decimal
    commitment_count: int    # numero di righe attive che contribuiscono all'impegno
    computed_at: datetime    # max(computed_at) tra le righe aggregate
