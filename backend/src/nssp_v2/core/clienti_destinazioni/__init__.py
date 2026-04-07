"""
Core slice `clienti + destinazioni` (DL-ARCH-V2-010).

Questo package espone il read model applicativo per la surface logistica.
Legge da `sync_clienti` e `sync_destinazioni`; persiste `nickname_destinazione`
nella tabella Core `core_destinazione_config`.

API pubblica:
    - ClienteItem
    - DestinazioneItem
    - DestinazioneDetail
    - list_clienti
    - list_destinazioni_per_cliente
    - get_destinazione_detail
    - set_nickname_destinazione
    - CoreDestinazioneConfig
"""

from nssp_v2.core.clienti_destinazioni.models import CoreDestinazioneConfig
from nssp_v2.core.clienti_destinazioni.read_models import (
    ClienteItem,
    DestinazioneDetail,
    DestinazioneItem,
)
from nssp_v2.core.clienti_destinazioni.queries import (
    get_destinazione_detail,
    list_clienti,
    list_destinazioni_per_cliente,
    set_nickname_destinazione,
)

__all__ = [
    "ClienteItem",
    "DestinazioneItem",
    "DestinazioneDetail",
    "CoreDestinazioneConfig",
    "list_clienti",
    "list_destinazioni_per_cliente",
    "get_destinazione_detail",
    "set_nickname_destinazione",
]
