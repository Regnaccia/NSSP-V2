"""
Modello ORM per il computed fact `core_customer_set_aside` (TASK-V2-044, DL-ARCH-V2-019).

La tabella rappresenta la quantita gia inscatolata/appartata per cliente, materializzata
a partire dal Core `customer_order_lines` (campo DOC_QTAP = set_aside_qty).

Regole:
- il Core legge il Core ordini (che legge sync_righe_ordine_cliente), mai Easy direttamente
- il rebuild e deterministico: lo stesso input produce lo stesso output
- il calcolo e responsabilita esclusiva del Core
- nessuna FK verso tabelle sync o ordini: indipendenza di layer
- concetto distinto da `commitments` (open_qty) e da `inventory` (stock fisico netto)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreCustomerSetAside(Base):
    """Quota appartata per cliente materializzata per articolo e riga sorgente (DL-ARCH-V2-019).

    Un record per ogni riga ordine con set_aside_qty > 0.

    set_aside_qty (V1, customer_order) = DOC_QTAP dalla riga ordine canonica
    """

    __tablename__ = "core_customer_set_aside"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Campi canonici (DL-ARCH-V2-019 §4)
    article_code: Mapped[str] = mapped_column(String(25), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)      # "customer_order"
    source_reference: Mapped[str] = mapped_column(String(60), nullable=False)  # "{order_ref}/{line_ref}"
    set_aside_qty: Mapped[Decimal] = mapped_column(Numeric(18, 5), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_core_customer_set_aside_article_code", "article_code"),
        Index("ix_core_customer_set_aside_source_type", "source_type"),
    )
