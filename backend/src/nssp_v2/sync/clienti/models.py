"""
Modelli SQLAlchemy per il target interno sync `clienti`.

Ownership: sync layer — solo le sync unit scrivono qui (DL-ARCH-V2-009 §1).

Tabelle di questa entita:
- sync_clienti: mirror interno di ANACLI (EasyJob) — owned da questa sync unit

Le strutture condivise del layer sync (run log, freshness anchor) sono in:
    nssp_v2.sync.models
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base

# Re-export per comodita degli import nella sync unit e nei test
from nssp_v2.sync.models import SyncEntityState, SyncRunLog  # noqa: F401


class SyncCliente(Base):
    """Mirror interno di ANACLI (EasyJob).

    Source identity key: codice_cli (CLI_COD in ANACLI).
    Delete handling: mark_inactive (attivo=False) — no hard delete.
    """

    __tablename__ = "sync_clienti"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codice_cli: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    ragione_sociale: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    attivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
