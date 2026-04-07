"""
Read model del Core slice `clienti + destinazioni` (DL-ARCH-V2-010, DL-ARCH-V2-012).

I read model espongono:
- dati Easy read-only (provenienti da sync_clienti / sync_destinazioni)
- dati interni configurabili (provenienti da core_destinazione_config)
- flag is_primary: True per la destinazione principale derivata da ANACLI (DL-ARCH-V2-012)

La distinzione tra principale e aggiuntive e esplicita nel read model (DL-ARCH-V2-012 §2).
"""

from pydantic import BaseModel, ConfigDict


# ─── Lista clienti (§6.1) ─────────────────────────────────────────────────────

class ClienteItem(BaseModel):
    """Rappresentazione minimale del cliente per la navigazione."""

    model_config = ConfigDict(frozen=True)

    # Dati Easy read-only
    codice_cli: str
    ragione_sociale: str


# ─── Lista destinazioni per cliente (§6.2) ───────────────────────────────────

class DestinazioneItem(BaseModel):
    """Riga della colonna centrale — destinazioni del cliente selezionato.

    Unifica destinazione principale (derivata da sync_clienti) e destinazioni
    aggiuntive (derivate da sync_destinazioni). Il flag is_primary distingue
    esplicitamente i due tipi (DL-ARCH-V2-012 §2).
    """

    model_config = ConfigDict(frozen=True)

    # Dati Easy read-only
    codice_destinazione: str
    codice_cli: str | None
    numero_progressivo_cliente: str | None
    indirizzo: str | None
    citta: str | None
    provincia: str | None

    # Dato interno configurabile (Core)
    nickname_destinazione: str | None

    # Campo sintetico derivato dal Core: nickname > fallback > codice
    display_label: str

    # True se destinazione principale derivata da ANACLI (DL-ARCH-V2-012 §1)
    is_primary: bool


# ─── Dettaglio destinazione (§6.3) ───────────────────────────────────────────

class DestinazioneDetail(BaseModel):
    """Scheda completa della destinazione selezionata (colonna destra).

    Valida sia per la principale (is_primary=True) sia per le aggiuntive.
    """

    model_config = ConfigDict(frozen=True)

    # Dati Easy read-only — destinazione
    codice_destinazione: str
    codice_cli: str | None
    numero_progressivo_cliente: str | None
    indirizzo: str | None
    citta: str | None
    provincia: str | None
    nazione_codice: str | None
    telefono_1: str | None

    # Dato Easy read-only — denormalizzato da cliente (join)
    ragione_sociale_cliente: str | None

    # Dato interno configurabile (Core)
    nickname_destinazione: str | None

    # Campo sintetico derivato dal Core
    display_label: str

    # True se destinazione principale derivata da ANACLI (DL-ARCH-V2-012 §1)
    is_primary: bool
