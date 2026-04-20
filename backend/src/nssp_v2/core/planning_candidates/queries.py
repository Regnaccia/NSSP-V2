"""
Query Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-065, TASK-V2-068,
TASK-V2-071, TASK-V2-074, TASK-V2-085, TASK-V2-100, TASK-V2-145,
DL-ARCH-V2-025, DL-ARCH-V2-027, DL-ARCH-V2-028, DL-ARCH-V2-030, DL-ARCH-V2-031,
DL-ARCH-V2-042).

Branching:
- by_article (effective_aggrega = True o None): logica V1 retrocompatibile, anchorata a
  core_availability. Candidate: fav < 0 OPPURE (se gestione_scorte_attiva) fav < trigger_stock_qty.
- by_customer_order_line (effective_aggrega = False): logica V2, anchorata a
  sync_righe_ordine_cliente. Candidate: line_future_coverage_qty < 0.

Regole comuni:
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- produzioni completate (forza_completata=True) escluse dalla supply in entrambe le modalita
- ordinamento finale: required_qty_minimum decrescente (maggiore scopertura sopra — UIX_SPEC)

Ramo by_article (TASK-V2-085 — stock policy integrata; TASK-V2-145 — rebase Core):
- stock_effective = max(inventory_qty, 0): clamp giacenza fisica (DL-ARCH-V2-028 §1)
- availability_qty = stock_effective - set_aside - committed (valore clamped, non raw)
- incoming_supply_qty: aggregata da sync_produzioni_attive per codice articolo
- customer_open_demand_qty: aggregata da sync_righe_ordine_cliente per codice articolo (informativa)
- stock metrics V1 caricati da list_stock_metrics_v1 (solo articoli by_article con gestione_scorte_attiva)
- candidate se:
    - fav < 0 (shortage cliente) → reason_code = "future_availability_negative"
    - OPPURE fav < trigger_stock_qty (trigger scorta) → reason_code = "stock_below_trigger"
- breakdown per articolo by_article:
    - customer_shortage_qty = max(-fav, 0)  [TASK-V2-145: usa fav completo, non capped per horizon]
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

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.clienti_destinazioni.models import CoreDestinazioneConfig
from nssp_v2.core.articoli.queries import resolve_planning_policy
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    PlanningContextOrderLine,
    capacity_headroom_now_qty_v1,
    customer_shortage_qty_v1,
    effective_stock,
    future_availability_v1,
    is_planning_candidate_with_stock_v1,
    is_planning_candidate_by_order_line,
    line_future_coverage_v2,
    release_qty_now_max_v1,
    release_status_v1,
    required_qty_minimum_by_order_line,
    required_qty_total_v1,
    stock_horizon_availability_qty_v1,
    stock_replenishment_qty_v1,
    resolve_primary_driver_v1,
    required_qty_minimum_by_primary_driver_v1,
)
from nssp_v2.core.stock_policy import StockMetricsItem, list_stock_metrics_v1
from nssp_v2.core.planning_mode import PlanningMode, resolve_planning_mode
from nssp_v2.core.planning_candidates.read_models import (
    PlanningCandidateActiveWarning,
    PlanningCandidateItem,
    PlanningOpenOrderLine,
)
from nssp_v2.core.produzioni.models import CoreProduzioneOverride
from nssp_v2.core.warnings import filter_warnings_by_areas, list_warnings_v1
# production_proposals.config e production_proposals.logic vengono importati lazy
# dentro le funzioni che li usano per evitare circular import:
# production_proposals.queries -> planning_candidates -> production_proposals.config (ok)
# ma production_proposals.__init__ -> production_proposals.queries -> planning_candidates (circular)
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.clienti.models import SyncCliente
from nssp_v2.sync.destinazioni.models import SyncDestinazione
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


def _normalize_description_parts(parts: list[str | None]) -> list[str]:
    normalized: list[str] = []
    for p in parts:
        v = (p or "").strip()
        if v:
            normalized.append(v)
    return normalized


def _display_description_from_parts(parts: list[str], article_code: str) -> str:
    return " | ".join(parts) if parts else article_code


def _load_active_article_warnings(
    session: Session,
    user_areas: list[str],
    is_admin: bool,
) -> dict[str, list[PlanningCandidateActiveWarning]]:
    """Mappa warning attivi visibili in planning per articolo canonico."""
    visible = filter_warnings_by_areas(
        list_warnings_v1(session),
        user_areas=user_areas,
        is_admin=is_admin,
    )
    warnings_by_article: dict[str, list[PlanningCandidateActiveWarning]] = {}
    for warning in visible:
        warning_item = PlanningCandidateActiveWarning(
            code=warning.type,
            severity=warning.severity,
            message=warning.message,
        )
        bucket = warnings_by_article.setdefault(warning.article_code, [])
        bucket.append(warning_item)
    for code in warnings_by_article:
        warnings_by_article[code].sort(key=lambda w: (w.code, w.message))
    return warnings_by_article


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
    description_parts: list[str]
    display_description: str
    misura: str | None         # misura_articolo da SyncArticolo (ART_MISURA)
    effective_gestione_scorte: bool | None  # prerequisito stock policy (TASK-V2-099)
    effective_stock_months: Decimal | None  # look-ahead scorta per capping impegni (TASK-V2-101)
    # Configurazione proposal — usata per il preview lato planning (TASK-V2-151)
    proposal_logic_key: str | None = None
    proposal_logic_article_params: dict = field(default_factory=dict)


@dataclass
class _OrderLineReadabilityContext:
    article_code: str
    order_reference: str
    line_reference: int
    open_qty: Decimal
    requested_delivery_date: date | None
    description_parts: list[str]
    full_order_line_description: str | None
    requested_destination_display: str | None


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

        description_parts = _normalize_description_parts([art.descrizione_1, art.descrizione_2])
        result.append(_ArticoloInfo(
            article_code=art.codice_articolo.strip().upper(),
            display_label=_display_label(art.descrizione_1, art.descrizione_2, art.codice_articolo.strip().upper()),
            famiglia_code=famiglia_code,
            famiglia_label=famiglia.label if famiglia else None,
            effective_considera=effective_considera,
            effective_aggrega=effective_aggrega,
            planning_mode=resolve_planning_mode(effective_aggrega),
            description_parts=description_parts,
            display_description=_display_description_from_parts(description_parts, art.codice_articolo.strip().upper()),
            misura=(art.misura_articolo or "").strip() or None,
            effective_gestione_scorte=effective_gestione,
            effective_stock_months=effective_stock_months,
            proposal_logic_key=config.proposal_logic_key if config is not None else None,
            proposal_logic_article_params=dict(config.proposal_logic_article_params_json or {}) if config is not None else {},
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


def _compute_open_qty(
    ordered_qty: Decimal | None,
    set_aside_qty: Decimal | None,
    fulfilled_qty: Decimal | None,
) -> Decimal:
    ordered = ordered_qty if ordered_qty is not None else Decimal("0")
    set_aside = set_aside_qty if set_aside_qty is not None else Decimal("0")
    fulfilled = fulfilled_qty if fulfilled_qty is not None else Decimal("0")
    return max(ordered - set_aside - fulfilled, Decimal("0"))


def _build_full_order_line_description(
    head_segment: str | None,
    description_lines: list[str],
) -> str | None:
    parts: list[str] = []
    if head_segment:
        hs = head_segment.strip()
        if hs:
            parts.append(hs)
    for line in description_lines:
        ls = (line or "").strip()
        if ls:
            parts.append(ls)
    if not parts:
        return None
    return " | ".join(parts)


def _load_order_line_readability_contexts(
    session: Session,
    article_codes_upper: set[str],
) -> dict[tuple[str, int], _OrderLineReadabilityContext]:
    """Context per descrizione completa e destinazione richiesta (TASK-V2-108)."""
    rows = (
        session.query(SyncRigaOrdineCliente)
        .order_by(SyncRigaOrdineCliente.order_reference, SyncRigaOrdineCliente.line_reference)
        .all()
    )

    base_rows: dict[tuple[str, int], SyncRigaOrdineCliente] = {}
    description_map: dict[tuple[str, int], list[str]] = {}
    open_qty_map: dict[tuple[str, int], Decimal] = {}
    article_map: dict[tuple[str, int], str] = {}
    pending_key: tuple[str, int] | None = None

    for row in rows:
        if row.continues_previous_line:
            if pending_key is not None and row.order_reference == pending_key[0] and row.article_description_segment:
                description_map[pending_key].append(row.article_description_segment)
            continue

        canonical = (row.article_code or "").strip().upper()
        key = (row.order_reference, row.line_reference)
        pending_key = None
        if not canonical or canonical not in article_codes_upper:
            continue

        base_rows[key] = row
        description_map[key] = []
        open_qty_map[key] = _compute_open_qty(row.ordered_qty, row.set_aside_qty, row.fulfilled_qty)
        article_map[key] = canonical
        pending_key = key

    destination_codes: set[str] = set()
    customer_codes_for_main: set[str] = set()
    destination_identity_by_key: dict[tuple[str, int], tuple[str, str] | None] = {}
    for key, row in base_rows.items():
        customer_code = (row.customer_code or "").strip() or None
        customer_progressive = (row.customer_destination_progressive or "").strip() or None
        destination_code = (row.destination_code or "").strip() or None
        if customer_progressive:
            if destination_code is None:
                destination_identity_by_key[key] = None
            else:
                destination_identity_by_key[key] = ("dest", destination_code)
                destination_codes.add(destination_code)
        else:
            if customer_code is None:
                destination_identity_by_key[key] = None
            else:
                destination_identity_by_key[key] = ("main", customer_code)
                customer_codes_for_main.add(customer_code)

    destination_config_codes: list[str] = []
    for identity in destination_identity_by_key.values():
        if identity is None:
            continue
        kind, code = identity
        if kind == "main":
            destination_config_codes.append(f"MAIN:{code}")
        else:
            destination_config_codes.append(code)
    config_rows = (
        session.query(CoreDestinazioneConfig)
        .filter(CoreDestinazioneConfig.codice_destinazione.in_(set(destination_config_codes)))
        .all()
        if destination_config_codes
        else []
    )
    nickname_by_code = {r.codice_destinazione: (r.nickname_destinazione or "").strip() or None for r in config_rows}

    clienti_rows = (
        session.query(SyncCliente.codice_cli, SyncCliente.ragione_sociale)
        .filter(SyncCliente.codice_cli.in_(customer_codes_for_main))
        .all()
        if customer_codes_for_main
        else []
    )
    ragione_sociale_by_customer = {c: (rs or "").strip() or None for c, rs in clienti_rows}

    dest_rows = (
        session.query(SyncDestinazione.codice_destinazione, SyncDestinazione.indirizzo)
        .filter(SyncDestinazione.codice_destinazione.in_(destination_codes))
        .all()
        if destination_codes
        else []
    )
    indirizzo_by_destination = {d: (i or "").strip() or None for d, i in dest_rows}

    result: dict[tuple[str, int], _OrderLineReadabilityContext] = {}
    for key, row in base_rows.items():
        destination_display: str | None = None
        identity = destination_identity_by_key.get(key)
        if identity is not None:
            kind, raw_code = identity
            if kind == "main":
                cfg_code = f"MAIN:{raw_code}"
                destination_display = (
                    nickname_by_code.get(cfg_code)
                    or ragione_sociale_by_customer.get(raw_code)
                    or raw_code
                )
            else:
                destination_display = (
                    nickname_by_code.get(raw_code)
                    or indirizzo_by_destination.get(raw_code)
                    or raw_code
                )

        from datetime import datetime as _dt
        requested_delivery: date | None = None
        if row.expected_delivery_date is not None:
            requested_delivery = (
                row.expected_delivery_date.date()
                if isinstance(row.expected_delivery_date, _dt)
                else row.expected_delivery_date
            )

        desc_parts = _normalize_description_parts(
            [(row.article_description_segment or "")] + description_map[key]
        )
        result[key] = _OrderLineReadabilityContext(
            article_code=article_map[key],
            order_reference=row.order_reference,
            line_reference=row.line_reference,
            open_qty=open_qty_map[key],
            requested_delivery_date=requested_delivery,
            description_parts=desc_parts,
            full_order_line_description=_display_description_from_parts(desc_parts, article_map[key]),
            requested_destination_display=destination_display,
        )
    return result


def _resolve_by_article_requested_destination_display(
    article_code: str,
    earliest_customer_delivery_date: date | None,
    contexts: dict[tuple[str, int], _OrderLineReadabilityContext],
) -> str | None:
    if earliest_customer_delivery_date is None:
        return None
    labels = {
        c.requested_destination_display
        for c in contexts.values()
        if c.article_code == article_code
        and c.open_qty > Decimal("0")
        and c.requested_delivery_date == earliest_customer_delivery_date
        and c.requested_destination_display is not None
    }
    if len(labels) == 1:
        return next(iter(labels))
    if len(labels) > 1:
        return "Multiple"
    return None


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


def _earliest_delivery_from_lines(
    line_data: list[tuple[Decimal, date | None]],
) -> date | None:
    """Data richiesta cliente minima tra righe aperte con data valorizzata."""
    dates = [delivery_date for _, delivery_date in line_data if delivery_date is not None]
    if not dates:
        return None
    return min(dates)


# ─── Proposal preview (TASK-V2-151) ──────────────────────────────────────────

@dataclass
class _SyncArticoloProposalData:
    """Dati SyncArticolo necessari per il preview full-bar (pre-caricati in batch)."""
    occorrente: Decimal | None
    scarto: Decimal | None
    raw_material_code: str | None


def _load_sync_articolo_proposal_data(
    session: Session,
    article_codes: set[str],
) -> dict[str, _SyncArticoloProposalData]:
    """Batch-load dati SyncArticolo (occorrente, scarto, raw_material_code) per il preview proposal."""
    if not article_codes:
        return {}
    rows = session.query(SyncArticolo).filter(
        func.upper(func.trim(SyncArticolo.codice_articolo)).in_(article_codes)
    ).all()
    result: dict[str, _SyncArticoloProposalData] = {}
    for art in rows:
        key = art.codice_articolo.strip().upper()
        raw_mat = (art.materiale_grezzo_codice or "").strip() or None
        result[key] = _SyncArticoloProposalData(
            occorrente=art.quantita_materiale_grezzo_occorrente,
            scarto=art.quantita_materiale_grezzo_scarto,
            raw_material_code=raw_mat,
        )
    return result


def _load_raw_material_bar_lengths(
    session: Session,
    raw_material_codes: set[str],
) -> dict[str, Decimal | None]:
    """Batch-load raw_bar_length_mm dai CoreArticoloConfig dei materiali grezzi."""
    if not raw_material_codes:
        return {}
    cfgs = session.query(CoreArticoloConfig).filter(
        func.upper(CoreArticoloConfig.codice_articolo).in_(raw_material_codes)
    ).all()
    return {
        cfg.codice_articolo.strip().upper(): cfg.raw_bar_length_mm
        for cfg in cfgs
    }


_FULL_BAR_LOGIC_KEYS: frozenset[str] = frozenset({
    "proposal_full_bar_v1",
    "proposal_full_bar_v2_capacity_floor",
    "proposal_multi_bar_v1_capacity_floor",
})

_LOGIC_LABELS: dict[str, str] = {
    "proposal_target_pieces_v1": "Target pezzi",
    "proposal_required_qty_total_v1": "Pezzi (alias)",
    "proposal_full_bar_v1": "Barre intere",
    "proposal_full_bar_v2_capacity_floor": "Barre intere v2",
    "proposal_multi_bar_v1_capacity_floor": "Fasci",
}


@dataclass(frozen=True)
class _ProposalPreview:
    proposal_status: str
    proposal_qty_computed: Decimal
    requested_proposal_logic_key: str
    effective_proposal_logic_key: str
    proposal_fallback_reason: str | None
    proposal_reason_summary: str
    proposal_local_warnings: list[str]
    note_fragment: str | None


def _compute_proposal_preview_v1(
    item: "PlanningCandidateItem",
    article_info: "_ArticoloInfo | None",
    logic_config: object,
    sync_proposal_data: dict[str, _SyncArticoloProposalData],
    raw_bar_lengths: dict[str, "Decimal | None"],
) -> _ProposalPreview:
    """Preview proposta per il pannello destra `Proposal` — contratto TASK-V2-151.

    Calcolo lightweight senza persistenza workspace:
    - logica target_pieces: triviale (qty = required_qty_total, senza query aggiuntive)
    - logica full-bar/multi-bar: usa dati pre-caricati in batch (occorrente, scarto, raw_bar_length_mm)
    - capacity_effective_qty: ricostruita da stock_effective_qty + capacity_headroom_now_qty
      (esatta per stock >= 0; stima conservativa per stock < 0)

    Non modifica primary_driver, reason_code, release_status del candidate.
    Importa production_proposals.logic lazy per evitare circular import.
    """
    # Lazy imports per evitare circular import (planning_candidates <-> production_proposals)
    from nssp_v2.core.production_proposals.logic import (  # noqa: PLC0415
        compute_full_bar_qty as _compute_full_bar_qty,
        compute_full_bar_qty_v2_capacity_floor as _compute_full_bar_v2,
        compute_multi_bar_qty_v1_capacity_floor as _compute_multi_bar_v1,
        merge_logic_params as _merge_logic_params,
    )

    req_total: Decimal = item.required_qty_total if item.required_qty_total is not None else item.required_qty_minimum

    # Resolve logica richiesta
    article_logic_key: str | None = article_info.proposal_logic_key if article_info else None
    requested_logic_key: str = article_logic_key or logic_config.default_logic_key
    global_params: dict = dict(logic_config.logic_params_by_key.get(requested_logic_key, {}))
    article_params: dict = article_info.proposal_logic_article_params if article_info else {}
    params_snapshot: dict = _merge_logic_params(global_params, article_params)

    effective_logic_key: str = requested_logic_key
    fallback_reason: str | None = None
    note_fragment: str | None = None
    local_warnings: list[str] = []
    proposed_qty: Decimal = req_total

    if requested_logic_key in _FULL_BAR_LOGIC_KEYS:
        sync_data = sync_proposal_data.get(item.article_code)
        raw_material_code = sync_data.raw_material_code if sync_data else None
        occorrente = sync_data.occorrente if sync_data else None
        scarto = sync_data.scarto if sync_data else None
        raw_bar_length_mm = raw_bar_lengths.get(raw_material_code) if raw_material_code else None

        if raw_bar_length_mm is None:
            local_warnings.append("missing_raw_bar_length")

        # Ricostruzione capacity_effective_qty (approssimazione)
        if item.capacity_headroom_now_qty is not None and item.stock_effective_qty is not None:
            capacity_effective_qty: Decimal | None = item.stock_effective_qty + item.capacity_headroom_now_qty
        else:
            capacity_effective_qty = None

        if requested_logic_key == "proposal_multi_bar_v1_capacity_floor":
            bar_multiple_raw = params_snapshot.get("bar_multiple")
            try:
                bar_multiple = int(bar_multiple_raw) if bar_multiple_raw is not None else None
            except (TypeError, ValueError):
                bar_multiple = None
            fb_result = _compute_multi_bar_v1(
                required_qty_total=req_total,
                customer_shortage_qty=item.customer_shortage_qty,
                availability_qty=item.availability_qty,
                capacity_effective_qty=capacity_effective_qty,
                raw_bar_length_mm=raw_bar_length_mm,
                occorrente=occorrente,
                scarto=scarto,
                bar_multiple=bar_multiple,
            )
        elif requested_logic_key == "proposal_full_bar_v2_capacity_floor":
            fb_result = _compute_full_bar_v2(
                required_qty_total=req_total,
                customer_shortage_qty=item.customer_shortage_qty,
                availability_qty=item.availability_qty,
                capacity_effective_qty=capacity_effective_qty,
                raw_bar_length_mm=raw_bar_length_mm,
                occorrente=occorrente,
                scarto=scarto,
            )
        else:
            fb_result = _compute_full_bar_qty(
                required_qty_total=req_total,
                customer_shortage_qty=item.customer_shortage_qty,
                availability_qty=item.availability_qty,
                capacity_effective_qty=capacity_effective_qty,
                raw_bar_length_mm=raw_bar_length_mm,
                occorrente=occorrente,
                scarto=scarto,
            )

        if fb_result.used_fallback:
            effective_logic_key = "proposal_target_pieces_v1"
            fallback_reason = fb_result.fallback_reason
            proposed_qty = req_total
        else:
            proposed_qty = fb_result.proposed_qty
            bars = fb_result.bars_required
            if requested_logic_key == "proposal_multi_bar_v1_capacity_floor":
                note_fragment = f"FASCI x{bars}"
            else:
                note_fragment = f"BAR x{bars}"

    # ordine_linea_mancante: errore bloccante export.
    # Applicabile solo ai candidate by_customer_order_line: in questa modalita ogni riga ha
    # un line_reference esplicito e l'export EasyJob richiede la riga ordine collegata.
    # Per by_article la mancanza di line_reference e normale (aggregato): non e un errore (TASK-V2-155).
    ordine_linea_mancante = (
        item.planning_mode == "by_customer_order_line"
        and item.line_reference is None
    )

    if ordine_linea_mancante:
        proposal_status = "Error"
    elif fallback_reason is not None or local_warnings:
        proposal_status = "Need review"
    else:
        proposal_status = "Valid for export"

    logic_label = _LOGIC_LABELS.get(effective_logic_key, effective_logic_key)
    if ordine_linea_mancante:
        reason_summary = "Riga ordine mancante — non esportabile"
    elif fallback_reason:
        reason_summary = f"{logic_label} (fallback: {fallback_reason}) — qty: {proposed_qty:.0f}"
    elif note_fragment:
        reason_summary = f"{logic_label} — {note_fragment} — qty: {proposed_qty:.0f}"
    else:
        reason_summary = f"{logic_label} — qty: {proposed_qty:.0f}"

    return _ProposalPreview(
        proposal_status=proposal_status,
        proposal_qty_computed=proposed_qty,
        requested_proposal_logic_key=requested_logic_key,
        effective_proposal_logic_key=effective_logic_key,
        proposal_fallback_reason=fallback_reason,
        proposal_reason_summary=reason_summary,
        proposal_local_warnings=local_warnings,
        note_fragment=note_fragment,
    )


def _compute_priority_score_v1_basic(
    nearest_delivery_date: date | None,
    customer_shortage_qty: Decimal | None,
    stock_replenishment_qty: Decimal | None,
    stock_effective_qty: Decimal | None,
    target_stock_qty: Decimal | None,
    release_status: str | None,
    active_warnings_count: int,
) -> tuple[float, str]:
    """Punteggio di priorita V1 Basic — contratto DL-ARCH-V2-044, TASK-V2-149.

    Formula additiva (clampata 0..100):
        priority_score = time_urgency + customer_pressure + stock_pressure
                         - release_penalty - warning_penalty

    Componenti:
    - time_urgency (0–35): fasce step-function sulla data rilevante.
    - customer_pressure (0–40): severita shortage cliente per quantita.
    - stock_pressure (0–24): ratio stock_effective_qty / target_stock_qty.
    - release_penalty (0–18): sottrazione per release status sfavorevole.
    - warning_penalty (0–12): sottrazione per warning attivi.

    Non sostituisce primary_driver, reason_code, reason_text o release_status.
    Ritorna (score, band) dove band in ('low', 'medium', 'high', 'critical').
    """
    today = date.today()

    # ── time_urgency ──────────────────────────────────────────────────────────
    time_urgency = 0.0
    if nearest_delivery_date is not None:
        days_ahead = (nearest_delivery_date - today).days
        if days_ahead <= 7:
            time_urgency = 35.0
        elif days_ahead <= 15:
            time_urgency = 28.0
        elif days_ahead <= 30:
            time_urgency = 20.0
        elif days_ahead <= 60:
            time_urgency = 10.0
        else:
            time_urgency = 4.0

    # ── customer_pressure ─────────────────────────────────────────────────────
    customer_pressure = 0.0
    shortage = float(customer_shortage_qty or 0)
    if shortage > 0:
        customer_pressure = 20.0
        if shortage >= 1000:
            customer_pressure += 20.0
        elif shortage >= 500:
            customer_pressure += 15.0
        elif shortage >= 100:
            customer_pressure += 10.0
        else:
            customer_pressure += 5.0
    customer_pressure = min(customer_pressure, 40.0)

    # ── stock_pressure ────────────────────────────────────────────────────────
    stock_pressure = 0.0
    replenishment = float(stock_replenishment_qty or 0)
    target = float(target_stock_qty or 0)
    if replenishment > 0 and target > 0:
        stock_eff = float(stock_effective_qty or 0)
        ratio = stock_eff / target
        if ratio >= 1.0:
            stock_pressure = 0.0
        elif ratio >= 0.75:
            stock_pressure = 4.0
        elif ratio >= 0.50:
            stock_pressure = 8.0
        elif ratio >= 0.25:
            stock_pressure = 14.0
        elif ratio >= 0.0:
            stock_pressure = 20.0
        else:
            stock_pressure = 24.0

    # ── release_penalty ───────────────────────────────────────────────────────
    if release_status == "launchable_partially":
        release_penalty = 8.0
    elif release_status == "blocked_by_capacity_now":
        release_penalty = 18.0
    else:
        release_penalty = 0.0

    # ── warning_penalty ───────────────────────────────────────────────────────
    if active_warnings_count == 0:
        warning_penalty = 0.0
    elif active_warnings_count == 1:
        warning_penalty = 4.0
    elif active_warnings_count <= 3:
        warning_penalty = 8.0
    else:
        warning_penalty = 12.0

    raw = time_urgency + customer_pressure + stock_pressure - release_penalty - warning_penalty
    score = round(max(0.0, min(100.0, raw)), 2)

    # ── band ──────────────────────────────────────────────────────────────────
    if score >= 75:
        band = "critical"
    elif score >= 50:
        band = "high"
    elif score >= 25:
        band = "medium"
    else:
        band = "low"

    return score, band


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
    readability_contexts = _load_order_line_readability_contexts(session, article_codes_upper)

    incoming = _compute_incoming_supply_by_article(session, forza_completata_ids, article_codes_upper)
    demand = _compute_customer_demand(session)

    # Customer horizon — data_consegna piu vicina per articolo (TASK-V2-100)
    nearest_deliveries: dict[str, date | None] = {}

    # Stock horizon — impegni per articolo con data_consegna (per capping — TASK-V2-101)
    open_commitments_with_dates = _load_open_commitments_by_article_with_dates(session, article_codes_upper)
    nearest_deliveries = {
        article_code: _earliest_delivery_from_lines(line_data)
        for article_code, line_data in open_commitments_with_dates.items()
    }

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
        assert fav is not None

        line_data = open_commitments_with_dates.get(avail.article_code, [])

        # Rebase Core (TASK-V2-145, DL-ARCH-V2-042 §3): customer_shortage_qty basata su fav completo.
        # customer_horizon_days non influenza piu la candidatura — vive nel layer priority_score / UI.
        shortage = customer_shortage_qty_v1(fav)

        # Stock horizon (DL-ARCH-V2-031 §4): capping impegni SOLO su effective_stock_months.
        # customer_horizon_days non deve influenzare la componente scorta.
        if target_qty is not None:
            if art.effective_stock_months is not None:
                lookahead_days = int(round(float(art.effective_stock_months) * 30))
                lookahead_date = date.today() + timedelta(days=lookahead_days)
                capped_committed = _capped_commitments_from_lines(line_data, lookahead_date)
            else:
                capped_committed = avail.committed_qty
            stock_horizon_avail = stock_horizon_availability_qty_v1(
                stock_eff, avail.customer_set_aside_qty, capped_committed, incoming_qty
            )
        else:
            stock_horizon_avail = avail_eff  # no stock policy: nessun capping

        stock_trigger_active = (
            trigger_qty is not None and stock_horizon_avail < trigger_qty
        )
        if shortage <= Decimal("0") and not stock_trigger_active:
            continue

        # Reason code: shortage cliente prioritario; stock trigger come secondo motivo
        if shortage > Decimal("0"):
            reason_code = "future_availability_negative"
            reason_text = "Disponibilita futura negativa anche considerando la supply in corso"
        else:
            reason_code = "stock_below_trigger"
            reason_text = "Disponibilita futura inferiore alla soglia di trigger scorta"

        replenishment = stock_replenishment_qty_v1(target_qty, stock_horizon_avail)
        primary_driver = resolve_primary_driver_v1(shortage, replenishment)
        # Hardening: i candidate con reason stock_below_trigger sono stock-driven
        # anche quando replenishment non e valorizzata (es. target non configurato).
        if reason_code == "stock_below_trigger":
            primary_driver = "stock"
        req = required_qty_minimum_by_primary_driver_v1(shortage, replenishment, primary_driver)
        req_total = required_qty_total_v1(shortage, replenishment)
        earliest_customer_delivery = (
            nearest_deliveries.get(avail.article_code) if shortage > Decimal("0") else None
        )
        requested_destination_display = (
            _resolve_by_article_requested_destination_display(
                avail.article_code,
                earliest_customer_delivery,
                readability_contexts,
            )
            if shortage > Decimal("0")
            else None
        )

        # Customer horizon flag (TASK-V2-100, DL-ARCH-V2-031 §3) — usa customer_horizon_days
        within_horizon = _is_within_customer_horizon(
            nearest_deliveries.get(avail.article_code),
            customer_horizon_days,
        )

        # Release now contract (TASK-V2-128) — solo se capacity_effective_qty disponibile
        capacity_effective_qty = metrics.capacity_effective_qty if metrics else None
        if capacity_effective_qty is not None and req_total is not None:
            headroom = capacity_headroom_now_qty_v1(capacity_effective_qty, avail.inventory_qty)
            rel_max = release_qty_now_max_v1(req_total, headroom)
            rel_status = release_status_v1(rel_max, req_total)
        else:
            headroom = None
            rel_max = None
            rel_status = None

        # Ordini aperti per questo articolo — sottosezione Ordini aperti (TASK-V2-143).
        # Filtra dal readability_contexts le righe di questo articolo con open_qty > 0,
        # ordinando per requested_delivery_date crescente (None in fondo).
        open_lines = [
            PlanningOpenOrderLine(
                order_reference=ctx.order_reference,
                line_reference=ctx.line_reference,
                requested_delivery_date=ctx.requested_delivery_date,
                requested_destination_display=ctx.requested_destination_display,
                open_qty=ctx.open_qty,
            )
            for ctx in readability_contexts.values()
            if ctx.article_code == avail.article_code and ctx.open_qty > Decimal("0")
        ]
        open_lines.sort(key=lambda ln: (ln.requested_delivery_date is None, ln.requested_delivery_date or date.min))

        candidates.append((req, PlanningCandidateItem(
            source_candidate_id=f"by_article::{avail.article_code}",
            article_code=avail.article_code,
            display_label=art.display_label,
            description_parts=art.description_parts,
            display_description=art.display_description,
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
            # by_article — giacenza effettiva e disponibilità (TASK-V2-143)
            stock_effective_qty=stock_eff,
            availability_qty=avail_eff,
            customer_open_demand_qty=demand_qty,
            incoming_supply_qty=incoming_qty,
            future_availability_qty=fav,
            # ordini aperti per articolo (TASK-V2-143)
            open_order_lines=open_lines,
            # stock policy breakdown (TASK-V2-085)
            customer_shortage_qty=shortage,
            stock_replenishment_qty=replenishment,
            required_qty_total=req_total,
            target_stock_qty=target_qty,
            primary_driver=primary_driver,
            # customer horizon (TASK-V2-100, TASK-V2-102)
            is_within_customer_horizon=within_horizon,
            earliest_customer_delivery_date=earliest_customer_delivery,
            nearest_delivery_date=nearest_deliveries.get(avail.article_code),
            requested_destination_display=requested_destination_display,
            # release now contract (TASK-V2-128)
            required_qty_eventual=req_total,
            capacity_headroom_now_qty=headroom,
            release_qty_now_max=rel_max,
            release_status=rel_status,
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
    readability_contexts = _load_order_line_readability_contexts(session, article_codes_upper)

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
        readability_ctx = readability_contexts.get(key)

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
        order_line_desc = (
            readability_ctx.full_order_line_description
            if readability_ctx is not None
            else (riga.article_description_segment or "").strip() or None
        )
        description_parts = (
            readability_ctx.description_parts
            if readability_ctx is not None
            else _normalize_description_parts([order_line_desc])
        )
        display = _display_description_from_parts(description_parts, canonical)

        # Misura dalla riga ordine (DL-ARCH-V2-028 §3)
        misura_col = (riga.article_measure or "").strip() or None
        requested_delivery_date = (
            readability_ctx.requested_delivery_date
            if readability_ctx is not None
            else (riga.expected_delivery_date.date() if riga.expected_delivery_date is not None else None)
        )
        requested_destination_display = (
            readability_ctx.requested_destination_display if readability_ctx is not None else None
        )

        candidates.append((req, PlanningCandidateItem(
            source_candidate_id=f"by_customer_order_line::{canonical}::{riga.order_reference or ''}::{riga.line_reference}",
            article_code=canonical,
            display_label=display,
            description_parts=description_parts,
            display_description=display,
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
            full_order_line_description=order_line_desc,
            requested_delivery_date=requested_delivery_date,
            requested_destination_display=requested_destination_display,
            line_open_demand_qty=line_demand,
            linked_incoming_supply_qty=linked_qty,
            line_future_coverage_qty=coverage,
        )))
    return candidates


# ─── Query principale ─────────────────────────────────────────────────────────

def list_planning_candidates_v1(
    session: Session,
    customer_horizon_days: int = 30,
    user_areas: list[str] | None = None,
    is_admin: bool = False,
) -> list[PlanningCandidateItem]:
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

    active_warnings_by_article = _load_active_article_warnings(
        session,
        user_areas=user_areas or [],
        is_admin=is_admin,
    )

    # Pre-load per proposal preview (TASK-V2-151): 2 query batch aggiuntive.
    # Lazy import per evitare circular import (planning_candidates <-> production_proposals)
    from nssp_v2.core.production_proposals.config import get_proposal_logic_config as _get_proposal_logic_config  # noqa: PLC0415
    proposal_logic_config = _get_proposal_logic_config(session)
    articoli_info_map = {a.article_code: a for a in articoli}
    candidate_codes = {item.article_code for _, item in (candidates_ba + candidates_col)}
    sync_proposal_data = _load_sync_articolo_proposal_data(session, candidate_codes)
    raw_material_codes = {
        d.raw_material_code
        for d in sync_proposal_data.values()
        if d.raw_material_code
    }
    raw_bar_lengths = _load_raw_material_bar_lengths(session, raw_material_codes)

    all_candidates = candidates_ba + candidates_col
    all_candidates.sort(key=lambda t: t[0], reverse=True)
    result: list[PlanningCandidateItem] = []
    for _, item in all_candidates:
        warnings = active_warnings_by_article.get(item.article_code, [])
        # priority_score_v1_basic iniettato qui: ha accesso a warnings definitivi (TASK-V2-149,
        # DL-ARCH-V2-044). Usa nearest_delivery_date (by_article) o requested_delivery_date
        # (by_customer_order_line). Non modifica primary_driver / reason_code / release_status.
        nearest = item.nearest_delivery_date or item.requested_delivery_date
        score, band = _compute_priority_score_v1_basic(
            nearest_delivery_date=nearest,
            customer_shortage_qty=item.customer_shortage_qty,
            stock_replenishment_qty=item.stock_replenishment_qty,
            stock_effective_qty=item.stock_effective_qty,
            target_stock_qty=item.target_stock_qty,
            release_status=item.release_status,
            active_warnings_count=len(warnings),
        )
        # Proposal preview iniettato qui: contratto read-only per la scheda destra
        # `Proposal` del workspace planning (TASK-V2-151).
        art_info = articoli_info_map.get(item.article_code)
        proposal_preview = _compute_proposal_preview_v1(
            item, art_info, proposal_logic_config, sync_proposal_data, raw_bar_lengths
        )
        result.append(item.model_copy(update={
            "active_warnings": warnings,
            "active_warning_codes": [w.code for w in warnings],
            "priority_score": score,
            "priority_band": band,
            "proposal_status": proposal_preview.proposal_status,
            "proposal_qty_computed": proposal_preview.proposal_qty_computed,
            "requested_proposal_logic_key": proposal_preview.requested_proposal_logic_key,
            "effective_proposal_logic_key": proposal_preview.effective_proposal_logic_key,
            "proposal_fallback_reason": proposal_preview.proposal_fallback_reason,
            "proposal_reason_summary": proposal_preview.proposal_reason_summary,
            "proposal_local_warnings": proposal_preview.proposal_local_warnings,
            "note_fragment": proposal_preview.note_fragment,
        }))
    return result
