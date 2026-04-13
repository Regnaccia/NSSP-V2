"""
Read model Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029).

Regole:
- il warning e l'oggetto canonico del modulo Warnings
- un warning esiste una sola volta e puo essere consumato da piu moduli o surface
- la generazione e persistenza restano centralizzate in questo modulo
- i read model sono frozen (immutabili)

Shape (DL-ARCH-V2-029, WARNINGS_SPEC_V1 §8):
- warning_id: identificativo canonico derivato (tipo:entita)
- type: vocabolario esplicito del tipo warning
- severity: livello di gravita ('warning', 'error', ecc.)
- entity_type: tipo entita colpita ('article')
- entity_key: identificativo entita colpita (codice articolo canonico)
- message: messaggio leggibile
- source_module: modulo proprietario ('warnings')
- visible_to_areas: aree/reparti operativi abilitati alla visualizzazione
- created_at: timestamp del warning (computed_at del fact sorgente)

Campi specifici NEGATIVE_STOCK (WARNINGS_SPEC_V1 §8):
- article_code: codice articolo canonico
- stock_calculated: valore raw inventory_qty (negativo)
- anomaly_qty: abs(stock_calculated) — entita dell'anomalia
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WarningItem(BaseModel):
    """Warning canonico V1 — primo tipo: NEGATIVE_STOCK.

    warning_id e derivato come '{type}:{entity_key}' — unico per articolo.
    visible_to_areas V1: ['magazzino', 'produzione'] — configurabile via admin.
    anomaly_qty = abs(stock_calculated): quanto la giacenza scende sotto zero.
    """

    model_config = ConfigDict(frozen=True)

    # ─── Shape canonica (WARNINGS_SPEC_V1 §8) ────────────────────────────────
    warning_id: str
    type: str
    severity: str
    entity_type: str
    entity_key: str
    message: str
    source_module: str
    visible_to_areas: list[str]
    created_at: datetime

    # ─── Campi specifici NEGATIVE_STOCK ──────────────────────────────────────
    article_code: str
    stock_calculated: Decimal
    anomaly_qty: Decimal
