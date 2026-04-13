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

from nssp_v2.core.articoli.read_models import ArticoloDetail, ArticoloItem, FamigliaItem, FamigliaRow
from nssp_v2.core.articoli.queries import (
    create_famiglia,
    get_articolo_detail,
    list_articoli,
    list_famiglie,
    list_famiglie_catalog,
    set_articolo_policy_override,
    set_famiglia_articolo,
    toggle_famiglia_active,
    toggle_famiglia_aggrega_codice_produzione,
    toggle_famiglia_considera_produzione,
)

__all__ = [
    "ArticoloItem",
    "ArticoloDetail",
    "FamigliaItem",
    "FamigliaRow",
    "list_articoli",
    "get_articolo_detail",
    "list_famiglie",
    "list_famiglie_catalog",
    "create_famiglia",
    "toggle_famiglia_active",
    "toggle_famiglia_considera_produzione",
    "toggle_famiglia_aggrega_codice_produzione",
    "set_famiglia_articolo",
    "set_articolo_policy_override",
]
