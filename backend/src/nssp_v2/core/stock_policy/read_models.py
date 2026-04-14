"""
Read model Core slice `stock_policy` metrics V1 (TASK-V2-084, DL-ARCH-V2-030).

Regole:
- il read model e frozen (immutabile)
- le metriche sono calcolate su richiesta (non persistite)
- computed_at riflette il momento del calcolo
- i campi nullable segnalano assenza di configurazione o dati insufficienti

Shape (STOCK_POLICY_V1_REDUCED_SPEC §10):
  article_code         — codice articolo canonico
  monthly_stock_base_qty  — quantita mensile media di consumo (da strategy)
  capacity_calculated_qty — capacity stimata dalla logica fissa
  capacity_effective_qty  — capacity effettiva (override > calculated)
  target_stock_qty     — scorta target (formula DL-ARCH-V2-030 §5)
  trigger_stock_qty    — soglia di trigger (formula DL-ARCH-V2-030 §5)
  strategy_key         — strategy usata per monthly_stock_base_qty
  params_snapshot      — snapshot dei parametri usati al momento del calcolo
  algorithm_key        — chiave logica capacity usata
  computed_at          — timestamp del calcolo

Campi nullable:
  Tutte le metriche possono essere None se la configurazione stock non e
  disponibile o i dati necessari sono insufficienti.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StockMetricsItem(BaseModel):
    """Metriche stock policy V1 per un articolo — computed read model.

    None su una metrica indica che la configurazione stock non e completa
    o che i dati sorgente non sono disponibili per quell'articolo.
    """

    model_config = ConfigDict(frozen=True)

    # Identificatore articolo (canonico — uppercase, stripped)
    article_code: str

    # Metriche calcolate
    monthly_stock_base_qty: Decimal | None
    capacity_calculated_qty: Decimal | None
    capacity_override_qty: Decimal | None
    capacity_effective_qty: Decimal | None
    target_stock_qty: Decimal | None
    trigger_stock_qty: Decimal | None

    # Metadati del calcolo
    strategy_key: str
    params_snapshot: dict
    algorithm_key: str
    computed_at: datetime
