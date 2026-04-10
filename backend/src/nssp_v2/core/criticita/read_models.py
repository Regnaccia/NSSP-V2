"""
Read model Core slice `criticita articoli` (TASK-V2-055, DL-ARCH-V2-023).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da core_availability + sync_articoli + core_articolo_config
- la logica di criticita e applicata nel layer Core, non nella UI
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CriticitaItem(BaseModel):
    """Articolo critico V1: availability_qty < 0.

    I valori quantitativi rispecchiano il computed fact `core_availability`.
    display_label e il campo sintetico di presentazione (DL-ARCH-V2-013 §6).
    famiglia_code / famiglia_label sono null se l'articolo non ha famiglia assegnata.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str
    descrizione_1: str | None
    descrizione_2: str | None
    display_label: str
    famiglia_code: str | None
    famiglia_label: str | None

    inventory_qty: Decimal
    customer_set_aside_qty: Decimal
    committed_qty: Decimal
    availability_qty: Decimal

    computed_at: datetime
