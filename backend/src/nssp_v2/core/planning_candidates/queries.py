"""
Query Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-065, TASK-V2-068,
TASK-V2-071, TASK-V2-074, TASK-V2-085, TASK-V2-100, DL-ARCH-V2-025, DL-ARCH-V2-027,
DL-ARCH-V2-028, DL-ARCH-V2-030, DL-ARCH-V2-031).

Branching:
- by_article (effective_aggrega = True o None): logica V1 retrocompatibile, anchorata a
  core_availability. Candidate: fav < 0 OPPURE (se gestione_scorte_attiva) fav < trigger_stock_qty.
- by_customer_order_line (effective_aggrega = False): logica V2, anchorata a
  sync_righe_ordine_cliente. Candidate: line_future_coverage_qty < 0.

Regole comuni:
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- produzioni completate (forza_completata=True) escluse dalla supply in entrambe le modalita
- ordinamento finale: required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC)

Ramo by_article (TASK-V2-085 — stock policy integrata):
- stock_effective = max(inventory_qty, 0): clamp giacenza fisica (DL-ARCH-V2-028 §1)
- availability_qty = stock_effective - set_aside - committed (valore clamped, non raw)
- incoming_supply_qty: aggregata da sync_produzioni_attive per codice articolo
- customer_open_demand_qty: aggregata da sync_righe_ordine_cliente per codice articolo (informativa)
- stock metrics V1 caricati da list_stock_metrics_v1 (solo articoli by_article con gestione_scorte_attiva)
- candidate se:
    - fav < 0 (shortage cliente) → reason_code = "future_availability_negative"
    - OPPURE fav < trigger_stock_qty (trigger scorta) → reason_code = "stock_below_trigger"
- breakdown per articolo by_article:
    - customer_shortage_qty = max(-fav, 0)
    - stock_horizon_availability_qty = stock_eff - set_aside - capped_committed + incoming
      dove capped_committed = impegni con data_consegna entro oggi + effective_stock_months * 30 gg
    - stock_replenishment_qty = max(target_stock_qty - max(stock_horizon_avail, 0), 0) — TASK-V2-101
    - required_qty_total = customer_shortage_qty + stock_replenishment_qty

Ramo by_customer_order_line:
- nessun uso di core_availability (modalita commessa-oriented, non stock-oriented)
- domanda per riga: max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
- supply: produzioni con riferimento_numero_ordine_cliente / riferimento_riga_ordine_cliente
  coincidenti con order_reference / line_reference della riga ordine
- candidate se line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty < 0
- display_label usa la descrizione dalla riga ordine se valorizzata (DL-ARCH-V2-028 §2)
- reason_code = "line_demand_uncovered"
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import resolve_planning_policy
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    PlanningContextOrderLine,
    customer_shortage_qty_v1,
    effective_stock,
    future_availability_v1,
    is_planning_candidate_with_stock_v1,
    is_planning_candidate_by_order_line,
    line_future_coverage_v2,
    required_qty_minimum_by_order_line,
    required_qty_total_v1,
    stock_horizon_availability_qty_v1,
    stock_replenishment_qty_v1,
    resolve_primary_driver_v1,
    required_qty_minimum_by_primary_driver_v1,
)
from nssp_v2.core.stock_policy import StockMetricsItem, list_stock_metrics_v1
from nssp_v2.core.planning_mode import PlanningMode, resolve_planning_mode
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem
from nssp_v2.core.produzioni.models import CoreProduzioneOverride
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente


# ─── Helper presentazione ─────────────────────────────────────────────────────

def _display_label(d1: str | None, d2: str | None, article_code: str) -> str:
    """Campo sintetico di presentazione (DL-ARCH-V2-013 §6)."""
    d1 = (d1 or "").strip()
    d2 = (d2 or "").strip()
    if d1 and d2:
        return f"{d1} {d2}"
    if d1:
        return d1
    return article_code


# ─── Customer horizon (TASK-V2-100, DL-ARCH-V2-031 §3) ───────────────────────

_DEFAULT_CUSTOMER_HORIZON_DAYS = 30
"""Orizzonte temporale cliente di default (giorni).

