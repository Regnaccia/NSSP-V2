"""
Modelli SQLAlchemy per il target interno sync `produzioni_storiche`.

Ownership: sync layer — solo le sync unit scrivono qui (DL-ARCH-V2-009 §1).

Tabelle di questa entita:
- sync_produzioni_storiche: mirror interno di SDPRE_PROD (EasyJob) — owned da questa sync unit

Campi allineati a EASY_PRODUZIONI.md (TASK-V2-029) — stesso mapping di produzioni_attive:
  id_dettaglio                        <- ID_DETTAGLIO  (source identity)
  cliente_ragione_sociale             <- CLI_RAG1       (nullable)
  codice_articolo                     <- ART_COD        (nullable)
  descrizione_articolo                <- ART_DESCR      (nullable)
  descrizione_articolo_2              <- ART_DES2       (nullable)
  numero_riga_documento               <- NR_RIGA        (nullable)
  quantita_ordinata                   <- DOC_QTOR       (nullable)
  quantita_prodotta                   <- DOC_QTEV       (nullable)
  materiale_partenza_codice           <- MAT_COD        (nullable)
  materiale_partenza_per_pezzo        <- MM_PEZZO       (nullable)
  misura_articolo                     <- ART_MISURA     (nullable)
  numero_documento                    <- DOC_NUM        (nullable)
  codice_immagine                     <- COD_IMM        (nullable)
  riferimento_numero_ordine_cliente   <- NUM_ORDINE     (nullable)
  riferimento_riga_ordine_cliente     <- RIGA_ORDINE    (nullable)
  note_articolo                       <- NOTE_ARTICOLO  (nullable)

Differenze tecniche note vs DPRE_PROD (EASY_PRODUZIONI.md §Structural Check):
  - COD_RIGA: varchar(6) vs varchar(25) — campo deferred, non mappato
  - scritto (lowercase) vs SCRITTO — campo deferred, non mappato

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


class SyncProduzioneStorica(Base):
    """Mirror interno di SDPRE_PROD (EasyJob).

    Source identity key: id_dettaglio (ID_DETTAGLIO in SDPRE_PROD).
    Delete handling: mark_inactive (attivo=False) — no hard delete.
    """

    __tablename__ = "sync_produzioni_storiche"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_dettaglio: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    # Cliente
    cliente_ragione_sociale: Mapped[str | None] = mapped_column(String(55), nullable=True)

    # Articolo
    codice_articolo: Mapped[str | None] = mapped_column(String(25), nullable=True)
    descrizione_articolo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    descrizione_articolo_2: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Documento e riga
    numero_riga_documento: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_documento: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Quantita
    quantita_ordinata: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)
    quantita_prodotta: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    # Materiale
    materiale_partenza_codice: Mapped[str | None] = mapped_column(String(25), nullable=True)
    materiale_partenza_per_pezzo: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    # Attributi articolo
    misura_articolo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    codice_immagine: Mapped[str | None] = mapped_column(String(1), nullable=True)

    # Riferimento ordine cliente
    riferimento_numero_ordine_cliente: Mapped[str | None] = mapped_column(String(10), nullable=True)
    riferimento_riga_ordine_cliente: Mapped[Decimal | None] = mapped_column(Numeric(18, 0), nullable=True)

    # Note
    note_articolo: Mapped[str | None] = mapped_column(String(55), nullable=True)

    attivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
