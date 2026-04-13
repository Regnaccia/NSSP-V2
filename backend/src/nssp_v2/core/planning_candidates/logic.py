"""
Logiche di dominio Core slice `planning_candidates` (TASK-V2-062, TASK-V2-071, DL-ARCH-V2-025, DL-ARCH-V2-027).

Struttura:
- PlanningContext: contesto per la logica by_article (V1)
- PlanningContextOrderLine: contesto per la logica by_customer_order_line (V2)
- future_availability_v1: copertura futura per by_article
- required_qty_minimum_v1: scopertura minima by_article
- is_planning_candidate_v1: candidatura by_article (future_availability_qty < 0)
- line_future_coverage_v2: copertura futura per by_customer_order_line
- required_qty_minimum_by_order_line: scopertura minima by_customer_order_line
- is_planning_candidate_by_order_line: candidatura by_customer_order_line (line_future_coverage_qty < 0)

Regole:
- by_article: future_availability_qty = availability_qty + incoming_supply_qty < 0
- by_customer_order_line: line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty < 0
- le due logiche sono indipendenti e non si mischiano
- la logica e separata e testabile in isolamento (DL-ARCH-V2-023)
"""

from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanningContext:
    """Contesto di fact canonici e aggregati passato alla logica planning by_article (V1).

    article_code: codice canonico dell'articolo (strip().upper()).
    availability_qty: quota libera attuale (CoreAvailability). None se non ancora calcolata.
    incoming_supply_qty: supply aggregata da produzioni attive per articolo (>= 0).
    customer_open_demand_qty: domanda cliente aperta aggregata per articolo (>= 0).
    """

    article_code: str
    availability_qty: Decimal | None
    incoming_supply_qty: Decimal
    customer_open_demand_qty: Decimal


@dataclass(frozen=True)
class PlanningContextOrderLine:
    """Contesto per la logica planning by_customer_order_line (TASK-V2-071, DL-ARCH-V2-027).

    article_code: codice canonico dell'articolo (strip().upper()).
    order_reference: numero ordine cliente (DOC_NUM in sync_righe_ordine_cliente).
    line_reference: numero riga ordine cliente (NUM_PROGR).
    line_open_demand_qty: max(ordered_qty - set_aside_qty - fulfilled_qty, 0).
    linked_incoming_supply_qty: supply da produzioni collegate alla stessa riga ordine (>= 0).
    """

    article_code: str
    order_reference: str
    line_reference: int
    line_open_demand_qty: Decimal
    linked_incoming_supply_qty: Decimal


def future_availability_v1(ctx: PlanningContext) -> Decimal | None:
    """Copertura futura semplice V1 (DL-ARCH-V2-025 §3).

    Formula: future_availability_qty = availability_qty + incoming_supply_qty

    Restituisce None se availability_qty non e ancora disponibile.
    """
    if ctx.availability_qty is None:
        return None
    return ctx.availability_qty + ctx.incoming_supply_qty


def required_qty_minimum_v1(future_availability_qty: Decimal | None) -> Decimal:
    """Scopertura minima quando la copertura futura e negativa (DL-ARCH-V2-025 §Required Quantity).

    Formula: abs(future_availability_qty) se < 0, altrimenti 0.

    Non e ancora quantita produttiva finale: non include lotti, policy o arrotondamenti.
    """
    if future_availability_qty is None or future_availability_qty >= Decimal("0"):
        return Decimal("0")
    return abs(future_availability_qty)


def is_planning_candidate_v1(ctx: PlanningContext) -> bool:
    """Logica V1: un articolo e un planning candidate se future_availability_qty < 0.

    Un articolo resta candidate solo se anche dopo la supply gia in corso (produzioni attive)
    la copertura futura e ancora negativa. Articoli gia coperti dalla supply non sono candidate.

    Restituisce False se availability_qty non e ancora disponibile (None).

    Questa funzione e intercambiabile (DL-ARCH-V2-023 §Regola 3):
    in futuro potra essere sostituita con logica piu ricca (horizon, scoring, policy
    per famiglia) senza modificare i fact canonici.
    """
    fav = future_availability_v1(ctx)
    if fav is None:
        return False
    return fav < Decimal("0")


# ─── Logica by_customer_order_line (TASK-V2-071, DL-ARCH-V2-027) ─────────────

def line_future_coverage_v2(ctx: PlanningContextOrderLine) -> Decimal:
    """Copertura futura per riga ordine cliente (by_customer_order_line).

    Formula: line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty

    Positivo o zero: la riga e gia coperta dalla supply collegata.
    Negativo: la riga richiede nuova attenzione produttiva.

    Non usa availability_qty: la modalita e commessa/riga-oriented, non stock-oriented
    (DL-ARCH-V2-027 §by_customer_order_line - Availability).
    """
    return ctx.linked_incoming_supply_qty - ctx.line_open_demand_qty


def is_planning_candidate_by_order_line(ctx: PlanningContextOrderLine) -> bool:
    """Candidatura by_customer_order_line: line_future_coverage_qty < 0.

    Una riga ordine e candidate se la supply gia collegata non copre la domanda aperta.
    """
    return line_future_coverage_v2(ctx) < Decimal("0")


def required_qty_minimum_by_order_line(line_future_coverage_qty: Decimal) -> Decimal:
    """Scopertura minima per riga ordine cliente.

    Formula: abs(line_future_coverage_qty) se < 0, altrimenti 0.
    """
    if line_future_coverage_qty >= Decimal("0"):
        return Decimal("0")
    return abs(line_future_coverage_qty)