V1: costante di modulo — configurazione minima senza tabella DB.
La UI puo usare il flag is_within_customer_horizon per filtrare i candidate
entro l'orizzonte senza perdere i candidate fuori orizzonte nel Core.
"""


def _compute_nearest_delivery_by_article(
    session: Session,
    article_codes_upper: set[str],
) -> dict[str, date]:
    """Calcola la data_consegna piu vicina per articolo dalle righe ordine cliente.

    Considera solo righe con expected_delivery_date valorizzata e non descrittive
    (continues_previous_line != True). Esclude articoli non nel set dato.

    Risultato: article_code (canonical) -> data minima (solo articoli con almeno una data).
    """
    from datetime import datetime as _dt
    rows = (
        session.query(
            func.upper(func.trim(SyncRigaOrdineCliente.article_code)).label("art"),
            func.min(SyncRigaOrdineCliente.expected_delivery_date).label("nearest"),
        )
        .filter(SyncRigaOrdineCliente.article_code.isnot(None))
        .filter(SyncRigaOrdineCliente.expected_delivery_date.isnot(None))
        .filter(
            (SyncRigaOrdineCliente.continues_previous_line == False)  # noqa: E712
            | SyncRigaOrdineCliente.continues_previous_line.is_(None)
        )
        .group_by(func.upper(func.trim(SyncRigaOrdineCliente.article_code)))
        .all()
    )
    result: dict[str, date] = {}
    for row in rows:
        if not row.art or row.art not in article_codes_upper or row.nearest is None:
            continue
        nearest = row.nearest
        result[row.art] = nearest.date() if isinstance(nearest, _dt) else nearest
    return result


def _is_within_customer_horizon(
    nearest_delivery: date | None,
    horizon_days: int,
) -> bool | None:
    """True se nearest_delivery <= oggi + horizon_days. None se nessuna data."""
    if nearest_delivery is None:
        return None
    return nearest_delivery <= date.today() + timedelta(days=horizon_days)


# ─── Dataclass articolo ───────────────────────────────────────────────────────

@dataclass
class _ArticoloInfo:
    """Dati articolo con policy effettiva risolta — usato come input al branching."""
    article_code: str          # canonical: strip().upper()
    display_label: str
    famiglia_code: str | None
    famiglia_label: str | None
    effective_considera: bool | None
    effective_aggrega: bool | None
    planning_mode: PlanningMode | None
    misura: str | None         # misura_articolo da SyncArticolo (ART_MISURA)
    effective_gestione_scorte: bool | None  # prerequisito stock policy (TASK-V2-099)
    effective_stock_months: Decimal | None  # look-ahead scorta per capping impegni (TASK-V2-101)


# ─── Step 1: caricamento articoli con policy ──────────────────────────────────

def _load_articoli_info(session: Session) -> list[_ArticoloInfo]:
    """Carica tutti gli articoli attivi con policy effettiva risolta.

    Base del branching: determina planning_mode per ogni articolo prima
    di eseguire le query specifiche per modalita.
    """
    famiglie_map: dict[str, ArticoloFamiglia] = {
        f.code: f
        for f in session.query(ArticoloFamiglia).filter(ArticoloFamiglia.is_active == True).all()  # noqa: E712
    }

    rows = (
        session.query(SyncArticolo, CoreArticoloConfig)
        .outerjoin(
            CoreArticoloConfig,
            func.upper(CoreArticoloConfig.codice_articolo) == func.upper(SyncArticolo.codice_articolo),
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .all()
    )

    result: list[_ArticoloInfo] = []
    for art, config in rows:
        famiglia_code = config.famiglia_code if config is not None else None
        famiglia = famiglie_map.get(famiglia_code) if famiglia_code else None
        override_considera = config.override_considera_in_produzione if config is not None else None
        override_aggrega = config.override_aggrega_codice_in_produzione if config is not None else None
        effective_considera = resolve_planning_policy(override_considera, famiglia.considera_in_produzione if famiglia else None)
        effective_aggrega = resolve_planning_policy(override_aggrega, famiglia.aggrega_codice_in_produzione if famiglia else None)

        # Gestione scorte attiva — prerequisito stock policy (TASK-V2-099)
        override_gestione = config.override_gestione_scorte_attiva if config is not None else None
        family_gestione = famiglia.gestione_scorte_attiva if famiglia else None
        effective_gestione = resolve_planning_policy(override_gestione, family_gestione)

        # Stock months effettivi — look-ahead scorta per capping impegni (TASK-V2-101)
        override_stock_months = config.override_stock_months if config is not None else None
        family_stock_months = famiglia.stock_months if famiglia else None
        effective_stock_months = override_stock_months if override_stock_months is not None else family_stock_months

        result.append(_ArticoloInfo(
            article_code=art.codice_articolo.strip().upper(),
            display_label=_display_label(art.descrizione_1, art.descrizione_2, art.codice_articolo.strip().upper()),
            famiglia_code=famiglia_code,
            famiglia_label=famiglia.label if famiglia else None,
            effective_considera=effective_considera,
            effective_aggrega=effective_aggrega,
            planning_mode=resolve_planning_mode(effective_aggrega),
            misura=(art.misura_articolo or "").strip() or None,
            effective_gestione_scorte=effective_gestione,
            effective_stock_months=effective_stock_months,
        ))
    return result


# ─── Step 2a: supply e demand per by_article ──────────────────────────────────

def _load_forza_completata_ids(session: Session) -> set[int]:
    """Set di id_dettaglio con forza_completata=True (esclusi dalla supply)."""
    return {
        r.id_dettaglio
        for r in session.query(CoreProduzioneOverride.id_dettaglio)
        .filter(CoreProduzioneOverride.forza_completata == True)  # noqa: E712
        .all()
    }


def _compute_incoming_supply_by_article(
    session: Session,
    forza_completata_ids: set[int],
    article_codes_upper: set[str],
) -> dict[str, Decimal]:
    """Aggrega incoming_supply_qty per article_code — ramo by_article.

    Per ogni produzione attiva con article_code nel set dato:
    - remaining = max(quantita_ordinata - quantita_prodotta, 0)
    - escluse produzioni con forza_completata=True
    """
    rows = (
        session.query(
            SyncProduzioneAttiva.id_dettaglio,
            SyncProduzioneAttiva.codice_articolo,
            SyncProduzioneAttiva.quantita_ordinata,
            SyncProduzioneAttiva.quantita_prodotta,
        )
        .filter(SyncProduzioneAttiva.attivo == True)  # noqa: E712
        .filter(SyncProduzioneAttiva.codice_articolo.isnot(None))
        .all()
    )

    result: dict[str, Decimal] = {}
    for id_det, codice, ordinata, prodotta in rows:
        if id_det in forza_completata_ids:
            continue
        canonical = codice.strip().upper()
        if canonical not in article_codes_upper:
            continue
        ord_qty = ordinata if ordinata is not None else Decimal("0")
        prod_qty = prodotta if prodotta is not None else Decimal("0")
        remaining = max(ord_qty - prod_qty, Decimal("0"))
        result[canonical] = result.get(canonical, Decimal("0")) + remaining
    return result


def _compute_customer_demand(session: Session) -> dict[str, Decimal]:
    """Aggrega customer_open_demand_qty per article_code canonico (per by_article, informativa).

    Formula per riga: max(ordered_qty - set_aside_qty - fulfilled_qty, 0).
    Esclude righe descrittive (continues_previous_line=True) e righe senza article_code.
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
        open_qty = max(ord_qty - sa_qty - ful_qty, Decimal("0"))
        result[canonical] = result.get(canonical, Decimal("0")) + open_qty
    return result


