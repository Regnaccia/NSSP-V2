"""
Read model Core slice `customer_set_aside` (TASK-V2-044, DL-ARCH-V2-019).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da core_customer_set_aside (mai da sync o Easy direttamente)
- il Core e il solo contratto ammesso tra sync e moduli applicativi futuri
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CustomerSetAsideItem(BaseModel):
    """Quota appartata per cliente per una singola riga sorgente (DL-ARCH-V2-019).

    Un record per ogni riga ordine con set_aside_qty > 0.
    source_reference permette di risalire all'entita canonica sorgente.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str
    source_type: str        # "customer_order" nel primo slice V1
    source_reference: str   # "{order_reference}/{line_reference}" per customer_order
    set_aside_qty: Decimal
    computed_at: datetime


class CustomerSetAsideByArticleItem(BaseModel):
    """Quota appartata aggregata per articolo (DL-ARCH-V2-019 §4).

    Somma di tutti i set_aside_qty attivi per lo stesso article_code.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str
    total_set_aside_qty: Decimal
    set_aside_count: int     # numero di righe attive che contribuiscono al totale
    computed_at: datetime    # max(computed_at) tra le righe aggregate
