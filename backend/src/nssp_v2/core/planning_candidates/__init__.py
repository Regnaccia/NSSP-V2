"""
Core slice `planning_candidates` V1 (TASK-V2-062, DL-ARCH-V2-025).

Esporta:
- PlanningContext: contesto di fact canonici per la logica V1
- PlanningCandidateItem: read model della projection V1
- is_planning_candidate_v1: logica pura intercambiabile
- future_availability_v1: copertura futura semplice
- required_qty_minimum_v1: scopertura minima
- list_planning_candidates_v1: query Core dei candidate aggregati per articolo
"""

from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    future_availability_v1,
    is_planning_candidate_v1,
    required_qty_minimum_v1,
)
from nssp_v2.core.planning_candidates.read_models import PlanningCandidateItem
from nssp_v2.core.planning_candidates.queries import list_planning_candidates_v1

__all__ = [
    "PlanningContext",
    "future_availability_v1",
    "is_planning_candidate_v1",
    "required_qty_minimum_v1",
    "PlanningCandidateItem",
    "list_planning_candidates_v1",
]