# ─── Step 2a-bis: impegni per articolo con data_consegna (stock horizon) ─────

def _load_open_commitments_by_article_with_dates(
    session: Session,
    article_codes_upper: set[str],
) -> dict[str, list[tuple[Decimal, date | None]]]:
    """Carica domanda aperta per articolo con data_consegna — per stock horizon capping (TASK-V2-101).

    Restituisce per ogni articolo: lista di (open_qty, delivery_date).
    Righe con open_qty = 0 sono escluse.
    Righe senza expected_delivery_date: delivery_date = None.
    """
    from datetime import datetime as _dt
    rows = (
        session.query(
            SyncRigaOrdineCliente.article_code,
            SyncRigaOrdineCliente.ordered_qty,
            SyncRigaOrdineCliente.set_aside_qty,
            SyncRigaOrdineCliente.fulfilled_qty,
            SyncRigaOrdineCliente.expected_delivery_date,
        )
        .filter(SyncRigaOrdineCliente.article_code.isnot(None))
        .filter(
            (SyncRigaOrdineCliente.continues_previous_line == False)  # noqa: E712
            | SyncRigaOrdineCliente.continues_previous_line.is_(None)
        )
        .all()
    )

    result: dict[str, list[tuple[Decimal, date | None]]] = {}
    for codice, ordered, set_aside, fulfilled, delivery in rows:
        canonical = (codice or "").strip().upper()
        if canonical not in article_codes_upper:
            continue
        ord_qty = ordered if ordered is not None else Decimal("0")
        sa_qty = set_aside if set_aside is not None else Decimal("0")
        ful_qty = fulfilled if fulfilled is not None else Decimal("0")
        open_qty = max(ord_qty - sa_qty - ful_qty, Decimal("0"))
        if open_qty == Decimal("0"):
            continue
        delivery_date: date | None = None
        if delivery is not None:
            delivery_date = delivery.date() if isinstance(delivery, _dt) else delivery
        if canonical not in result:
            result[canonical] = []
        result[canonical].append((open_qty, delivery_date))
    return result


