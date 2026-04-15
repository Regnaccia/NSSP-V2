"""
Read model Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029, TASK-V2-091).

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

Campi specifici INVALID_STOCK_CAPACITY (TASK-V2-091):
- article_code: codice articolo canonico
- capacity_calculated_qty: capacity calcolata da contenitori (None se dati mancanti)
- capacity_override_qty: override articolo-specifico (None se non impostato)
- capacity_effective_qty: valore effettivo (None o <= 0 = warning attivo)

Campi specifici MISSING_RAW_BAR_LENGTH (TASK-V2-122):
- article_code: codice articolo canonico
- famiglia_code: codice famiglia con raw_bar_length_mm_enabled=True
- raw_bar_length_mm_enabled: True (trigger condition)
- raw_bar_length_mm: valore corrente dell'articolo (None o <= 0 = warning attivo)
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WarningItem(BaseModel):
    """Warning canonico V1 — tipi: NEGATIVE_STOCK, INVALID_STOCK_CAPACITY, MISSING_RAW_BAR_LENGTH.

    warning_id e derivato come '{type}:{entity_key}' — unico per articolo.
    I campi specifici per tipo sono opzionali (None per i tipi che non li usano).
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

    # ─── Campo comune a tutti i tipi articolo ────────────────────────────────
    article_code: str

    # ─── Campi specifici NEGATIVE_STOCK ──────────────────────────────────────
    stock_calculated: Decimal | None = None
    anomaly_qty: Decimal | None = None

    # ─── Campi specifici INVALID_STOCK_CAPACITY (TASK-V2-091) ────────────────
    capacity_calculated_qty: Decimal | None = None
    capacity_override_qty: Decimal | None = None
    capacity_effective_qty: Decimal | None = None

    # ─── Campi specifici MISSING_RAW_BAR_LENGTH (TASK-V2-122) ────────────────
    famiglia_code: str | None = None
    raw_bar_length_mm_enabled: bool | None = None
    raw_bar_length_mm: Decimal | None = None
