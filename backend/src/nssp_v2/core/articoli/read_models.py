"""
Read model Core slice `articoli` (DL-ARCH-V2-013, DL-ARCH-V2-014).

Regole:
- i read model sono frozen (immutabili): la UI non puo modificarli
- i dati Easy provengono da sync_articoli via query Core
- i dati interni (famiglia) provengono da articolo_famiglie / core_articolo_config
- il Core e il solo contratto ammesso tra sync e UI
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ArticoloItem(BaseModel):
    """Riga di lista articoli — popola la colonna sinistra della UI.

    Campi minimi per identificazione rapida e ricerca (DL-ARCH-V2-013 §5.1).
    Famiglia interna aggiunta (DL-ARCH-V2-014 §5).
    """

    model_config = ConfigDict(frozen=True)

    # Identificatore tecnico
    codice_articolo: str

    # Descrizioni (da ART_DES1 / ART_DES2)
    descrizione_1: str | None
    descrizione_2: str | None

    # Unita di misura
    unita_misura_codice: str | None

    # Campo sintetico di presentazione (DL-ARCH-V2-013 §6)
    display_label: str

    # Famiglia articolo interna (DL-ARCH-V2-014) — nullable nel primo slice
    famiglia_code: str | None
    famiglia_label: str | None


class ArticoloDetail(BaseModel):
    """Dettaglio completo di un articolo — popola la colonna destra della UI.

    Dati Easy da sync_articoli + dati interni V2 (DL-ARCH-V2-014 §5).
    """

    model_config = ConfigDict(frozen=True)

    # Identificatore tecnico
    codice_articolo: str

    # Descrizioni
    descrizione_1: str | None
    descrizione_2: str | None

    # Unita di misura
    unita_misura_codice: str | None

    # Data ultima modifica lato sorgente
    source_modified_at: datetime | None

    # Categoria
    categoria_articolo_1: str | None

    # Materiale grezzo per produzione
    materiale_grezzo_codice: str | None
    quantita_materiale_grezzo_occorrente: Decimal | None
    quantita_materiale_grezzo_scarto: Decimal | None

    # Attributi articolo
    misura_articolo: str | None
    codice_immagine: str | None
    contenitori_magazzino: str | None
    peso_grammi: Decimal | None

    # Campo sintetico di presentazione (DL-ARCH-V2-013 §6)
    display_label: str

    # Famiglia articolo interna (DL-ARCH-V2-014) — nullable nel primo slice
    famiglia_code: str | None
    famiglia_label: str | None


class FamigliaItem(BaseModel):
    """Voce del catalogo famiglie articolo.

    Usata dall'endpoint GET /api/produzione/famiglie.
    """

    model_config = ConfigDict(frozen=True)

    code: str
    label: str
    sort_order: int | None