def _capped_commitments_from_lines(
    line_data: list[tuple[Decimal, date | None]],
    lookahead_date: date,
) -> Decimal:
    """Somma degli impegni con data_consegna entro il look-ahead stock (TASK-V2-101).

    Regola:
    - delivery_date <= lookahead_date: incluso
    - delivery_date > lookahead_date: escluso (oltre l'orizzonte scorta)
    - delivery_date is None: incluso (conservativo — data sconosciuta, trattata come urgente)
    """
    total = Decimal("0")
    for open_qty, delivery_date in line_data:
        if delivery_date is None or delivery_date <= lookahead_date:
            total += open_qty
    return total


# ─── Step 2b: supply collegata per by_customer_order_line ────────────────────

def _compute_linked_supply_by_line(
    session: Session,
    forza_completata_ids: set[int],
) -> dict[tuple[str, int], Decimal]:
    """Aggrega supply per (order_reference, line_reference) — ramo by_customer_order_line.

    Filtra solo produzioni con riferimento ordine cliente valorizzato.
    Escluse produzioni con forza_completata=True.

    Chiave: (riferimento_numero_ordine_cliente.strip(), int(riferimento_riga_ordine_cliente))
    """
    rows = (
        session.query(
            SyncProduzioneAttiva.id_dettaglio,
            SyncProduzioneAttiva.riferimento_numero_ordine_cliente,
            SyncProduzioneAttiva.riferimento_riga_ordine_cliente,
            SyncProduzioneAttiva.quantita_ordinata,
            SyncProduzioneAttiva.quantita_prodotta,
        )
        .filter(SyncProduzioneAttiva.attivo == True)  # noqa: E712
        .filter(SyncProduzioneAttiva.riferimento_numero_ordine_cliente.isnot(None))
        .filter(SyncProduzioneAttiva.riferimento_riga_ordine_cliente.isnot(None))
        .all()
    )

    result: dict[tuple[str, int], Decimal] = {}
    for id_det, ref_num, ref_riga, ordinata, prodotta in rows:
        if id_det in forza_completata_ids:
            continue
        ref_num_stripped = (ref_num or "").strip()
        if not ref_num_stripped:
            continue
        try:
            ref_line_int = int(ref_riga)
        except (TypeError, ValueError):
            continue
        key = (ref_num_stripped, ref_line_int)
        ord_qty = ordinata if ordinata is not None else Decimal("0")
        prod_qty = prodotta if prodotta is not None else Decimal("0")
        remaining = max(ord_qty - prod_qty, Decimal("0"))
        result[key] = result.get(key, Decimal("0")) + remaining
    return result


