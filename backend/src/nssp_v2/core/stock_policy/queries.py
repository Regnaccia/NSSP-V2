"""
Query Core slice `stock_policy` metrics V1 (TASK-V2-084, TASK-V2-087, TASK-V2-088, TASK-V2-099, DL-ARCH-V2-030).

Regole:
- legge da sync_mag_reale (mai da Easy diretto)
- legge da sync_articoli per i dati articolo (contenitori_magazzino)
- legge core_articolo_config + articolo_famiglie per i valori di policy effettivi
- legge core_stock_logic_config per strategy e parametri (TASK-V2-086)
- non modifica mai le tabelle di input
- restituisce computed read model (non persistito)
- computed_at e il timestamp del calcolo

Perimetro articoli (TASK-V2-088, TASK-V2-099):
- solo articoli con planning_mode = by_article
  (effective_aggrega_codice_in_produzione = True)
- E con gestione_scorte_attiva = True
  (effective_gestione_scorte_attiva = True — TASK-V2-099)
- articoli senza planning_mode o con gestione scorte disattivata sono esclusi

Driver movimenti V1 (TASK-V2-088):
- uscite di magazzino: quantita_scaricata > 0
- nessun filtro su causale_movimento_codice in V1
- min_movements: soglia minima righe movimento per articolo nel periodo

Calcolo mensile (monthly_stock_base_from_sales_v1 — TASK-V2-087):
- aggrega quantita_scaricata da sync_mag_reale PER MESE nel periodo di lookback
- lookback = max(params.get('windows_months', [12, 6, 3])) mesi
- algoritmo: finestre multiple, percentile, filtro z-score

Capacity (capacity_from_containers_v1 — logica fissa):
- parsa contenitori_magazzino come Decimal
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.stock_policy.config import CAPACITY_LOGIC_KEY, get_stock_logic_config
from nssp_v2.core.stock_policy.logic import (
    compute_target_stock_qty,
    compute_trigger_stock_qty,
    estimate_capacity_from_containers_v1,
    estimate_monthly_stock_base_from_sales_v1,
    estimate_monthly_stock_base_weighted_v2,
    estimate_monthly_stock_base_segmented_v1,
    resolve_capacity_effective,
)
from nssp_v2.core.stock_policy.read_models import StockMetricsItem
from nssp_v2.shared.article_codes import normalize_article_code
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.mag_reale.models import SyncMagReale

_DEFAULT_WINDOWS_MONTHS = [12, 6, 3]

_MONTHLY_BASE_DISPATCH = {
    "monthly_stock_base_from_sales_v1": estimate_monthly_stock_base_from_sales_v1,
    "monthly_stock_base_weighted_v2": estimate_monthly_stock_base_weighted_v2,
    "monthly_stock_base_segmented_v1": estimate_monthly_stock_base_segmented_v1,
}


def _estimate_monthly_base(
    strategy_key: str,
    monthly_sales: dict,
    params: dict,
    total_movements: int,
) -> "Decimal | None":
    """Dispatch alla funzione di stima corretta in base alla strategy_key."""
    fn = _MONTHLY_BASE_DISPATCH.get(strategy_key)
    if fn is None:
        # Fallback sicuro alla v1 se la strategy non e nel dispatch
        fn = estimate_monthly_stock_base_from_sales_v1
    return fn(monthly_sales, params, total_movements=total_movements)


def _months_ago(months: int) -> datetime:
    """Restituisce datetime naive pari a 'oggi - N mesi' (giorno 1 del mese)."""
    now = datetime.now()
    year = now.year
    month = now.month - months
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)


def _resolve_stock_months(
    override: Decimal | None,
    family_default: Decimal | None,
) -> Decimal | None:
    """Risoluzione effective stock policy — stessa regola planning policy."""
    if override is not None:
        return override
    return family_default


def list_stock_metrics_v1(session: Session) -> list[StockMetricsItem]:
    """Calcola le metriche stock policy V1 per tutti gli articoli attivi.

    Algoritmo:
    1. Legge config logiche stock (strategy + params)
    2. Aggrega quantita_scaricata da sync_mag_reale PER MESE nel periodo di lookback
       (lookback = max delle finestre configurate)
    3. Per ogni articolo attivo:
       - calcola monthly_stock_base_qty con la strategy attiva (multi-finestra)
       - stima capacity_calculated_qty da contenitori_magazzino
       - risolve effective_stock_months / trigger_months dalla policy config
       - calcola target/trigger secondo le formule DL-ARCH-V2-030 §5

    Gli articoli senza configurazione stock producono metriche con None
    per target_stock_qty e trigger_stock_qty, ma mantengono i valori di
    base (monthly_stock_base_qty, capacity_calculated_qty) dove disponibili.
    """
    config = get_stock_logic_config(session)
    params = dict(config.monthly_base_params)
    windows_months: list[int] = [int(w) for w in params.get("windows_months", _DEFAULT_WINDOWS_MONTHS)]
    if not windows_months:
        windows_months = _DEFAULT_WINDOWS_MONTHS
    max_window = max(windows_months)

    cutoff_dt = _months_ago(max_window)
    computed_at = datetime.now(timezone.utc)

    # ─── Aggregazione uscite mag_reale per articolo e mese ────────────────────
    # Driver V1: quantita_scaricata > 0 (uscite di magazzino — TASK-V2-088)
    sales_rows = (
        session.query(
            func.upper(func.trim(SyncMagReale.codice_articolo)).label("article_code"),
            func.extract("year", SyncMagReale.data_movimento).label("year"),
            func.extract("month", SyncMagReale.data_movimento).label("month"),
            func.sum(SyncMagReale.quantita_scaricata).label("total_scaricata"),
            func.count().label("movement_count"),
        )
        .filter(
            SyncMagReale.codice_articolo.isnot(None),
            SyncMagReale.data_movimento >= cutoff_dt,
            SyncMagReale.quantita_scaricata > 0,
        )
        .group_by(
            func.upper(func.trim(SyncMagReale.codice_articolo)),
            func.extract("year", SyncMagReale.data_movimento),
            func.extract("month", SyncMagReale.data_movimento),
        )
        .all()
    )
    # sales_map: article_code -> {(year, month): total_scaricata}
    # movements_map: article_code -> total movement rows in period
    sales_map: dict[str, dict[tuple[int, int], Decimal]] = {}
    movements_map: dict[str, int] = {}
    for row in sales_rows:
        if row.total_scaricata is None:
            continue
        code = row.article_code
        if code not in sales_map:
            sales_map[code] = {}
        sales_map[code][(int(row.year), int(row.month))] = Decimal(str(row.total_scaricata))
        movements_map[code] = movements_map.get(code, 0) + int(row.movement_count)

    # ─── Famiglie attive ──────────────────────────────────────────────────────
    famiglie: dict[str, ArticoloFamiglia] = {
        f.code: f
        for f in session.query(ArticoloFamiglia).filter(ArticoloFamiglia.is_active == True).all()  # noqa: E712
    }

    # ─── Articoli attivi con config ───────────────────────────────────────────
    rows = (
        session.query(SyncArticolo, CoreArticoloConfig)
        .outerjoin(
            CoreArticoloConfig,
            SyncArticolo.codice_articolo == CoreArticoloConfig.codice_articolo,
        )
        .filter(SyncArticolo.attivo == True)  # noqa: E712
        .order_by(SyncArticolo.codice_articolo)
        .all()
    )

    result: list[StockMetricsItem] = []
    for art, art_config in rows:
        canonical = normalize_article_code(art.codice_articolo)
        if canonical is None:
            continue

        # Risoluzione policy stock effettiva
        famiglia = famiglie.get(art_config.famiglia_code) if art_config and art_config.famiglia_code else None

        # Filtro planning_mode = by_article (TASK-V2-088)
        # effective_aggrega_codice_in_produzione = True <-> by_article
        override_aggrega = art_config.override_aggrega_codice_in_produzione if art_config else None
        family_aggrega = famiglia.aggrega_codice_in_produzione if famiglia else None
        effective_aggrega = override_aggrega if override_aggrega is not None else family_aggrega
        if effective_aggrega is not True:
            continue

        # Filtro gestione_scorte_attiva (TASK-V2-099)
        # Solo articoli con effective_gestione_scorte_attiva = True entrano nel perimetro stock policy
        override_gestione = art_config.override_gestione_scorte_attiva if art_config else None
        family_gestione = famiglia.gestione_scorte_attiva if famiglia else None
        effective_gestione = override_gestione if override_gestione is not None else family_gestione
        if effective_gestione is not True:
            continue

        family_stock_months = famiglia.stock_months if famiglia else None
        family_stock_trigger = famiglia.stock_trigger_months if famiglia else None
        override_stock_months = art_config.override_stock_months if art_config else None
        override_stock_trigger = art_config.override_stock_trigger_months if art_config else None
        capacity_override = art_config.capacity_override_qty if art_config else None

        effective_stock_months = _resolve_stock_months(override_stock_months, family_stock_months)
        effective_stock_trigger = _resolve_stock_months(override_stock_trigger, family_stock_trigger)

        # Calcolo metriche
        monthly_sales = sales_map.get(canonical, {})
        total_movements = movements_map.get(canonical, 0)
        monthly_base = _estimate_monthly_base(
            config.monthly_base_strategy_key, monthly_sales, params, total_movements
        )
        capacity_calculated = estimate_capacity_from_containers_v1(
            art.contenitori_magazzino,
            art.peso_grammi,
            dict(config.capacity_logic_params),
        )
        capacity_effective = resolve_capacity_effective(capacity_calculated, capacity_override)
        target = compute_target_stock_qty(capacity_effective, effective_stock_months, monthly_base)
        trigger = compute_trigger_stock_qty(effective_stock_trigger, monthly_base)

        result.append(StockMetricsItem(
            article_code=canonical,
            monthly_stock_base_qty=monthly_base,
            capacity_calculated_qty=capacity_calculated,
            capacity_override_qty=capacity_override,
            capacity_effective_qty=capacity_effective,
            target_stock_qty=target,
            trigger_stock_qty=trigger,
            strategy_key=config.monthly_base_strategy_key,
            params_snapshot=params,
            algorithm_key=CAPACITY_LOGIC_KEY,
            computed_at=computed_at,
        ))

    return result
