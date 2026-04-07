"""
Modello Core per la configurazione interna della destinazione (DL-ARCH-V2-010 §4).

Ownership: Core layer — non scritto mai dal layer sync.

Tabelle:
- core_destinazione_config: dati interni configurabili per destinazione
  - identita: codice_destinazione (stessa source identity del layer sync)
  - primo dato interno: nickname_destinazione
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreDestinazioneConfig(Base):
    """Configurazione interna per una destinazione.

    Keyed su `codice_destinazione` — stessa source identity del layer sync.
    Nessuna FK hard verso sync_destinazioni (decoupling intenzionale).

    Dati interni (non provengono da Easy, non scritti nel layer sync):
    - nickname_destinazione: nome leggibile per la destinazione
    """

    __tablename__ = "core_destinazione_config"

    codice_destinazione: Mapped[str] = mapped_column(
        String(32), primary_key=True
    )
    nickname_destinazione: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