# ─── Ramo by_article ─────────────────────────────────────────────────────────

def _list_by_article_candidates(
    session: Session,
    articoli: list[_ArticoloInfo],
    forza_completata_ids: set[int],
    customer_horizon_days: int,
) -> list[tuple[Decimal, PlanningCandidateItem]]:
    """Genera candidati by_article con stock policy V1 integrata (TASK-V2-085).

    Ancora: core_availability. Candidate:
    - fav < 0 (shortage cliente), OPPURE
    - fav < trigger_stock_qty (trigger scorta)

    Articoli senza riga core_availability non producono candidati.
    Stock metrics caricate da list_stock_metrics_v1 — solo articoli by_article.
    """
    if not articoli:
        return []

    article_codes_upper = {a.article_code for a in articoli}
    articoli_map = {a.article_code: a for a in articoli}

    incoming = _compute_incoming_supply_by_article(session, forza_completata_ids, article_codes_upper)
    demand = _compute_customer_demand(session)

    # Customer horizon — data_consegna piu vicina per articolo (TASK-V2-100)
    nearest_deliveries = _compute_nearest_delivery_by_article(session, article_codes_upper)

    # Stock horizon — impegni per articolo con data_consegna (per capping — TASK-V2-101)
    open_commitments_with_dates = _load_open_commitments_by_article_with_dates(session, article_codes_upper)

    # Stock metrics V1 — solo per articoli by_article (list_stock_metrics_v1 filtra gia)
    stock_metrics: dict[str, StockMetricsItem] = {
        m.article_code: m
        for m in list_stock_metrics_v1(session)
        if m.article_code in article_codes_upper
    }

    avail_rows = (
        session.query(CoreAvailability)
        .filter(CoreAvailability.article_code.in_(article_codes_upper))
        .all()
    )

    candidates: list[tuple[Decimal, PlanningCandidateItem]] = []
    for avail in avail_rows:
        art = articoli_map.get(avail.article_code)
        if art is None:
            continue

        incoming_qty = incoming.get(avail.article_code, Decimal("0"))
        demand_qty = demand.get(avail.article_code, Decimal("0"))

        # DL-ARCH-V2-028 §1: clamp giacenza fisica a 0.
        stock_eff = effective_stock(avail.inventory_qty)
        avail_eff = stock_eff - avail.customer_set_aside_qty - avail.committed_qty

        ctx = PlanningContext(
            article_code=avail.article_code,
            availability_qty=avail_eff,
            incoming_supply_qty=incoming_qty,
            customer_open_demand_qty=demand_qty,
        )

        # Stock metrics per questo articolo — solo se gestione_scorte_attiva (TASK-V2-099)
        # Se il flag e False o None, non si usa mai la stock policy (trigger e target = None)
        metrics = stock_metrics.get(avail.article_code) if art.effective_gestione_scorte is True else None
        trigger_qty = metrics.trigger_stock_qty if metrics else None
        target_qty = metrics.target_stock_qty if metrics else None

        fav = future_availability_v1(ctx)

        # Condizione candidatura estesa con stock policy (TASK-V2-085)
        if not is_planning_candidate_with_stock_v1(fav, trigger_qty):
            continue

        assert fav is not None
        # Breakdown stock-driven (DL-ARCH-V2-030 §9, TASK-V2-101)
        shortage = customer_shortage_qty_v1(fav)

        # Stock horizon (DL-ARCH-V2-031 §4): capping impegni SOLO su effective_stock_months.
        # customer_horizon_days non deve influenzare la componente scorta.
        if target_qty is not None:
            if art.effective_stock_months is not None:
                lookahead_days = int(round(float(art.effective_stock_months) * 30))
                lookahead_date = date.today() + timedelta(days=lookahead_days)
                line_data = open_commitments_with_dates.get(avail.article_code, [])
                capped_committed = _capped_commitments_from_lines(line_data, lookahead_date)
            else:
                capped_committed = avail.committed_qty
            stock_horizon_avail = stock_horizon_availability_qty_v1(
                stock_eff, avail.customer_set_aside_qty, capped_committed, incoming_qty
            )
        else:
            stock_horizon_avail = avail_eff  # no stock policy: nessun capping

        replenishment = stock_replenishment_qty_v1(target_qty, stock_horizon_avail)
        primary_driver = resolve_primary_driver_v1(shortage, replenishment)
        req = required_qty_minimum_by_primary_driver_v1(shortage, replenishment, primary_driver)
        req_total = required_qty_total_v1(shortage, replenishment)

        # Reason code: shortage cliente prioritario; stock trigger come secondo motivo
        if fav < Decimal("0"):
            reason_code = "future_availability_negative"
            reason_text = "Disponibilita futura negativa anche considerando la supply in corso"
        else:
            reason_code = "stock_below_trigger"
            reason_text = "Disponibilita futura inferiore alla soglia di trigger scorta"

        # Customer horizon flag (TASK-V2-100, DL-ARCH-V2-031 §3) — usa customer_horizon_days
        within_horizon = _is_within_customer_horizon(
            nearest_deliveries.get(avail.article_code),
            customer_horizon_days,
        )

        candidates.append((req, PlanningCandidateItem(
            article_code=avail.article_code,
            display_label=art.display_label,
            famiglia_code=art.famiglia_code,
            famiglia_label=art.famiglia_label,
            effective_considera_in_produzione=art.effective_considera,
            effective_aggrega_codice_in_produzione=art.effective_aggrega,
            planning_mode=art.planning_mode,
            reason_code=reason_code,
            reason_text=reason_text,
            misura=art.misura,
            required_qty_minimum=req,
            computed_at=avail.computed_at,
            # by_article
            availability_qty=avail_eff,
            customer_open_demand_qty=demand_qty,
            incoming_supply_qty=incoming_qty,
            future_availability_qty=fav,
            # stock policy breakdown (TASK-V2-085)
            customer_shortage_qty=shortage,
            stock_replenishment_qty=replenishment,
            required_qty_total=req_total,
            primary_driver=primary_driver,
            # customer horizon (TASK-V2-100, TASK-V2-102)
            is_within_customer_horizon=within_horizon,
            nearest_delivery_date=nearest_deliveries.get(avail.article_code),
        )))
    return candidates


