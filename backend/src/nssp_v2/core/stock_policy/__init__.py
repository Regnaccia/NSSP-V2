"""
Core slice `stock_policy` V1 (TASK-V2-086, TASK-V2-084, DL-ARCH-V2-030).

Modulo per la configurazione e il calcolo delle metriche stock V1.

Esporta (TASK-V2-086 — configurazione logiche):
- KNOWN_MONTHLY_BASE_STRATEGIES: registry chiuso delle strategy ammesse
- CAPACITY_LOGIC_KEY: costante logica capacity fissa
- StockLogicConfig: read model configurazione logiche attive
- get_stock_logic_config: legge configurazione da DB con fallback ai default
- set_stock_logic_config: aggiorna la configurazione singleton

Esporta (TASK-V2-084 — metriche calcolate):
- StockMetricsItem: read model frozen per le metriche stock articolo
- list_stock_metrics_v1: calcola le metriche per tutti gli articoli attivi
- estimate_monthly_stock_base_from_sales_v1: logica base mensile da vendite
- estimate_capacity_from_containers_v1: logica capacity da contenitori
- resolve_capacity_effective: risoluzione capacity con override
- compute_target_stock_qty: formula target DL-ARCH-V2-030 §5
- compute_trigger_stock_qty: formula trigger DL-ARCH-V2-030 §5

Principio (DL-ARCH-V2-030):
- monthly_stock_base_qty usa una strategy switchable (registry nel codice)
- capacity_from_containers_v1 e logica fissa non switchabile
- i parametri numerici sono configurabili e non hardcoded
"""

from nssp_v2.core.stock_policy.config import (
    CAPACITY_LOGIC_KEY,
    KNOWN_MONTHLY_BASE_STRATEGIES,
    StockLogicConfig,
    get_stock_logic_config,
    set_stock_logic_config,
)
from nssp_v2.core.stock_policy.logic import (
    compute_target_stock_qty,
    compute_trigger_stock_qty,
    estimate_capacity_from_containers_v1,
    estimate_monthly_stock_base_from_sales_v1,
    resolve_capacity_effective,
)
from nssp_v2.core.stock_policy.queries import list_stock_metrics_v1
from nssp_v2.core.stock_policy.read_models import StockMetricsItem

__all__ = [
    # config (TASK-V2-086)
    "KNOWN_MONTHLY_BASE_STRATEGIES",
    "CAPACITY_LOGIC_KEY",
    "StockLogicConfig",
    "get_stock_logic_config",
    "set_stock_logic_config",
    # read model (TASK-V2-084)
    "StockMetricsItem",
    # query (TASK-V2-084)
    "list_stock_metrics_v1",
    # pure logic (TASK-V2-084)
    "estimate_monthly_stock_base_from_sales_v1",
    "estimate_capacity_from_containers_v1",
    "resolve_capacity_effective",
    "compute_target_stock_qty",
    "compute_trigger_stock_qty",
]
