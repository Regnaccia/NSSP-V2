"""
Modello ORM per la configurazione di visibilita dei warning (TASK-V2-077, TASK-V2-081, DL-ARCH-V2-029).

Tabella `core_warning_type_config`:
- un record per tipo warning (NEGATIVE_STOCK, ...)
- `visible_to_areas`: lista di aree/reparti operativi in cui il warning e visibile
- governata dalla surface `admin`

Regola (DL-ARCH-V2-029 §3):
- la visibilita e modellata come metadato del warning canonico
- non esistono warning distinti per reparto
- la configurazione e accessibile e modificabile da admin

Aree valide V1: magazzino, produzione, logistica
(TASK-V2-081: migrazione da visible_in_surfaces a visible_to_areas)
"""

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class WarningTypeConfig(Base):
    """Configurazione di visibilita per tipo warning.

    Un record per ogni tipo warning configurato.
    Se non esiste un record, si usa il default del tipo.

    visible_to_areas: lista di aree/reparti operativi (es. ['magazzino', 'produzione']).
    """

    __tablename__ = "core_warning_type_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warning_type: Mapped[str] = mapped_column(String(64), nullable=False)
    visible_to_areas: Mapped[list] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("warning_type", name="uq_core_warning_type_config_type"),
    )
