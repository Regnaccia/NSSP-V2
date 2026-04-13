"""
Modelli SQLAlchemy per i dati interni del Core slice `articoli` (DL-ARCH-V2-014).

Tabelle:
- articolo_famiglie: catalogo controllato delle famiglie articolo
- core_articolo_config: configurazione interna per articolo (famiglia, futuri dati interni)

Ownership: Core layer — nessun dato qui viene scritto dal layer sync.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class ArticoloFamiglia(Base):
    """Catalogo interno delle famiglie articolo.

    Il catalogo e controllato dal sistema V2.
    I codici sono stabili e non cambiano; le etichette possono essere aggiornate.

    Seed iniziale (DL-ARCH-V2-014 §2):
        materia_prima, articolo_standard, speciale, barre, conto_lavorazione

    Planning policy defaults (DL-ARCH-V2-026):
        considera_in_produzione: default di inclusione nel perimetro operativo planning/produzione.
        aggrega_codice_in_produzione: default di aggregabilita per codice nelle logiche operative.

    I valori effettivi per un articolo si ottengono risolvendo:
        effective = override_articolo if override_articolo is not None else family_default
    """

    __tablename__ = "articolo_famiglie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Planning policy defaults (DL-ARCH-V2-026)
    considera_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aggrega_codice_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Stock policy defaults V1 (DL-ARCH-V2-030, TASK-V2-083)
    # Nullable: None = famiglia non ha configurazione stock; non impone comportamento.
    # Validi solo per articoli con planning_mode = by_article.
    stock_months: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    stock_trigger_months: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)


class CoreArticoloConfig(Base):
    """Configurazione interna per articolo.

    PK: codice_articolo (string) — allineata al codice del mirror sync_articoli.
    Non e una FK hard verso sync_articoli per mantenere indipendenza dei layer.

    famiglia_code: riferimento stabile al code in articolo_famiglie.
                   Nullable: la mancanza di famiglia non blocca la surface.

    Override nullable tri-state (DL-ARCH-V2-026 §Override articolo):
        null  = eredita dalla famiglia (default)
        True  = sovrascrive con True indipendentemente dalla famiglia
        False = sovrascrive con False indipendentemente dalla famiglia

    override_considera_in_produzione: override puntuale per l'inclusione nel perimetro operativo.
    override_aggrega_codice_in_produzione: override puntuale per l'aggregabilita per codice.

    Risoluzione (effective policy):
        effective_value = override if override is not None else family_default
    """

    __tablename__ = "core_articolo_config"

    codice_articolo: Mapped[str] = mapped_column(String(25), primary_key=True)
    famiglia_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Override nullable tri-state (DL-ARCH-V2-026)
    override_considera_in_produzione: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    override_aggrega_codice_in_produzione: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Stock policy overrides articolo V1 (DL-ARCH-V2-030, TASK-V2-083)
    # Nullable: None = eredita il default famiglia; valore = sovrascrive.
    # capacity_override_qty: non ha default famiglia (proprieta articolo-specifica).
    override_stock_months: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    override_stock_trigger_months: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    capacity_override_qty: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
