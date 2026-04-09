"""
Read model Core slice `availability` (TASK-V2-049, DL-ARCH-V2-021).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da core_availability (mai dai mirror sync direttamente)
- il Core e il solo contratto ammesso tra sync e moduli applicativi futuri
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AvailabilityItem(BaseModel):
    """Disponibilita canonica per un singolo articolo (DL-ARCH-V2-021).

    availability_qty = inventory_qty - customer_set_aside_qty - committed_qty

    Il valore puo essere negativo: rappresenta una situazione di sovra-impegno.
    Non equivale ad ATP, disponibilita promessa o allocazione per priorita (V1 scope).
    """

    model_config = ConfigDict(frozen=True)

    article_code: str

    inventory_qty: Decimal
    customer_set_aside_qty: Decimal
    committed_qty: Decimal
    availability_qty: Decimal

    computed_at: datetime
