"""
Modelli SQLAlchemy per i dati interni del Core slice `articoli` (DL-ARCH-V2-014).

Tabelle:
- articolo_famiglie: catalogo controllato delle famiglie articolo
- core_articolo_config: configurazione interna per articolo (famiglia, futuri dati interni)

Ownership: Core layer — nessun dato qui viene scritto dal layer sync.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class ArticoloFamiglia(Base):
    """Catalogo interno delle famiglie articolo.

    Il catalogo e controllato dal sistema V2.
    I codici sono stabili e non cambiano; le etichette possono essere aggiornate.

    Seed iniziale (DL-ARCH-V2-014 §2):
        materia_prima, articolo_standard, speciale, barre, conto_lavorazione
    """

    __tablename__ = "articolo_famiglie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    considera_in_produzione: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CoreArticoloConfig(Base):
    """Configurazione interna per articolo.

    PK: codice_articolo (string) — allineata al codice del mirror sync_articoli.
    Non e una FK hard verso sync_articoli per mantenere indipendenza dei layer.

    famiglia_code: riferimento stabile al code in articolo_famiglie.
                   Nullable: la mancanza di famiglia non blocca la surface.
    """

    __tablename__ = "core_articolo_config"

    codice_articolo: Mapped[str] = mapped_column(String(25), primary_key=True)
    famiglia_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
