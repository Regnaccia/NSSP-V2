"""
Modelli SQLAlchemy per il target interno sync `articoli`.

Ownership: sync layer — solo le sync unit scrivono qui (DL-ARCH-V2-009 §1).

Tabelle di questa entita:
- sync_articoli: mirror interno di ANAART (EasyJob) — owned da questa sync unit

Campi allineati a EASY_ARTICOLI.md (TASK-V2-018):
  codice_articolo                     <- ART_COD  (source identity)
  descrizione_1                       <- ART_DES1 (nullable)
  descrizione_2                       <- ART_DES2 (nullable)
  unita_misura_codice                 <- UM_COD   (nullable)
  source_modified_at                  <- ART_DTMO (nullable)
  categoria_articolo_1                <- CAT_ART1 (nullable)
  materiale_grezzo_codice             <- MAT_COD  (nullable)
  quantita_materiale_grezzo_occorrente <- REGN_QT_OCCORR (nullable)
  quantita_materiale_grezzo_scarto    <- REGN_QT_SCARTO  (nullable)
  misura_articolo                     <- ART_MISURA (nullable)
  codice_immagine                     <- COD_IMM    (nullable)
  contenitori_magazzino               <- ART_CONTEN (nullable)
  peso_grammi                         <- ART_KG     (nullable)

Le strutture condivise del layer sync (run log, freshness anchor) sono in:
    nssp_v2.sync.models
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base

# Re-export per comodita degli import nella sync unit e nei test
from nssp_v2.sync.models import SyncEntityState, SyncRunLog  # noqa: F401


class SyncArticolo(Base):
    """Mirror interno di ANAART (EasyJob).

    Source identity key: codice_articolo (ART_COD in ANAART).
    Delete handling: mark_inactive (attivo=False) — no hard delete.
    """

    __tablename__ = "sync_articoli"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codice_articolo: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)

    # Descrizione
    descrizione_1: Mapped[str | None] = mapped_column(String(100), nullable=True)
    descrizione_2: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Unita di misura
    unita_misura_codice: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Data ultima modifica lato sorgente (candidato watermark futuro)
    source_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    # Categoria e materiale
    categoria_articolo_1: Mapped[str | None] = mapped_column(String(6), nullable=True)
    materiale_grezzo_codice: Mapped[str | None] = mapped_column(String(25), nullable=True)

    # Quantita produzione
    quantita_materiale_grezzo_occorrente: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 5), nullable=True
    )
    quantita_materiale_grezzo_scarto: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 5), nullable=True
    )

    # Attributi articolo
    misura_articolo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    codice_immagine: Mapped[str | None] = mapped_column(String(3), nullable=True)
    contenitori_magazzino: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Peso (in grammi secondo convenzione operativa corrente — da validare)
    peso_grammi: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    attivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
