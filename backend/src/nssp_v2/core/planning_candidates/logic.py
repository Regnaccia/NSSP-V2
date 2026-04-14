"""
Logiche di dominio Core slice `planning_candidates` (TASK-V2-062, TASK-V2-071, TASK-V2-074,
TASK-V2-085, TASK-V2-101, DL-ARCH-V2-025, DL-ARCH-V2-027, DL-ARCH-V2-028, DL-ARCH-V2-030,
DL-ARCH-V2-031).

Struttura:
- PlanningContext: contesto per la logica by_article (V1)
- PlanningContextOrderLine: contesto per la logica by_customer_order_line (V2)
- effective_stock: clamp giacenza fisica a 0 (DL-ARCH-V2-028)
- future_availability_v1: copertura futura per by_article (usa stock_effective)
- required_qty_minimum_v1: scopertura minima by_article (customer shortage)
- is_planning_candidate_v1: candidatura by_article (future_availability_qty < 0)
- is_planning_candidate_with_stock_v1: candidatura by_article con stock policy (TASK-V2-085)
- customer_shortage_qty_v1: componente shortage cliente del breakdown (TASK-V2-085)
- stock_replenishment_qty_v1: componente replenishment scorta del breakdown (TASK-V2-085)
- required_qty_total_v1: somma shortage + replenishment (TASK-V2-085)
- line_future_coverage_v2: copertura futura per by_customer_order_line
- required_qty_minimum_by_order_line: scopertura minima by_customer_order_line
- is_planning_candidate_by_order_line: candidatura by_customer_order_line (line_future_coverage_qty < 0)

Regole:
- by_article: stock_effective = max(on_hand, 0); future_availability_qty = availability_qty + incoming_supply_qty < 0
- by_article con stock policy (TASK-V2-085, DL-ARCH-V2-030 §9):
    candidate se fav < 0 (shortage cliente) OPPURE fav < trigger_stock_qty (trigger scorta)
    customer_shortage_qty = max(-fav, 0)
    stock_replenishment_qty = max(target_stock_qty - max(fav, 0), 0)   se target configurato
    required_qty_total = customer_shortage_qty + stock_replenishment_qty
    un solo candidate per articolo — breakdown separato tra shortage e replenishment
- by_customer_order_line: line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty < 0
- le due logiche sono indipendenti e non si mischiano
- la logica e separata e testabile in isolamento (DL-ARCH-V2-023)
- la sola giacenza negativa senza domanda non genera candidate (DL-ARCH-V2-028)
"""

from decimal import Decimal
from dataclasses import dataclass
from typing import Literal


PrimaryDriver = Literal["customer", "stock"]


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


def effective_stock(inventory_qty: Decimal | None) -> Decimal:
    """Giacenza fisica effettiva per il planning (DL-ARCH-V2-028 §1).

    Formula: max(inventory_qty, 0)

    La giacenza fisica negativa e un'anomalia inventariale, non un fabbisogno produttivo.
    Il clamp a zero impedisce che anomalie dati (movimenti fantasma, rettifiche non
    ancora sincronizzate) generino candidate fittizi.

    Il valore raw (stock_calculated) rimane disponibile nel layer di persistenza
    per diagnostica e futura gestione nel modulo Warnings.
    """
    raw = inventory_qty if inventory_qty is not None else Decimal("0")
    return raw if raw > Decimal("0") else Decimal("0")


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


# ─── Logica by_article con stock policy (TASK-V2-085, DL-ARCH-V2-030 §9) ─────

def is_planning_candidate_with_stock_v1(
    future_availability_qty: Decimal | None,
    trigger_stock_qty: Decimal | None,
) -> bool:
    """Candidatura by_article estesa con stock policy V1 (TASK-V2-085).

    Un articolo e candidate se:
    - future_availability_qty < 0 (shortage cliente), OPPURE
    - trigger_stock_qty is not None AND future_availability_qty < trigger_stock_qty

    Se trigger_stock_qty e None (nessuna config stock), comportamento identico
    a is_planning_candidate_v1 (solo fav < 0).

    Restituisce False se future_availability_qty is None.
    """
    if future_availability_qty is None:
        return False
    if future_availability_qty < Decimal("0"):
        return True
    if trigger_stock_qty is not None and future_availability_qty < trigger_stock_qty:
        return True
    return False


