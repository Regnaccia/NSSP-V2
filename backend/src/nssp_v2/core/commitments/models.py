"""
Modello ORM per il computed fact `core_commitments` (TASK-V2-042, DL-ARCH-V2-017).

La tabella rappresenta gli impegni attivi per articolo, materializzati a partire
dal Core `customer_order_lines`.

Regole:
- il Core legge il Core ordini (che legge sync_righe_ordine_cliente), mai Easy direttamente
- il rebuild e deterministico: lo stesso input produce lo stesso output
- il calcolo e responsabilita esclusiva del Core
- nessuna FK verso tabelle sync o ordini: indipendenza di layer
- il modello e estendibile a future provenienze (production, trasferimenti, ecc.)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreCommitment(Base):
    """Impegno attivo materializzato per articolo e riga sorgente (DL-ARCH-V2-017).

    Un record per ogni domanda operativa ancora aperta (open_qty > 0).

    committed_qty (V1, customer_order) = open_qty dalla riga ordine canonica
                 = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
    """

    __tablename__ = "core_commitments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Campi canonici (DL-ARCH-V2-017 §4)
    article_code: Mapped[str] = mapped_column(String(25), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)      # es. "customer_order"
    source_reference: Mapped[str] = mapped_column(String(60), nullable=False)  # es. "ORD001/1"
    committed_qty: Mapped[Decimal] = mapped_column(Numeric(18, 5), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_core_commitments_article_code", "article_code"),
        Index("ix_core_commitments_source_type", "source_type"),
    )
