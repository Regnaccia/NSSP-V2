"""
Modelli SQLAlchemy per il target interno sync `destinazioni`.

Ownership: sync layer — solo questa sync unit scrive qui (DL-ARCH-V2-009 §1).

Tabelle di questa entita:
- sync_destinazioni: mirror interno di POT_DESTDIV (EasyJob) — owned da questa sync unit

Campi allineati a EASY_DESTINAZIONI.md (TASK-V2-011):
  codice_destinazione          <- PDES_COD (source identity)
  codice_cli                   <- CLI_COD (nullable)
  numero_progressivo_cliente   <- NUM_PROGR_CLIENTE (nullable)
  indirizzo                    <- PDES_IND (nullable)
  nazione_codice               <- NAZ_COD (nullable)
  citta                        <- CITTA (nullable)
  provincia                    <- PROV (nullable)
  telefono_1                   <- PDES_TEL1 (nullable)
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class SyncDestinazione(Base):
    """Mirror interno di POT_DESTDIV (EasyJob).

    Source identity key: codice_destinazione (PDES_COD in POT_DESTDIV).
    Delete handling: mark_inactive (attivo=False) — no hard delete.
    """

    __tablename__ = "sync_destinazioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codice_destinazione: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    # Riferimento al cliente (CLI_COD) — non FK hard verso sync_clienti per indipendenza
    codice_cli: Mapped[str | None] = mapped_column(String(32), nullable=True)
    numero_progressivo_cliente: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Campi di recapito
    indirizzo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nazione_codice: Mapped[str | None] = mapped_column(String(16), nullable=True)
    citta: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(4), nullable=True)
    telefono_1: Mapped[str | None] = mapped_column(String(64), nullable=True)

    attivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
