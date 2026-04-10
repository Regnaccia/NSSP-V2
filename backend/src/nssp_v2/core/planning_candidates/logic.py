"""
Logiche di dominio Core slice `planning_candidates` V1 (TASK-V2-062, DL-ARCH-V2-025).

Struttura:
- PlanningContext: contesto stabile (fact canonici + aggregati) passato alla logica
- future_availability_v1: calcolo deterministico della copertura futura
- required_qty_minimum_v1: scopertura minima quando la copertura futura e negativa
- is_planning_candidate_v1: funzione pura intercambiabile — V1 = future_availability_qty < 0

Regola DL-ARCH-V2-025:
- planning candidates V1 risponde a: dobbiamo ancora attivare nuova produzione per questo
  articolo, anche considerando la supply gia in corso?
- regola V1: future_availability_qty = availability_qty + incoming_supply_qty < 0
- la logica e un livello separato, testabile in isolamento (DL-ARCH-V2-023)
"""

from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanningContext:
    """Contesto di fact canonici e aggregati passato alla logica planning V1.

    article_code: codice canonico dell'articolo (strip().upper()).
    availability_qty: quota libera attuale (CoreAvailability). None se non ancora calcolata.
    incoming_supply_qty: supply aggregata da produzioni attive per articolo (>= 0).
    customer_open_demand_qty: domanda cliente aperta aggregata per articolo (>= 0).
    """

    article_code: str
    availability_qty: Decimal | None
    incoming_supply_qty: Decimal
    customer_open_demand_qty: Decimal


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
