"""
Query Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-065, TASK-V2-068,
TASK-V2-071, TASK-V2-074, DL-ARCH-V2-025, DL-ARCH-V2-027, DL-ARCH-V2-028).

Branching:
- by_article (effective_aggrega = True o None): logica V1 retrocompatibile, anchorata a
  core_availability. Candidate: future_availability_qty < 0.
- by_customer_order_line (effective_aggrega = False): logica V2, anchorata a
  sync_righe_ordine_cliente. Candidate: line_future_coverage_qty < 0.

Regole comuni:
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- produzioni completate (forza_completata=True) escluse dalla supply in entrambe le modalita
- ordinamento finale: required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC)

Ramo by_article:
- stock_effective = max(inventory_qty, 0): clamp giacenza fisica (DL-ARCH-V2-028 §1)
- availability_qty = stock_effective - set_aside - committed (valore clamped, non raw)
- incoming_supply_qty: aggregata da sync_produzioni_attive per codice articolo
- customer_open_demand_qty: aggregata da sync_righe_ordine_cliente per codice articolo (informativa)
- candidate se future_availability_qty = availability_qty + incoming_supply_qty < 0
- reason_code = "future_availability_negative"

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
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import resolve_planning_policy
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    PlanningContextOrderLine,
    effective_stock,
    future_availability_v1,
    is_planning_candidate_v1,
    is_planning_candidate_by_order_line,
    line_future_coverage_v2,
    required_qty_minimum_v1,
    required_qty_minimum_by_order_line,
)
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

        result.append(_ArticoloInfo(
            article_code=art.codice_articolo.strip().upper(),
            display_label=_display_label(art.descrizione_1, art.descrizione_2, art.codice_articolo.strip().upper()),
            famiglia_code=famiglia_code,
            famiglia_label=famiglia.label if famiglia else None,
            effective_considera=effective_considera,
            effective_aggrega=effective_aggrega,
            planning_mode=resolve_planning_mode(effective_aggrega),
            misura=(art.misura_articolo or "").strip() or None,
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
) -> list[tuple[Decimal, PlanningCandidateItem]]:
    """Genera candidati by_article (V1 behavior).

    Ancora: core_availability. Candidate: future_availability_qty < 0.
    Articoli senza riga core_availability non producono candidati.
    """
    if not articoli:
        return []

    article_codes_upper = {a.article_code for a in articoli}
    articoli_map = {a.article_code: a for a in articoli}

    incoming = _compute_incoming_supply_by_article(session, forza_completata_ids, article_codes_upper)
    demand = _compute_customer_demand(session)

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
        # La giacenza negativa e un'anomalia inventariale, non un fabbisogno produttivo.
        # stock_effective = max(on_hand, 0) — impedisce che anomalie dati (movimenti
        # fantasma, rettifiche non sincronizzate) generino candidate fittizi.
        stock_eff = effective_stock(avail.inventory_qty)
        avail_eff = stock_eff - avail.customer_set_aside_qty - avail.committed_qty

        ctx = PlanningContext(
            article_code=avail.article_code,
            availability_qty=avail_eff,
            incoming_supply_qty=incoming_qty,
            customer_open_demand_qty=demand_qty,
        )
        if not is_planning_candidate_v1(ctx):
            continue

        fav = future_availability_v1(ctx)
        assert fav is not None
        req = required_qty_minimum_v1(fav)

        candidates.append((req, PlanningCandidateItem(
            article_code=avail.article_code,
            display_label=art.display_label,
            famiglia_code=art.famiglia_code,
            famiglia_label=art.famiglia_label,
            effective_considera_in_produzione=art.effective_considera,
            effective_aggrega_codice_in_produzione=art.effective_aggrega,
            planning_mode=art.planning_mode,
            reason_code="future_availability_negative",
            reason_text="Disponibilita futura negativa anche considerando la supply in corso",
            misura=art.misura,
            required_qty_minimum=req,
            computed_at=avail.computed_at,
            # by_article — availability_qty usa il valore clamped (stock_effective)
            availability_qty=avail_eff,
            customer_open_demand_qty=demand_qty,
            incoming_supply_qty=incoming_qty,
            future_availability_qty=fav,
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

def list_planning_candidates_v1(session: Session) -> list[PlanningCandidateItem]:
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

    candidates_ba = _list_by_article_candidates(session, articoli_by_article, forza_completata_ids)

    linked_supply = _compute_linked_supply_by_line(session, forza_completata_ids) if articoli_by_col else {}
    candidates_col = _list_by_customer_order_line_candidates(session, articoli_by_col, linked_supply)

    all_candidates = candidates_ba + candidates_col
    all_candidates.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in all_candidates]
