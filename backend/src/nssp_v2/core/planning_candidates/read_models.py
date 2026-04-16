"""
Read model Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-065, TASK-V2-069,
TASK-V2-071, TASK-V2-074, TASK-V2-085, TASK-V2-100, DL-ARCH-V2-025, DL-ARCH-V2-027,
DL-ARCH-V2-028, DL-ARCH-V2-030, DL-ARCH-V2-031).

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
  by_article (V1 retrocompatibile + stock policy V1 — TASK-V2-085):
    - popola: availability_qty, customer_open_demand_qty, incoming_supply_qty, future_availability_qty
    - popola (solo se stock policy configurata):
        customer_shortage_qty, stock_replenishment_qty, required_qty_total
    - lascia None: order_reference, line_reference, line_open_demand_qty,
                   linked_incoming_supply_qty, line_future_coverage_qty,
                   order_line_description

  by_customer_order_line (V2 — TASK-V2-071):
    - popola: order_reference, line_reference, line_open_demand_qty,
              linked_incoming_supply_qty, line_future_coverage_qty,
              order_line_description (descrizione dalla riga ordine — DL-ARCH-V2-028 §2)
    - lascia None: availability_qty, customer_open_demand_qty, incoming_supply_qty,
                   future_availability_qty, customer_shortage_qty, stock_replenishment_qty,
                   required_qty_total

Reason codes:
  future_availability_negative  — fav < 0 (shortage cliente — con o senza stock policy)
  stock_below_trigger           — fav >= 0 ma fav < trigger_stock_qty (solo scorta)
  line_demand_uncovered         — by_customer_order_line
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nssp_v2.core.planning_mode import PlanningMode


class PlanningCandidateActiveWarning(BaseModel):
    """Forma minima warning esposta nel contratto Planning Candidates."""

    model_config = ConfigDict(frozen=True)

    code: str
    severity: str
    message: str


class PlanningCandidateItem(BaseModel):
    """Planning candidate — by_article (V1) o by_customer_order_line (V2).

    Campi comuni a entrambe le modalita:
    - article_code, display_label, famiglia_*, effective_*, planning_mode
    - reason_code, reason_text: spiegazione esplicita del candidate (DL-ARCH-V2-028 §4)
    - misura: unita di misura / misura articolo (DL-ARCH-V2-028 §3)
    - required_qty_minimum: minima quantita coerente col driver primario
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
    source_candidate_id: str
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
    description_parts: list[str] = Field(default_factory=list)
    display_description: str
    active_warning_codes: list[str] = Field(default_factory=list)
    active_warnings: list[PlanningCandidateActiveWarning] = Field(default_factory=list)
    # Misura (DL-ARCH-V2-028 §3)
    misura: str | None = None
    required_qty_minimum: Decimal
    # Driver primario unico per filtri UI:
    # - customer: shortage cliente > 0 (precedenza anche nei casi misti)
    # - stock: solo componente scorta attiva
    primary_driver: Literal["customer", "stock"] | None = None
    requested_destination_display: str | None = None
    computed_at: datetime

    # ─── by_article (None per by_customer_order_line) ─────────────────────────
    availability_qty: Decimal | None = None
    customer_open_demand_qty: Decimal | None = None
    incoming_supply_qty: Decimal | None = None
    future_availability_qty: Decimal | None = None

    # ─── by_article con stock policy V1 (TASK-V2-085, DL-ARCH-V2-030 §9) ─────
    # None se l'articolo non ha stock policy configurata (target/trigger assenti).
    # customer_shortage_qty = max(-future_availability_qty, 0)
    # stock_replenishment_qty = max(target_stock_qty - max(stock_horizon_availability_qty, 0), 0)
    # required_qty_total = customer_shortage_qty + stock_replenishment_qty
    customer_shortage_qty: Decimal | None = None
    stock_replenishment_qty: Decimal | None = None
    required_qty_total: Decimal | None = None

    # ─── by_article customer horizon (TASK-V2-100, DL-ARCH-V2-031 §3) ──────
    # True  se la data_consegna piu vicina delle righe ordine <= today + customer_horizon_days.
    # False se la data_consegna piu vicina e oltre l'orizzonte.
    # None  se nessuna riga ordine per questo articolo ha expected_delivery_date valorizzata.
    # Sempre None per by_customer_order_line (il flag appartiene al ramo by_article).
    is_within_customer_horizon: bool | None = None
    earliest_customer_delivery_date: date | None = None
    # Data_consegna piu vicina tra le righe ordine — None se nessuna data o by_customer_order_line.
    # Esposta per consentire alla UI di applicare un orizzonte configurabile (TASK-V2-102).
    nearest_delivery_date: date | None = None

    # ─── Release now contract — by_article only (TASK-V2-128) ────────────────
    # None per by_customer_order_line; None per by_article senza capacity configurata.
    # required_qty_eventual = required_qty_total (alias esplicito del contratto release)
    # capacity_headroom_now_qty = max(capacity_effective_qty - inventory_qty, 0)
    # release_qty_now_max = min(required_qty_eventual, capacity_headroom_now_qty)
    # release_status: launchable_now | launchable_partially | blocked_by_capacity_now
    required_qty_eventual: Decimal | None = None
    capacity_headroom_now_qty: Decimal | None = None
    release_qty_now_max: Decimal | None = None
    release_status: Literal["launchable_now", "launchable_partially", "blocked_by_capacity_now"] | None = None

    # ─── by_customer_order_line (None per by_article) ─────────────────────────
    order_reference: str | None = None
    line_reference: int | None = None
    # Descrizione dalla riga ordine (DL-ARCH-V2-028 §2) — None per by_article
    order_line_description: str | None = None
    full_order_line_description: str | None = None
    requested_delivery_date: date | None = None
    line_open_demand_qty: Decimal | None = None
    linked_incoming_supply_qty: Decimal | None = None
    line_future_coverage_qty: Decimal | None = None
