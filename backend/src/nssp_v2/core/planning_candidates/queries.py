"""
Query Core slice `planning_candidates` V1 (TASK-V2-062, TASK-V2-065, DL-ARCH-V2-025).

Regole:
- legge da core_availability (mai dai mirror sync direttamente per il fatto canonico)
- perimetro articoli: INNER JOIN su sync_articoli con attivo=True — coerente con criticita
  (un codice con availability_qty ma assente/non attivo in sync_articoli non appare)
- incoming_supply_qty aggregata da sync_produzioni_attive (attivo=True) per articolo
- customer_open_demand_qty aggregata da sync_righe_ordine_cliente per articolo
- join cross-source con UPPER() per tollerare mismatch di casing (TASK-V2-059, TASK-V2-060)
- candidato generato solo quando future_availability_qty < 0 (DL-ARCH-V2-025 §Generation Rule)
- arricchimento presentazione: sync_articoli (descrizione), core_articolo_config + articolo_famiglie
- effective policy (DL-ARCH-V2-026): resolve_planning_policy sul lato query
- ordinamento default: required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC)

V1 tradeoffs espliciti (DL-ARCH-V2-025):
- incoming_supply_qty e time-agnostic: nessun ETA, nessun horizon
- produzioni attive trattate come supply in arrivo (rimanente = ordinata - prodotta)
- forza_completata non considerato in V1 per semplicita (override Core non impatta qui)
- customer_open_demand_qty: max(ordered - set_aside - fulfilled, 0) per riga non-description
"""

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import resolve_planning_policy
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    future_availability_v1,
    is_planning_candidate_v1,
    required_qty_minimum_v1,
)
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente


def _display_label(d1: str | None, d2: str | None, article_code: str) -> str:
    """Campo sintetico di presentazione (DL-ARCH-V2-013 §6)."""
    d1 = (d1 or "").strip()
    d2 = (d2 or "").strip()
    if d1 and d2:
        return f"{d1} {d2}"
    if d1:
        return d1
    return article_code


# ─── Aggregati ausiliari ──────────────────────────────────────────────────────

def _compute_incoming_supply(session: Session) -> dict[str, Decimal]:
    """Aggrega incoming_supply_qty per article_code canonico da produzioni attive.

    Per ogni produzione attiva (attivo=True) con codice_articolo definito:
    - remaining_qty = max(quantita_ordinata - COALESCE(quantita_prodotta, 0), 0)

    Se entrambe le quantita sono None, la produzione contribuisce 0.

    Il codice articolo e normalizzato a UPPER in Python per allineamento al canonical
    article_code di core_availability.

    V1 tradeoff: non considera forza_completata (override Core) — la produzione resta
    "incoming" se attivo=True, anche se marcata completata via override.
    """
    rows = (
        session.query(
            SyncProduzioneAttiva.codice_articolo,
            SyncProduzioneAttiva.quantita_ordinata,
            SyncProduzioneAttiva.quantita_prodotta,
        )
        .filter(SyncProduzioneAttiva.attivo == True)  # noqa: E712
        .filter(SyncProduzioneAttiva.codice_articolo.isnot(None))
        .all()
    )

    result: dict[str, Decimal] = {}
    for codice, ordinata, prodotta in rows:
        canonical = codice.strip().upper()
        ord_qty = ordinata if ordinata is not None else Decimal("0")
        prod_qty = prodotta if prodotta is not None else Decimal("0")
        remaining = ord_qty - prod_qty
        if remaining < Decimal("0"):
            remaining = Decimal("0")
        result[canonical] = result.get(canonical, Decimal("0")) + remaining
    return result


def _compute_customer_demand(session: Session) -> dict[str, Decimal]:
    """Aggrega customer_open_demand_qty per article_code canonico.

    Formula per riga: max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
    Valori None trattati come 0.

    Esclude righe di descrizione (continues_previous_line=True): non generano domanda.
    Esclude righe senza article_code.

    Il codice articolo e normalizzato a UPPER per allineamento al canonical.
    """
    rows = (
        session.query(
            SyncRigaOrdineCliente.article_code,
            SyncRigaOrdineCliente.ordered_qty,
            SyncRigaOrdineCliente.set_aside_qty,
            SyncRigaOrdineCliente.fulfilled_qty,
        )
        .filter(SyncRigaOrdineCliente.article_code.isnot(None))
        .filter(
            (SyncRigaOrdineCliente.continues_previous_line == False)  # noqa: E712
            | SyncRigaOrdineCliente.continues_previous_line.is_(None)
        )
        .all()
    )

    result: dict[str, Decimal] = {}
    for codice, ordered, set_aside, fulfilled in rows:
        canonical = codice.strip().upper()
        ord_qty = ordered if ordered is not None else Decimal("0")
        sa_qty = set_aside if set_aside is not None else Decimal("0")
        ful_qty = fulfilled if fulfilled is not None else Decimal("0")
        open_qty = ord_qty - sa_qty - ful_qty
        if open_qty < Decimal("0"):
            open_qty = Decimal("0")
        result[canonical] = result.get(canonical, Decimal("0")) + open_qty
    return result


