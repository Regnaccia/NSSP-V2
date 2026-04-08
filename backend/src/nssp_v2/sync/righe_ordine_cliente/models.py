"""
Modelli SQLAlchemy per il target interno sync `righe_ordine_cliente` (TASK-V2-040).

Ownership: sync layer — solo le sync unit scrivono qui (DL-ARCH-V2-009 §1).

Tabella:
- sync_righe_ordine_cliente: mirror interno di V_TORDCLI (EasyJob)

Source identity: (order_reference, line_reference) = (DOC_NUM, NUM_PROGR)

Campi allineati a EASY_RIGHE_ORDINE_CLIENTE.md:
  DOC_NUM              -> order_reference                    (source identity, parte 1)
  NUM_PROGR            -> line_reference                     (source identity, parte 2)
  DOC_DATA             -> order_date                        (nullable)
  DOC_PREV             -> expected_delivery_date             (nullable)
  CLI_COD              -> customer_code                      (nullable)
  PDES_COD             -> destination_code                   (nullable)
  NUM_PROGR_CLIENTE    -> customer_destination_progressive   (nullable)
  N_ORDCLI             -> customer_order_reference           (nullable)
  ART_COD              -> article_code                       (nullable: vuoto sulle righe descrittive)
  ART_DESCR            -> article_description_segment        (nullable)
  ART_MISURA           -> article_measure                    (nullable)
  DOC_QTOR             -> ordered_qty                        (nullable)
  DOC_QTEV             -> fulfilled_qty                      (nullable)
  DOC_QTAP             -> set_aside_qty                      (nullable — quantita inscatolata/appartata)
  DOC_PZ_NETTO         -> net_unit_price                     (nullable)
  COLL_RIGA_PREC       -> continues_previous_line            (nullable)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base

from nssp_v2.sync.models import SyncEntityState, SyncRunLog  # noqa: F401


class SyncRigaOrdineCliente(Base):
    """Mirror interno di V_TORDCLI (EasyJob).

    Source identity: (order_reference, line_reference) = (DOC_NUM, NUM_PROGR).
    Delete handling: no_delete_handling — le righe non piu in sorgente restano nel mirror.
    """

    __tablename__ = "sync_righe_ordine_cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Source identity
    order_reference: Mapped[str] = mapped_column(String(10), nullable=False)
    line_reference: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dati testata ordine
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    expected_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    # Riferimenti cliente e destinazione
    customer_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    destination_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    customer_destination_progressive: Mapped[str | None] = mapped_column(String(6), nullable=True)
    customer_order_reference: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Riferimenti articolo e descrizione
    article_code: Mapped[str | None] = mapped_column(String(25), nullable=True)
    article_description_segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    article_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quantita
    ordered_qty: Mapped[Decimal | None] = mapped_column(Numeric(13, 5), nullable=True)
    fulfilled_qty: Mapped[Decimal | None] = mapped_column(Numeric(13, 5), nullable=True)
    set_aside_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    # Prezzo
    net_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    # Flag riga descrittiva di continuazione
    continues_previous_line: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Metadati sync
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "order_reference", "line_reference",
            name="uq_sync_righe_ordine_cliente_order_line",
        ),
    )
