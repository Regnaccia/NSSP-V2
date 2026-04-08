"""
Core slice `produzioni` (DL-ARCH-V2-015).

Aggrega i mirror `sync_produzioni_attive` e `sync_produzioni_storiche`.
Espone bucket, stato_produzione e override interno forza_completata.

API pubblica:
    - ProduzioneItem
    - list_produzioni
    - set_forza_completata
"""

from nssp_v2.core.produzioni.read_models import ProduzioneItem
from nssp_v2.core.produzioni.queries import list_produzioni, set_forza_completata

__all__ = [
    "ProduzioneItem",
    "list_produzioni",
    "set_forza_completata",
]
