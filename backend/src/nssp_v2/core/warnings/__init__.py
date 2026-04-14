"""
Core slice `warnings` V1 (TASK-V2-076, TASK-V2-077, TASK-V2-081, DL-ARCH-V2-029, TASK-V2-091).

Modulo trasversale canonico per le anomalie operative e di dati.

Esporta:
- is_negative_stock: condizione NEGATIVE_STOCK (inventory_qty < 0)
- is_invalid_stock_capacity: condizione INVALID_STOCK_CAPACITY (capacity_effective_qty None o <= 0)
- WarningItem: read model canonico warning
- list_warnings_v1: query Core — genera NEGATIVE_STOCK e INVALID_STOCK_CAPACITY
- filter_warnings_by_areas: filtra la lista warning per le aree operative dell'utente corrente
- WarningTypeConfigItem: read model configurazione visibilita per tipo warning
- KNOWN_WARNING_TYPES: vocabolario canonico dei tipi warning supportati
- KNOWN_AREAS: aree/reparti operativi validi per la configurazione di visibilita
- list_warning_configs: lista config visibilita per tutti i tipi noti
- set_warning_config: aggiorna o crea config per un tipo warning
- get_visible_to_areas: risolve visible_to_areas da DB con fallback default

Principio (DL-ARCH-V2-029):
- un warning esiste una sola volta
- la configurazione di visibilita e governata dalla surface admin
- altri moduli possono leggere i warning ma non possiedono la logica di generazione
- la surface Warnings e un punto trasversale canonico: non dipende dalla config per area
"""

from nssp_v2.core.warnings.logic import is_invalid_stock_capacity, is_negative_stock
from nssp_v2.core.warnings.read_models import WarningItem
from nssp_v2.core.warnings.queries import list_warnings_v1, filter_warnings_by_areas
from nssp_v2.core.warnings.config import (
    WarningTypeConfigItem,
    KNOWN_WARNING_TYPES,
    KNOWN_AREAS,
    list_warning_configs,
    set_warning_config,
    get_visible_to_areas,
)

__all__ = [
    "is_negative_stock",
    "is_invalid_stock_capacity",
    "WarningItem",
    "list_warnings_v1",
    "filter_warnings_by_areas",
    "WarningTypeConfigItem",
    "KNOWN_WARNING_TYPES",
    "KNOWN_AREAS",
    "list_warning_configs",
    "set_warning_config",
    "get_visible_to_areas",
]
