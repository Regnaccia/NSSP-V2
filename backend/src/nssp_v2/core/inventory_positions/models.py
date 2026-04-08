"""
Modello ORM per il computed fact `core_inventory_positions` (TASK-V2-037, DL-ARCH-V2-016).

La tabella rappresenta una giacenza netta materializzata per articolo.
Viene ricostruita completamente (rebuild) a partire da sync_mag_reale.

Regole:
- il Core legge sync_mag_reale, mai Easy direttamente
- nessuna FK verso sync_mag_reale: indipendenza di layer
- il rebuild e deterministico: lo stesso input produce lo stesso output
- il calcolo di business (giacenza) e responsabilita esclusiva del Core
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreInventoryPosition(Base):
    """Giacenza netta materializzata per codice articolo (DL-ARCH-V2-016).

    Ogni riga rappresenta la posizione inventariale aggregata di un singolo articolo.
    Costruita interamente da Core a partire dai movimenti sync (sync_mag_reale).

    on_hand_qty = total_load_qty - total_unload_qty
    """

    __tablename__ = "core_inventory_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_code: Mapped[str] = mapped_column(String(25), nullable=False)

    # Aggregati dai movimenti sync
    total_load_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_unload_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    on_hand_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    movement_count: Mapped[int] = mapped_column(nullable=False)

    # Metadati temporali
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_last_movement_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("article_code", name="uq_core_inventory_positions_article_code"),
    )