def customer_shortage_qty_v1(future_availability_qty: Decimal) -> Decimal:
    """Componente shortage cliente del breakdown stock-driven (DL-ARCH-V2-030 §9).

    Formula: max(-future_availability_qty, 0)

    Zero se la disponibilita futura e positiva (il cliente e gia coperto).
    """
    return max(-future_availability_qty, Decimal("0"))


def stock_replenishment_qty_v1(
    target_stock_qty: Decimal | None,
    future_availability_qty: Decimal,
) -> Decimal | None:
    """Componente replenishment scorta del breakdown stock-driven (DL-ARCH-V2-030 §9).

    Formula: max(target_stock_qty - max(future_availability_qty, 0), 0)

    Restituisce None se target_stock_qty non e configurato (no stock policy).
    Il clamp max(fav, 0) evita il doppio conteggio con customer_shortage_qty:
    se fav e negativo (gia in shortage), la quota shortage e gia coperta dalla
    componente cliente; il replenishment parte da disponibilita effettiva = 0.
    """
    if target_stock_qty is None:
        return None
    effective_fav = max(future_availability_qty, Decimal("0"))
    return max(target_stock_qty - effective_fav, Decimal("0"))


def stock_horizon_availability_qty_v1(
    stock_effective: Decimal,
    customer_set_aside_qty: Decimal,
    capped_commitments_qty: Decimal,
    incoming_supply_qty: Decimal,
) -> Decimal:
    """Disponibilita orizzonata per la componente scorta (TASK-V2-101, DL-ARCH-V2-031 §4).

    Formula:
        stock_horizon_availability_qty =
            stock_effective - customer_set_aside_qty - capped_commitments_qty + incoming_supply_qty

    Usata SOLO nel calcolo di stock_replenishment_qty:
        stock_replenishment_qty = max(target - max(stock_horizon_avail, 0), 0)

    La componente customer-driven (customer_shortage_qty) continua a usare
    future_availability_qty (full commitments), invariata.

    Il capping riduce i commitments contati agli impegni con data_consegna
    entro il look-ahead stock (today + effective_stock_months), evitando che
    la scorta reagisca a ordini troppo lontani nel tempo.
    """
    return stock_effective - customer_set_aside_qty - capped_commitments_qty + incoming_supply_qty


def required_qty_total_v1(
    shortage_qty: Decimal,
    replenishment_qty: Decimal | None,
) -> Decimal:
    """Quantita totale richiesta = shortage cliente + replenishment scorta (DL-ARCH-V2-030 §9).

    Se replenishment_qty e None (no stock policy) restituisce solo shortage_qty.
    """
    return shortage_qty + (replenishment_qty if replenishment_qty is not None else Decimal("0"))


def resolve_primary_driver_v1(
    customer_shortage_qty: Decimal,
    stock_replenishment_qty: Decimal | None,
) -> PrimaryDriver:
    """Classificazione primaria by_article (DL-ARCH-V2-031 §2.1).

    Precedenza:
    1) customer_shortage_qty > 0 -> customer
    2) altrimenti, stock_replenishment_qty > 0 -> stock

    Per robustezza conservativa, in assenza di entrambe le componenti torna customer.
    """
    if customer_shortage_qty > Decimal("0"):
        return "customer"
    if stock_replenishment_qty is not None and stock_replenishment_qty > Decimal("0"):
        return "stock"
    return "customer"


def required_qty_minimum_by_primary_driver_v1(
    customer_shortage_qty: Decimal,
    stock_replenishment_qty: Decimal | None,
    primary_driver: PrimaryDriver,
) -> Decimal:
    """Fabbisogno minimo coerente con il driver primario (DL-ARCH-V2-031 §2.2)."""
    if primary_driver == "stock":
        return stock_replenishment_qty if stock_replenishment_qty is not None else Decimal("0")
    return customer_shortage_qty


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
