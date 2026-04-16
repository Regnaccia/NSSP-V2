"""
Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-069, TASK-V2-071, TASK-V2-074,
DL-ARCH-V2-025, DL-ARCH-V2-027, DL-ARCH-V2-028).

Esporta:
- PlanningContext: contesto by_article (V1)
- PlanningContextOrderLine: contesto by_customer_order_line (V2)
- PlanningCandidateItem: read model con branching by_article / by_customer_order_line
- PlanningMode: vocabolario esplicito (by_article | by_customer_order_line)
- resolve_planning_mode: mappatura central effective_aggrega -> planning_mode
- effective_stock: clamp giacenza fisica a max(on_hand, 0) (DL-ARCH-V2-028)
- Logica V1: future_availability_v1, is_planning_candidate_v1, required_qty_minimum_v1
- Logica V2: line_future_coverage_v2, is_planning_candidate_by_order_line, required_qty_minimum_by_order_line
- list_planning_candidates_v1: query Core con branching
"""

from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    PlanningContextOrderLine,
    capacity_headroom_now_qty_v1,
    effective_stock,
    future_availability_v1,
    is_planning_candidate_v1,
    is_planning_candidate_by_order_line,
    line_future_coverage_v2,
    release_qty_now_max_v1,
    release_status_v1,
    required_qty_minimum_v1,
    required_qty_minimum_by_order_line,
    resolve_primary_driver_v1,
    required_qty_minimum_by_primary_driver_v1,
)
from nssp_v2.core.planning_mode import PlanningMode, resolve_planning_mode
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem
from nssp_v2.core.planning_candidates.queries import list_planning_candidates_v1

__all__ = [
    "PlanningContext",
    "PlanningContextOrderLine",
    "capacity_headroom_now_qty_v1",
    "effective_stock",
    "future_availability_v1",
    "is_planning_candidate_v1",
    "is_planning_candidate_by_order_line",
    "line_future_coverage_v2",
    "release_qty_now_max_v1",
    "release_status_v1",
    "required_qty_minimum_v1",
    "required_qty_minimum_by_order_line",
    "resolve_primary_driver_v1",
    "required_qty_minimum_by_primary_driver_v1",
    "PlanningMode",
    "resolve_planning_mode",
    "PlanningCandidateItem",
    "list_planning_candidates_v1",
]
