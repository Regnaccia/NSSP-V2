"""
Logiche di dominio su fact canonici — criticita articoli (DL-ARCH-V2-023, TASK-V2-055).

Struttura:
- ArticleLogicContext: contesto stabile (fact canonici) passato alla logica
- is_critical_v1: funzione pura intercambiabile — V1 = availability_qty < 0

Regola DL-ARCH-V2-023:
- i fact canonici restano stabili
- la logica e un livello separato, testabile in isolamento
- la UI consuma esiti, non formula hardcoded
"""

from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleLogicContext:
    """Contesto di fact canonici passato alle logiche di dominio articolo.

    Tutti i campi quantitativi possono essere None se il fact non e ancora stato
    calcolato (primo avvio, refresh non ancora eseguito).
    """

    article_code: str
    inventory_qty: Decimal | None
    customer_set_aside_qty: Decimal | None
    committed_qty: Decimal | None
    availability_qty: Decimal | None


def is_critical_v1(ctx: ArticleLogicContext) -> bool:
    """Logica V1: un articolo e critico se availability_qty < 0.

    Restituisce False se availability_qty non e ancora disponibile (None).

    Questa funzione e intercambiabile (DL-ARCH-V2-023 §Regola 3):
    in futuro potra essere sostituita con una logica piu ricca
    (safety stock, policy per famiglia, ecc.) senza modificare i fact canonici.
    """
    if ctx.availability_qty is None:
        return False
    return ctx.availability_qty < Decimal("0")
