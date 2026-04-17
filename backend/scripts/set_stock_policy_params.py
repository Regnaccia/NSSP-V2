"""
Aggiorna i parametri della stock policy nel DB e confronta i risultati
prima/dopo il cambiamento.

Uso:
    cd backend
    .venv\\Scripts\\activate

    # Mostra configurazione attuale senza modificare
    python scripts/set_stock_policy_params.py --dry-run

    # Applica i parametri raccomandati (v1 con percentile 70, min_nonzero_months 2)
    python scripts/set_stock_policy_params.py --apply-v1-recommended

    # Applica la nuova logica v2 con pesi (recente conta di piu)
    python scripts/set_stock_policy_params.py --apply-v2-weighted

    # Applica parametri personalizzati su v1
    python scripts/set_stock_policy_params.py --strategy v1 --percentile 75 --min-nonzero-months 2

    # Applica parametri personalizzati su v2
    python scripts/set_stock_policy_params.py --strategy v2 --percentile 70 --min-nonzero-months 2 --weights 1,2,4
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.stock_policy.config import get_stock_logic_config, set_stock_logic_config
from nssp_v2.core.stock_policy.queries import list_stock_metrics_v1

SEP = "=" * 80
SEP2 = "-" * 60

# ─── Configurazioni predefinite ───────────────────────────────────────────────

# V1 con parametri originali (quello che era in DB)
PARAMS_V1_ORIGINAL = {
    "windows_months": [12, 6, 3],
    "percentile": 90,
    "zscore_threshold": 2.0,
    "min_nonzero_months": 4,
    "min_movements": 3,
}

# V1 raccomandati dopo analisi dati reali
PARAMS_V1_RECOMMENDED = {
    "windows_months": [12, 6, 3],
    "percentile": 70,
    "zscore_threshold": 2.0,
    "min_nonzero_months": 2,
    "min_movements": 3,
}

# V2 con pesi crescenti verso il recente
PARAMS_V2_WEIGHTED = {
    "windows_months": [12, 6, 3],
    "window_weights": [1, 2, 3],
    "percentile": 70,
    "zscore_threshold": 2.0,
    "min_nonzero_months": 2,
    "min_movements": 3,
}

CAPACITY_PARAMS = {"max_container_weight_kg": 25.0}


def _fmt(v, decimals=1):
    if v is None:
        return "None"
    try:
        return f"{float(v):.{decimals}f}"
    except Exception:
        return str(v)


def _summarize_metrics(metrics: list) -> dict:
    """Calcola statistiche riassuntive da una lista di StockMetricsItem."""
    total = len(metrics)
    with_base = [m for m in metrics if m.monthly_stock_base_qty is not None]
    with_target = [m for m in metrics if m.target_stock_qty is not None]

    if with_base:
        bases = [float(m.monthly_stock_base_qty) for m in with_base]
        avg_base = sum(bases) / len(bases)
        max_base = max(bases)
    else:
        avg_base = max_base = 0.0

    return {
        "total": total,
        "with_base": len(with_base),
        "without_base": total - len(with_base),
        "pct_with_base": 100 * len(with_base) / total if total else 0,
        "with_target": len(with_target),
        "avg_base": avg_base,
        "max_base": max_base,
    }


def _print_summary(label: str, s: dict) -> None:
    print(f"\n  {label}")
    print(f"  {SEP2}")
    print(f"  Articoli totali nel perimetro : {s['total']}")
    print(f"  Con monthly_base calcolato    : {s['with_base']}  ({s['pct_with_base']:.1f}%)")
    print(f"  Senza monthly_base (None)     : {s['without_base']}")
    print(f"  Con target_stock_qty          : {s['with_target']}")
    print(f"  Avg monthly_base (tra quelli calcolati): {s['avg_base']:.1f}")
    print(f"  Max monthly_base              : {s['max_base']:.1f}")


def _print_top(metrics: list, n: int = 20) -> None:
    with_base = [m for m in metrics if m.monthly_stock_base_qty is not None]
    with_base.sort(key=lambda m: m.monthly_stock_base_qty, reverse=True)
    print(f"\n  {'Codice':<18}  {'Base/mese':>9}  {'Target':>9}  {'Trigger':>9}")
    print(f"  {'-'*18}  {'-'*9}  {'-'*9}  {'-'*9}")
    for m in with_base[:n]:
        print(f"  {m.article_code:<18}  "
              f"{_fmt(m.monthly_stock_base_qty, 1):>9}  "
              f"{_fmt(m.target_stock_qty, 1):>9}  "
              f"{_fmt(m.trigger_stock_qty, 1):>9}")


def _print_config(cfg) -> None:
    print(f"  Strategy : {cfg.monthly_base_strategy_key}")
    print(f"  Params   : {cfg.monthly_base_params}")
    print(f"  Default  : {cfg.is_default}")
    if cfg.updated_at:
        print(f"  Updated  : {cfg.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestione parametri stock policy")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="Mostra configurazione attuale e preview senza modificare il DB")
    mode.add_argument("--apply-v1-recommended", action="store_true",
                      help="Applica parametri v1 raccomandati (percentile=70, min_nonzero=2)")
    mode.add_argument("--apply-v2-weighted", action="store_true",
                      help="Applica v2 con pesi crescenti sul recente (window_weights=[1,2,3])")
    mode.add_argument("--strategy", choices=["v1", "v2"],
                      help="Specifica strategy manuale (usare con --percentile ecc.)")

    parser.add_argument("--percentile", type=int, default=None)
    parser.add_argument("--min-nonzero-months", type=int, default=None)
    parser.add_argument("--min-movements", type=int, default=None)
    parser.add_argument("--zscore-threshold", type=float, default=None)
    parser.add_argument("--windows", type=str, default=None,
                        help="Finestre in mesi separate da virgola, es: 12,6,3")
    parser.add_argument("--weights", type=str, default=None,
                        help="Pesi per finestra (solo v2), es: 1,2,3")
    parser.add_argument("--show-top", type=int, default=20,
                        help="Quanti articoli mostrare in cima alla classifica (default: 20)")

    args = parser.parse_args()

    # Se nessuna modalita specificata, usa dry-run
    if not any([args.dry_run, args.apply_v1_recommended, args.apply_v2_weighted, args.strategy]):
        args.dry_run = True

    with SessionLocal() as session:

        # ─── Configurazione attuale ───────────────────────────────────────────
        print(f"\n{SEP}")
        print("  CONFIGURAZIONE ATTUALE")
        print(SEP)
        current_cfg = get_stock_logic_config(session)
        _print_config(current_cfg)

        # ─── Calcolo risultati attuali ────────────────────────────────────────
        print(f"\n{SEP}")
        print("  RISULTATI CON CONFIGURAZIONE ATTUALE")
        print(SEP)
        current_metrics = list_stock_metrics_v1(session)
        current_summary = _summarize_metrics(current_metrics)
        _print_summary("Statistiche attuali", current_summary)

        if args.dry_run:
            print(f"\n  Top {args.show_top} articoli per monthly_base (configurazione attuale):")
            _print_top(current_metrics, args.show_top)
            print(f"\n{SEP}")
            print("  [DRY RUN] Nessuna modifica applicata al DB.")
            print(f"  Usa --apply-v1-recommended o --apply-v2-weighted per applicare le modifiche.")
            print(SEP)
            return

        # ─── Determina nuovi parametri ────────────────────────────────────────
        if args.apply_v1_recommended:
            new_strategy_key = "monthly_stock_base_from_sales_v1"
            new_params = dict(PARAMS_V1_RECOMMENDED)

        elif args.apply_v2_weighted:
            new_strategy_key = "monthly_stock_base_weighted_v2"
            new_params = dict(PARAMS_V2_WEIGHTED)

        else:  # --strategy manuale
            if args.strategy == "v1":
                new_strategy_key = "monthly_stock_base_from_sales_v1"
                base = dict(PARAMS_V1_RECOMMENDED)
            else:
                new_strategy_key = "monthly_stock_base_weighted_v2"
                base = dict(PARAMS_V2_WEIGHTED)

            new_params = base.copy()
            if args.percentile is not None:
                new_params["percentile"] = args.percentile
            if args.min_nonzero_months is not None:
                new_params["min_nonzero_months"] = args.min_nonzero_months
            if args.min_movements is not None:
                new_params["min_movements"] = args.min_movements
            if args.zscore_threshold is not None:
                new_params["zscore_threshold"] = args.zscore_threshold
            if args.windows is not None:
                new_params["windows_months"] = [int(x) for x in args.windows.split(",")]
            if args.weights is not None:
                new_params["window_weights"] = [int(x) for x in args.weights.split(",")]

        # ─── Preview nuovi parametri ──────────────────────────────────────────
        print(f"\n{SEP}")
        print("  PREVIEW NUOVI PARAMETRI (senza ancora scrivere nel DB)")
        print(SEP)
        print(f"  Strategy : {new_strategy_key}")
        print(f"  Params   : {new_params}")

        # Simula il calcolo con i nuovi parametri senza scrivere nel DB
        # (imposta temporaneamente la config nel session senza commit)
        from nssp_v2.core.stock_policy.config import StockLogicConfig, CAPACITY_LOGIC_KEY
        from nssp_v2.core.stock_policy.queries import _estimate_monthly_base, _months_ago, _resolve_stock_months
        from nssp_v2.core.stock_policy.logic import (
            estimate_capacity_from_containers_v1,
            resolve_capacity_effective,
            compute_target_stock_qty,
            compute_trigger_stock_qty,
        )
        from nssp_v2.core.stock_policy.read_models import StockMetricsItem
        from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
        from nssp_v2.sync.articoli.models import SyncArticolo
        from nssp_v2.sync.mag_reale.models import SyncMagReale
        from nssp_v2.shared.article_codes import normalize_article_code
        from sqlalchemy import func
        from datetime import datetime, timezone

        # Replica la query di list_stock_metrics_v1 con i nuovi parametri
        windows_months = [int(w) for w in new_params.get("windows_months", [12, 6, 3])]
        max_window = max(windows_months)
        cutoff_dt = _months_ago(max_window)
        computed_at = datetime.now(timezone.utc)

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
        sales_map: dict = {}
        movements_map: dict = {}
        for row in sales_rows:
            if row.total_scaricata is None:
                continue
            code = row.article_code
            if code not in sales_map:
                sales_map[code] = {}
            sales_map[code][(int(row.year), int(row.month))] = Decimal(str(row.total_scaricata))
            movements_map[code] = movements_map.get(code, 0) + int(row.movement_count)

        famiglie = {
            f.code: f
            for f in session.query(ArticoloFamiglia).filter(ArticoloFamiglia.is_active == True).all()  # noqa: E712
        }
        art_rows = (
            session.query(SyncArticolo, CoreArticoloConfig)
            .outerjoin(CoreArticoloConfig, SyncArticolo.codice_articolo == CoreArticoloConfig.codice_articolo)
            .filter(SyncArticolo.attivo == True)  # noqa: E712
            .all()
        )

        preview_metrics = []
        cap_params = dict(current_cfg.capacity_logic_params) or CAPACITY_PARAMS
        for art, art_config in art_rows:
            canonical = normalize_article_code(art.codice_articolo)
            if canonical is None:
                continue
            famiglia = famiglie.get(art_config.famiglia_code) if art_config and art_config.famiglia_code else None
            override_aggrega = art_config.override_aggrega_codice_in_produzione if art_config else None
            family_aggrega = famiglia.aggrega_codice_in_produzione if famiglia else None
            effective_aggrega = override_aggrega if override_aggrega is not None else family_aggrega
            if effective_aggrega is not True:
                continue
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

            monthly_sales = sales_map.get(canonical, {})
            total_movements = movements_map.get(canonical, 0)
            monthly_base = _estimate_monthly_base(new_strategy_key, monthly_sales, new_params, total_movements)
            capacity_calculated = estimate_capacity_from_containers_v1(art.contenitori_magazzino, art.peso_grammi, cap_params)
            capacity_effective = resolve_capacity_effective(capacity_calculated, capacity_override)
            target = compute_target_stock_qty(capacity_effective, effective_stock_months, monthly_base)
            trigger = compute_trigger_stock_qty(effective_stock_trigger, monthly_base)

            preview_metrics.append(StockMetricsItem(
                article_code=canonical,
                monthly_stock_base_qty=monthly_base,
                capacity_calculated_qty=capacity_calculated,
                capacity_override_qty=capacity_override,
                capacity_effective_qty=capacity_effective,
                target_stock_qty=target,
                trigger_stock_qty=trigger,
                strategy_key=new_strategy_key,
                params_snapshot=new_params,
                algorithm_key=CAPACITY_LOGIC_KEY,
                computed_at=computed_at,
            ))

        new_summary = _summarize_metrics(preview_metrics)

        print(f"\n{SEP}")
        print("  CONFRONTO ATTUALE vs NUOVI PARAMETRI")
        print(SEP)
        _print_summary("Attuale", current_summary)
        _print_summary("Con nuovi parametri", new_summary)

        gained = new_summary["with_base"] - current_summary["with_base"]
        print(f"\n  Articoli che acquistano monthly_base: {gained:+d}")

        print(f"\n  Top {args.show_top} con nuovi parametri:")
        _print_top(preview_metrics, args.show_top)

        # ─── Conferma e scrittura DB ──────────────────────────────────────────
        print(f"\n{SEP}")
        print("  CONFERMA SCRITTURA NEL DB")
        print(SEP)
        print(f"  Strategy : {new_strategy_key}")
        print(f"  Params   : {new_params}")
        print()
        answer = input("  Confermi la scrittura nel DB? [s/N] ").strip().lower()
        if answer not in ("s", "si", "sì", "y", "yes"):
            print("  Annullato — nessuna modifica al DB.")
            return

        set_stock_logic_config(
            session,
            monthly_base_strategy_key=new_strategy_key,
            monthly_base_params=new_params,
            capacity_logic_params=cap_params,
        )
        print(f"\n  Configurazione aggiornata nel DB.")
        print(f"  Da questo momento list_stock_metrics_v1() usera '{new_strategy_key}'")
        print(f"  con parametri: {new_params}")
        print(SEP)


if __name__ == "__main__":
    main()
