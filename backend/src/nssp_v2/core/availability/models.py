"""
Modello ORM per il computed fact `core_availability` (TASK-V2-049, DL-ARCH-V2-021).

La tabella rappresenta la quota libera per articolo, derivata dai tre fact canonici:
- inventory_positions  (stock fisico netto)
- customer_set_aside   (quota appartata per cliente, DOC_QTAP)
- commitments          (domanda operativa ancora aperta)

Formula canonica V1:
    availability_qty = inventory_qty - customer_set_aside_qty - committed_qty

Regole:
- il Core legge i tre fact canonici, mai i mirror sync grezzi
- il rebuild e deterministico: lo stesso input produce lo stesso output
- availability_qty puo risultare negativa (nessun clamp a zero)
- i fact mancanti per articolo valgono 0 nel calcolo
- nessuna FK verso tabelle sync: indipendenza di layer
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreAvailability(Base):
    """Quota libera materializzata per codice articolo (DL-ARCH-V2-021).

    Ogni riga rappresenta la disponibilita aggregata di un singolo articolo.

    availability_qty = inventory_qty - customer_set_aside_qty - committed_qty
    """

    __tablename__ = "core_availability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_code: Mapped[str] = mapped_column(String(25), nullable=False)

    # Contributi numerici dai tre fact sorgente
    inventory_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    customer_set_aside_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    committed_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    # Derivato canonico (puo essere negativo)
    availability_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("article_code", name="uq_core_availability_article_code"),
    )
