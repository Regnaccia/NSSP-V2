"""
Modelli SQLAlchemy condivisi del layer `sync`.

Ownership: layer `sync` — non specifici di una singola entita.

Questi modelli sono trasversali a tutte le sync unit e non devono risiedere
nel package di una singola entita (DL-ARCH-V2-009 §6, §7).

Tabelle:
- sync_run_log:       metadati di ogni singola esecuzione di sync
- sync_entity_state:  freshness anchor per entita (last_success_at)
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class SyncRunLog(Base):
    """Metadati di una singola esecuzione di sync (DL-ARCH-V2-009 §6).

    Un record per ogni run, indipendentemente dall'esito.
    Condiviso da tutte le sync unit.
    """

    __tablename__ = "sync_run_log"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)   # UUID
    entity_code: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)      # running|success|error
    rows_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncEntityState(Base):
    """Freshness anchor per entita (DL-ARCH-V2-009 §7).

    Un record per entity_code. Aggiornato a ogni run completato con successo.
    Usato per la freshness policy definita in DL-ARCH-V2-008 §5.
    Condiviso da tutte le sync unit.
    """

    __tablename__ = "sync_entity_state"

    entity_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
