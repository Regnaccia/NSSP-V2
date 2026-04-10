"""
Core slice `criticita articoli` (TASK-V2-055, DL-ARCH-V2-023).

Espone la logica V1 di criticita e il read model applicativo.

API pubblica:
    - ArticleLogicContext
    - CriticitaItem
    - is_critical_v1
    - list_criticita_v1
"""

from nssp_v2.core.criticita.logic import ArticleLogicContext, is_critical_v1
from nssp_v2.core.criticita.read_models import CriticitaItem
from nssp_v2.core.criticita.queries import list_criticita_v1

__all__ = [
    "ArticleLogicContext",
    "CriticitaItem",
    "is_critical_v1",
    "list_criticita_v1",
]