# ─── Ramo by_customer_order_line ─────────────────────────────────────────────

def _list_by_customer_order_line_candidates(
    session: Session,
    articoli: list[_ArticoloInfo],
    linked_supply: dict[tuple[str, int], Decimal],
) -> list[tuple[Decimal, PlanningCandidateItem]]:
    """Genera candidati by_customer_order_line (TASK-V2-071).

    Ancora: sync_righe_ordine_cliente. Candidate: line_future_coverage_qty < 0.
    Ogni riga ordine aperta genera al piu un candidato.
    Righe con line_open_demand_qty == 0 sono saltate.
    """
    if not articoli:
        return []

    article_codes_upper = {a.article_code for a in articoli}
    articoli_map = {a.article_code: a for a in articoli}

    righe = (
        session.query(SyncRigaOrdineCliente)
        .filter(SyncRigaOrdineCliente.article_code.isnot(None))
        .filter(
            (SyncRigaOrdineCliente.continues_previous_line == False)  # noqa: E712
            | SyncRigaOrdineCliente.continues_previous_line.is_(None)
        )
        .all()
    )

    candidates: list[tuple[Decimal, PlanningCandidateItem]] = []
    for riga in righe:
        canonical = riga.article_code.strip().upper()
        if canonical not in article_codes_upper:
            continue

        art = articoli_map[canonical]

        ord_qty = riga.ordered_qty if riga.ordered_qty is not None else Decimal("0")
        sa_qty = riga.set_aside_qty if riga.set_aside_qty is not None else Decimal("0")
        ful_qty = riga.fulfilled_qty if riga.fulfilled_qty is not None else Decimal("0")
        line_demand = max(ord_qty - sa_qty - ful_qty, Decimal("0"))

        if line_demand == Decimal("0"):
            continue  # nessuna domanda aperta

        key = (riga.order_reference, riga.line_reference)
        linked_qty = linked_supply.get(key, Decimal("0"))

        ctx = PlanningContextOrderLine(
            article_code=canonical,
            order_reference=riga.order_reference,
            line_reference=riga.line_reference,
            line_open_demand_qty=line_demand,
            linked_incoming_supply_qty=linked_qty,
        )
        if not is_planning_candidate_by_order_line(ctx):
            continue

        coverage = line_future_coverage_v2(ctx)
        req = required_qty_minimum_by_order_line(coverage)

        # DL-ARCH-V2-028 §2: per by_customer_order_line la descrizione primaria
        # e quella della riga ordine cliente, non quella anagrafica articolo.
        order_line_desc = (riga.article_description_segment or "").strip() or None
        display = order_line_desc or art.display_label

        # Misura dalla riga ordine (DL-ARCH-V2-028 §3)
        misura_col = (riga.article_measure or "").strip() or None

        candidates.append((req, PlanningCandidateItem(
            article_code=canonical,
            display_label=display,
            famiglia_code=art.famiglia_code,
            famiglia_label=art.famiglia_label,
            effective_considera_in_produzione=art.effective_considera,
            effective_aggrega_codice_in_produzione=art.effective_aggrega,
            planning_mode=art.planning_mode,
            reason_code="line_demand_uncovered",
            reason_text="Domanda sulla riga ordine non coperta dalla supply collegata",
            misura=misura_col,
            required_qty_minimum=req,
            computed_at=riga.synced_at,
            primary_driver="customer",
            # by_customer_order_line
            order_reference=riga.order_reference,
            line_reference=riga.line_reference,
            order_line_description=order_line_desc,
            line_open_demand_qty=line_demand,
            linked_incoming_supply_qty=linked_qty,
            line_future_coverage_qty=coverage,
        )))
    return candidates


