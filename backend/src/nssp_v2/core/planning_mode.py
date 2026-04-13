"""
Vocabolario esplicito `planning_mode` (DL-ARCH-V2-027, TASK-V2-069).

`planning_mode` e il termine di dominio derivato da `effective_aggrega_codice_in_produzione`:
- by_article            : aggregazione per codice articolo (true)
- by_customer_order_line: per riga ordine cliente         (false)
- None                  : policy non definita (articolo senza famiglia e senza override)

Il mapping e centrale e univoco: questa e l'unica sorgente autorevole della conversione.
`effective_aggrega_codice_in_produzione` resta il driver dati di policy — `planning_mode`
e il vocabolario esplicito derivato, non una configurazione indipendente.

Uso previsto:
- read model Core che preparano il branching V2 (PlanningCandidateItem, ArticoloDetail)
- logica query future che biforca su by_article vs by_customer_order_line
"""

from typing import Literal

PlanningMode = Literal["by_article", "by_customer_order_line"]


def resolve_planning_mode(effective_aggrega: bool | None) -> PlanningMode | None:
    """Converte effective_aggrega_codice_in_produzione nel vocabolario planning_mode.

    True  -> "by_article"             (aggregazione per codice articolo)
    False -> "by_customer_order_line" (per riga ordine cliente)
    None  -> None                     (policy non definita)
    """
    if effective_aggrega is True:
        return "by_article"
    if effective_aggrega is False:
        return "by_customer_order_line"
    return None