# ─── Query principale ─────────────────────────────────────────────────────────

def list_planning_candidates_v1(session: Session) -> list[PlanningCandidateItem]:
    """Lista planning candidates V1 nel perimetro della surface articoli.

    Perimetro articoli: INNER JOIN su sync_articoli con attivo=True.
    Coerente con criticita (TASK-V2-060): un codice assente o non attivo in sync_articoli
    non appare, anche se ha availability_qty negativa.

    Arricchimento (TASK-V2-065):
    - display_label da sync_articoli (descrizione_1 / descrizione_2)
    - famiglia_code / famiglia_label da core_articolo_config + articolo_famiglie
    - effective_considera_in_produzione / effective_aggrega_codice_in_produzione
      via resolve_planning_policy (DL-ARCH-V2-026, TASK-V2-064)

    Logica V1 (DL-ARCH-V2-025):
    - future_availability_qty = availability_qty + incoming_supply_qty
    - candidate se future_availability_qty < 0
    - required_qty_minimum = abs(future_availability_qty) quando candidate

    Ordinamento: required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC).
    """
    incoming = _compute_incoming_supply(session)
    demand = _compute_customer_demand(session)

    # Carica famiglie attive per il lookup
    famiglie_map: dict[str, ArticoloFamiglia] = {
        f.code: f
        for f in session.query(ArticoloFamiglia).filter(ArticoloFamiglia.is_active == True).all()  # noqa: E712
    }

    rows = (
        session.query(CoreAvailability, SyncArticolo, CoreArticoloConfig)
        .join(
            SyncArticolo,
            func.upper(SyncArticolo.codice_articolo) == CoreAvailability.article_code,
        )
        .outerjoin(
            CoreArticoloConfig,
            func.upper(CoreArticoloConfig.codice_articolo) == CoreAvailability.article_code,
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .all()
    )

    candidates: list[tuple[Decimal, PlanningCandidateItem]] = []

    for avail, art, config in rows:
        incoming_qty = incoming.get(avail.article_code, Decimal("0"))
        demand_qty = demand.get(avail.article_code, Decimal("0"))

        ctx = PlanningContext(
            article_code=avail.article_code,
            availability_qty=avail.availability_qty,
            incoming_supply_qty=incoming_qty,
            customer_open_demand_qty=demand_qty,
        )

        if not is_planning_candidate_v1(ctx):
            continue

        fav = future_availability_v1(ctx)
        assert fav is not None  # garantito da is_planning_candidate_v1
        req = required_qty_minimum_v1(fav)

        # Presentazione
        famiglia_code = config.famiglia_code if config is not None else None
        famiglia = famiglie_map.get(famiglia_code) if famiglia_code else None
        family_considera = famiglia.considera_in_produzione if famiglia else None
        family_aggrega = famiglia.aggrega_codice_in_produzione if famiglia else None
        override_considera = config.override_considera_in_produzione if config is not None else None
        override_aggrega = config.override_aggrega_codice_in_produzione if config is not None else None

        candidates.append((
            req,
            PlanningCandidateItem(
                article_code=avail.article_code,
                display_label=_display_label(art.descrizione_1, art.descrizione_2, avail.article_code),
                famiglia_code=famiglia_code,
                famiglia_label=famiglia.label if famiglia else None,
                effective_considera_in_produzione=resolve_planning_policy(override_considera, family_considera),
                effective_aggrega_codice_in_produzione=resolve_planning_policy(override_aggrega, family_aggrega),
                availability_qty=avail.availability_qty,
                customer_open_demand_qty=demand_qty,
                incoming_supply_qty=incoming_qty,
                future_availability_qty=fav,
                required_qty_minimum=req,
                computed_at=avail.computed_at,
            ),
        ))

    # Ordina per required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC)
    candidates.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in candidates]
