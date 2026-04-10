"""
Read model Core slice `planning_candidates` V1 (TASK-V2-062, TASK-V2-065, DL-ARCH-V2-025).

Regole:
- i read model sono frozen (immutabili)
- i dati quantitativi provengono da core_availability + sync_produzioni_attive + sync_righe_ordine_cliente
- i dati di presentazione provengono da sync_articoli + core_articolo_config + articolo_famiglie
- la logica di candidatura e applicata nel layer Core, non nella UI
- effective policy (TASK-V2-064) incluse per consentire il filtro solo_in_produzione lato UI
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PlanningCandidateItem(BaseModel):
    """Articolo planning candidate V1: future_availability_qty < 0.

    Un articolo e candidate se anche dopo aver conteggiato la supply gia in corso
    (produzioni attive) la copertura futura resta negativa.

    Campi quantitativi:
    - availability_qty: quota libera attuale (core_availability)
    - customer_open_demand_qty: domanda cliente aperta aggregata per articolo
    - incoming_supply_qty: supply aggregata da produzioni attive per articolo
    - future_availability_qty: availability_qty + incoming_supply_qty (puo essere negativa)
    - required_qty_minimum: abs(future_availability_qty) quando < 0, altrimenti 0

    Campi di presentazione (TASK-V2-065):
    - display_label: campo sintetico di presentazione (DL-ARCH-V2-013 §6)
    - famiglia_code / famiglia_label: nullable se articolo senza famiglia

    Planning policy effettive (DL-ARCH-V2-026, TASK-V2-064):
    - effective_considera_in_produzione: usata dalla UI per il toggle solo_in_produzione
    - effective_aggrega_codice_in_produzione: esposta per uso futuro

    computed_at: timestamp del computed fact availability piu recente per l'articolo.
    """

    model_config = ConfigDict(frozen=True)

    article_code: str

    # Campi di presentazione
    display_label: str
    famiglia_code: str | None
    famiglia_label: str | None

    # Planning policy effettive (DL-ARCH-V2-026)
    effective_considera_in_produzione: bool | None
    effective_aggrega_codice_in_produzione: bool | None

    # Campi quantitativi
    availability_qty: Decimal
    customer_open_demand_qty: Decimal
    incoming_supply_qty: Decimal
    future_availability_qty: Decimal
    required_qty_minimum: Decimal
    computed_at: datetime
