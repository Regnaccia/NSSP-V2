"""
Modello ORM per il mirror sync `sync_mag_reale` (TASK-V2-036).

Contratto:
- ENTITY_CODE:         "mag_reale"
- ALIGNMENT_STRATEGY:  "append_only"
- CHANGE_ACQUISITION:  "cursor"   (cursor = max id_movimento gia presente)
- DELETE_HANDLING:     "no_delete_handling"

Il layer sync non calcola giacenza.
Il mirror e read-only rispetto a Easy.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class SyncMagReale(Base):
    """Mirror di un movimento di magazzino proveniente da MAG_REALE.

    Ogni riga rappresenta un singolo movimento.
    id_movimento = ID_MAGREALE (source identity key).
    codice_articolo viene normalizzato (strip + uppercase) in ingresso.
    """

    __tablename__ = "sync_mag_reale"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_movimento: Mapped[int] = mapped_column(Integer, nullable=False)

    codice_articolo: Mapped[str | None] = mapped_column(String(25), nullable=True)
    quantita_caricata: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    quantita_scaricata: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    causale_movimento_codice: Mapped[str | None] = mapped_column(String(6), nullable=True)
    data_movimento: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("id_movimento", name="uq_sync_mag_reale_id_movimento"),
    )
