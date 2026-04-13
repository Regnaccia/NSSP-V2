"""
Read model Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-065, TASK-V2-069,
TASK-V2-071, TASK-V2-074, DL-ARCH-V2-025, DL-ARCH-V2-027, DL-ARCH-V2-028).

Regole:
- i read model sono frozen (immutabili)
- il branching by_article / by_customer_order_line e determinato da planning_mode
- i campi quantitativi dipendono dalla modalita; i campi dell'altra modalita sono None
- la logica di candidatura e applicata nel layer Core, non nella UI
- effective policy (TASK-V2-064) incluse per consentire il filtro solo_in_produzione lato UI
- planning_mode (TASK-V2-069, DL-ARCH-V2-027): vocabolario esplicito derivato da
  effective_aggrega_codice_in_produzione
- reason_code / reason_text (TASK-V2-074, DL-ARCH-V2-028): spiegazione esplicita del candidate
- stock_effective (TASK-V2-074, DL-ARCH-V2-028): clamp max(on_hand, 0) applicato prima
  del calcolo planning — availability_qty riflette il valore clamped usato nella logica

Branching:
  by_article (V1 retrocompatibile):
    - popola: availability_qty, customer_open_demand_qty, incoming_supply_qty, future_availability_qty
    - lascia None: order_reference, line_reference, line_open_demand_qty,
                   linked_incoming_supply_qty, line_future_coverage_qty,
                   order_line_description

  by_customer_order_line (V2 — TASK-V2-071):
    - popola: order_reference, line_reference, line_open_demand_qty,
              linked_incoming_supply_qty, line_future_coverage_qty,
              order_line_description (descrizione dalla riga ordine — DL-ARCH-V2-028 §2)
    - lascia None: availability_qty, customer_open_demand_qty, incoming_supply_qty,
                   future_availability_qty (non usabile in modo non ambiguo in questa modalita)
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from nssp_v2.core.planning_mode import PlanningMode


class PlanningCandidateItem(BaseModel):
    """Planning candidate — by_article (V1) o by_customer_order_line (V2).

    Campi comuni a entrambe le modalita:
    - article_code, display_label, famiglia_*, effective_*, planning_mode
    - reason_code, reason_text: spiegazione esplicita del candidate (DL-ARCH-V2-028 §4)
    - misura: unita di misura / misura articolo (DL-ARCH-V2-028 §3)
    - required_qty_minimum: scopertura minima (abs del deficit, in entrambe le modalita)
    - computed_at: availability.computed_at per by_article, synced_at riga per by_customer_order_line

    Campi by_article (None per by_customer_order_line):
    - availability_qty: quota libera effettiva = max(on_hand,0) - set_aside - committed
      (nota: usa stock_effective per il clamp DL-ARCH-V2-028, non il valore raw di CoreAvailability)
    - customer_open_demand_qty: domanda cliente aggregata per articolo
    - incoming_supply_qty: supply aggregata da produzioni attive per articolo
    - future_availability_qty: availability_qty + incoming_supply_qty

    Campi by_customer_order_line (None per by_article):
    - order_reference: numero ordine cliente (DOC_NUM)
    - line_reference: numero riga ordine (NUM_PROGR)
    - order_line_description: descrizione dalla riga ordine cliente (DL-ARCH-V2-028 §2)
    - line_open_demand_qty: max(ordered - set_aside - fulfilled, 0) per la riga
    - linked_incoming_supply_qty: supply da produzioni collegate a questa riga ordine
    - line_future_coverage_qty: linked_incoming_supply_qty - line_open_demand_qty
    """

    model_config = ConfigDict(frozen=True)

    # ─── Comuni ───────────────────────────────────────────────────────────────
    article_code: str
    display_label: str
    famiglia_code: str | None
    famiglia_label: str | None
    effective_considera_in_produzione: bool | None
    effective_aggrega_codice_in_produzione: bool | None
    planning_mode: PlanningMode | None
    # Reason esplicita (DL-ARCH-V2-028 §4) — sempre valorizzata
    reason_code: str
    reason_text: str
    # Misura (DL-ARCH-V2-028 §3)
    misura: str | None = None
    required_qty_minimum: Decimal
    computed_at: datetime

    # ─── by_article (None per by_customer_order_line) ─────────────────────────
    availability_qty: Decimal | None = None
    customer_open_demand_qty: Decimal | None = None
    incoming_supply_qty: Decimal | None = None
    future_availability_qty: Decimal | None = None

    # ─── by_customer_order_line (None per by_article) ─────────────────────────
    order_reference: str | None = None
    line_reference: int | None = None
    # Descrizione dalla riga ordine (DL-ARCH-V2-028 §2) — None per by_article
    order_line_description: str | None = None
    line_open_demand_qty: Decimal | None = None
    linked_incoming_supply_qty: Decimal | None = None
    line_future_coverage_qty: Decimal | None = None