# ─── Query principale ─────────────────────────────────────────────────────────

def list_planning_candidates_v1(session: Session, customer_horizon_days: int = 30) -> list[PlanningCandidateItem]:
    """Lista planning candidates con branching by_article / by_customer_order_line.

    Step 1: carica tutti gli articoli attivi con planning_mode risolto.
    Step 2a: ramo by_article (planning_mode in {by_article, None}) — logica V1.
    Step 2b: ramo by_customer_order_line — logica V2 per-riga ordine.
    Step 3: merge e ordina per required_qty_minimum decrescente (UIX_SPEC).

    Articoli senza policy definita (planning_mode = None) usano il ramo by_article
    (V1 fallback conservativo).
    """
    articoli = _load_articoli_info(session)

    articoli_by_article = [a for a in articoli if a.planning_mode != "by_customer_order_line"]
    articoli_by_col = [a for a in articoli if a.planning_mode == "by_customer_order_line"]

    forza_completata_ids = _load_forza_completata_ids(session)

    candidates_ba = _list_by_article_candidates(
        session,
        articoli_by_article,
        forza_completata_ids,
        customer_horizon_days,
    )

    linked_supply = _compute_linked_supply_by_line(session, forza_completata_ids) if articoli_by_col else {}
    candidates_col = _list_by_customer_order_line_candidates(session, articoli_by_col, linked_supply)

    all_candidates = candidates_ba + candidates_col
    all_candidates.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in all_candidates]
