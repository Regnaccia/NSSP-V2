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

from pydantic import BaseModel, ConfigDict, Field

from nssp_v2.core.planning_mode import PlanningMode


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

    # Planning policy effettive (DL-ARCH-V2-026 §Effective policy, TASK-V2-064):
    #   override articolo se valorizzato, altrimenti default famiglia.
    #   None se l'articolo non ha famiglia e non ha override (valore indefinito).
    effective_considera_in_produzione: bool | None = None
    effective_aggrega_codice_in_produzione: bool | None = None


class ArticoloDetail(BaseModel):
    """Dettaglio completo di un articolo — popola la colonna destra della UI.

    Dati Easy da sync_articoli + dati interni V2 (DL-ARCH-V2-014 §5).
    Giacenza calcolata da core_inventory_positions (DL-ARCH-V2-016, TASK-V2-038).
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

    # Planning policy effettive (DL-ARCH-V2-026 §Effective policy, TASK-V2-064):
    #   override articolo se valorizzato, altrimenti default famiglia.
    #   None se l'articolo non ha famiglia e non ha override (valore indefinito).
    effective_considera_in_produzione: bool | None = None
    effective_aggrega_codice_in_produzione: bool | None = None

    # Override articolo per planning policy (DL-ARCH-V2-026, TASK-V2-067):
    #   None = eredita il default di famiglia; True/False = sovrascrive.
    override_considera_in_produzione: bool | None = None
    override_aggrega_codice_in_produzione: bool | None = None

    # Vocabolario planning_mode (DL-ARCH-V2-027, TASK-V2-069):
    #   derivato da effective_aggrega_codice_in_produzione via resolve_planning_mode.
    planning_mode: PlanningMode | None = None

    # Giacenza canonica (DL-ARCH-V2-016, TASK-V2-038) — None se nessun movimento registrato
    on_hand_qty: Decimal | None = None
    giacenza_computed_at: datetime | None = None

    # Quota appartata per cliente (DL-ARCH-V2-019, TASK-V2-044) — None se nessuna quota appartata
    customer_set_aside_qty: Decimal | None = None
    set_aside_computed_at: datetime | None = None

    # Impegni totali per articolo (DL-ARCH-V2-017, TASK-V2-050) — None se nessun impegno
    committed_qty: Decimal | None = None
    commitments_computed_at: datetime | None = None

    # Disponibilita canonica (DL-ARCH-V2-021, TASK-V2-050) — None se fact non ancora calcolato
    availability_qty: Decimal | None = None
    availability_computed_at: datetime | None = None

    # Stock policy effettiva V1 (DL-ARCH-V2-030, TASK-V2-083):
    #   override articolo se presente, altrimenti default famiglia.
    #   None se nessun valore configurato a nessun livello.
    #   Significativi solo per planning_mode = by_article.
    effective_stock_months: Decimal | None = None
    effective_stock_trigger_months: Decimal | None = None

    # Override stock policy articolo-specifici (DL-ARCH-V2-030, TASK-V2-089):
    #   None = eredita il default di famiglia; valore = sovrascrive.
    override_stock_months: Decimal | None = None
    override_stock_trigger_months: Decimal | None = None

    # Capacity override articolo-specifica (DL-ARCH-V2-030, TASK-V2-083):
    #   nessun default famiglia — proprieta dell'articolo.
    capacity_override_qty: Decimal | None = None

    # Gestione scorte attiva — effective value e override articolo (TASK-V2-096, TASK-V2-098):
    #   effective: override articolo se valorizzato, altrimenti default famiglia.
    #   None se l'articolo non ha famiglia e non ha override.
    effective_gestione_scorte_attiva: bool | None = None
    override_gestione_scorte_attiva: bool | None = None

    # Metriche stock calcolate — sola lettura (TASK-V2-084, TASK-V2-089):
    #   None se l'articolo non ha planning_mode = by_article o dati insufficienti.
    monthly_stock_base_qty: Decimal | None = None
    capacity_calculated_qty: Decimal | None = None
    capacity_effective_qty: Decimal | None = None
    target_stock_qty: Decimal | None = None
    trigger_stock_qty: Decimal | None = None
    stock_computed_at: datetime | None = None
    stock_strategy_key: str | None = None

    # Proposal logic articolo-specifica (V1).
    effective_proposal_logic_key: str | None = None
    proposal_logic_key: str | None = None
    proposal_logic_article_params: dict = Field(default_factory=dict)

    # Lunghezza barra grezza articolo-specifica (TASK-V2-118, DL-ARCH-V2-035).
    # None se non configurata. Esposta indipendentemente dal flag famiglia.
    raw_bar_length_mm: Decimal | None = None


class FamigliaItem(BaseModel):
    """Voce del catalogo famiglie articolo.

    Usata dall'endpoint GET /api/produzione/famiglie (picker — solo attive).
    """

    model_config = ConfigDict(frozen=True)

    code: str
    label: str
    sort_order: int | None
    # Flag abilitazione configurazione campo barra (TASK-V2-123, DL-ARCH-V2-035)
    raw_bar_length_mm_enabled: bool = False


class FamigliaRow(BaseModel):
    """Riga della tabella di gestione famiglie articolo.

    Usata dall'endpoint GET /api/produzione/famiglie/catalog (tutte, con conteggio).
    """

    model_config = ConfigDict(frozen=True)

    code: str
    label: str
    sort_order: int | None
    is_active: bool
    considera_in_produzione: bool
    aggrega_codice_in_produzione: bool
    n_articoli: int

    # Stock policy defaults V1 (DL-ARCH-V2-030, TASK-V2-083)
    stock_months: Decimal | None = None
    stock_trigger_months: Decimal | None = None

    # Flag esplicito di applicabilita stock policy (TASK-V2-096)
    gestione_scorte_attiva: bool = False

    # Flag abilitazione configurazione lunghezza barra grezza (TASK-V2-118, DL-ARCH-V2-035)
    raw_bar_length_mm_enabled: bool = False
