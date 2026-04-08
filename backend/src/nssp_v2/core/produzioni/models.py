"""
Modelli SQLAlchemy per i dati interni del Core slice `produzioni` (DL-ARCH-V2-015).

Tabelle:
- core_produzione_override: override manuali interni (forza_completata) per produzione

Ownership: Core layer — nessun dato qui viene scritto dal layer sync.
Il flag forza_completata non retroagisce mai sui mirror sync ne sulla sorgente Easy.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreProduzioneOverride(Base):
    """Override interno per una singola produzione.

    PK composita: (id_dettaglio, bucket) — necessaria per distinguere record con
    lo stesso id_dettaglio provenienti da DPRE_PROD (active) o SDPRE_PROD (historical).

    Nessuna FK verso i mirror sync: il Core mantiene indipendenza dal layer sync.

    forza_completata: se True, stato_produzione = "completata" indipendentemente
                     dalle quantita. Usato per gestire dati sporchi noti in Easy.
    """

    __tablename__ = "core_produzione_override"

    id_dettaglio: Mapped[int] = mapped_column(primary_key=True)
    bucket: Mapped[str] = mapped_column(String(16), primary_key=True)
    forza_completata: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
