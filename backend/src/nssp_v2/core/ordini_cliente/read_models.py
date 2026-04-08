"""
Read model Core slice `ordini_cliente` (TASK-V2-041, DL-ARCH-V2-018).

Regole:
- i read model sono frozen (immutabili)
- i dati provengono da sync_righe_ordine_cliente (mai da Easy direttamente)
- il Core e il solo contratto ammesso tra sync e moduli applicativi futuri
- i dati cliente/destinazione sono esposti come codici di riferimento, non come copie persistite
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CustomerOrderLineItem(BaseModel):
    """Riga ordine cliente canonica (DL-ARCH-V2-018).

    Entita operativa minima del dominio ordini: una riga ordine per articolo.

    Formula open_qty (V1):
        open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
        (valori None trattati come 0)

    Regola is_main_destination:
        customer_destination_progressive vuoto/None => is_main_destination = True

    description_lines:
        segmenti descrittivi provenienti dalle righe COLL_RIGA_PREC=True immediatamente
        successive nel mirror sync. Non generano quantita autonoma.
    """

    model_config = ConfigDict(frozen=True)

    # Identity canonica
    order_reference: str
    line_reference: int

    # Riferimenti ordine
    order_date: datetime | None
    expected_delivery_date: datetime | None
    customer_order_reference: str | None

    # Riferimenti cliente e destinazione (codici canonici — non copie persistite)
    customer_code: str | None
    destination_code: str | None
    customer_destination_progressive: str | None
    is_main_destination: bool  # True se NUM_PROGR_CLIENTE vuoto/None

    # Articolo
    article_code: str | None
    article_measure: str | None
    article_description_segment: str | None  # segmento principale della riga
    description_lines: list[str]             # segmenti da righe COLL_RIGA_PREC=True successive

    # Quantita
    ordered_qty: Decimal | None
    fulfilled_qty: Decimal | None
    set_aside_qty: Decimal | None
    open_qty: Decimal  # max(ordered_qty - set_aside_qty - fulfilled_qty, 0)

    # Prezzo
    net_unit_price: Decimal | None
