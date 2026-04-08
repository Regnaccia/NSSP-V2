"""
Read model Core slice `produzioni` (DL-ARCH-V2-015).

Regole:
- i read model sono frozen (immutabili): la UI non puo modificarli
- i dati Easy provengono da sync_produzioni_attive / sync_produzioni_storiche via query Core
- l'override interno (forza_completata) proviene da core_produzione_override
- il Core e il solo contratto ammesso tra sync e UI
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProduzioneItem(BaseModel):
    """Read model unificato di una produzione (DL-ARCH-V2-015).

    Aggrega attive e storiche con bucket esplicito e stato computato.
    """

    model_config = ConfigDict(frozen=True)

    # Identita tecnica
    id_dettaglio: int

    # Bucket applicativo — deriva dalla sorgente sync
    bucket: Literal["active", "historical"]

    # Cliente
    cliente_ragione_sociale: str | None

    # Articolo
    codice_articolo: str | None
    descrizione_articolo: str | None

    # Documento
    numero_documento: str | None
    numero_riga_documento: int | None

    # Quantita
    quantita_ordinata: Decimal | None
    quantita_prodotta: Decimal | None

    # Computed fact (DL-ARCH-V2-015 §3-§5)
    stato_produzione: Literal["attiva", "completata"]

    # Override interno
    forza_completata: bool


class ProduzioniPaginata(BaseModel):
    """Risposta paginata della lista produzioni (TASK-V2-034).

    Contratto API per GET /produzione/produzioni con filtro bucket e paginazione.
    """

    model_config = ConfigDict(frozen=True)

    items: list[ProduzioneItem]
    total: int
    limit: int
    offset: int
