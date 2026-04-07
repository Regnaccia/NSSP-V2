"""
Core slice `articoli` (DL-ARCH-V2-013, DL-ARCH-V2-014).

Questo package espone il read model applicativo per la surface produzione.
Legge da `sync_articoli`; dati interni (famiglia) in `core_articolo_config`.

API pubblica:
    - ArticoloItem
    - ArticoloDetail
    - FamigliaItem
    - list_articoli
    - get_articolo_detail
    - list_famiglie
    - set_famiglia_articolo
"""

from nssp_v2.core.articoli.read_models import ArticoloDetail, ArticoloItem, FamigliaItem
from nssp_v2.core.articoli.queries import (
    get_articolo_detail,
    list_articoli,
    list_famiglie,
    set_famiglia_articolo,
)

__all__ = [
    "ArticoloItem",
    "ArticoloDetail",
    "FamigliaItem",
    "list_articoli",
    "get_articolo_detail",
    "list_famiglie",
    "set_famiglia_articolo",
]
