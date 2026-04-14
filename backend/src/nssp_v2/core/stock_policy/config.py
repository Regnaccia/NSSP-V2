"""
Configurazione logiche stock V1 (TASK-V2-086, DL-ARCH-V2-030).

Struttura:
- KNOWN_MONTHLY_BASE_STRATEGIES: registry chiuso delle strategy ammesse
- CAPACITY_LOGIC_KEY: logica capacity fissa (non switchabile)
- StockLogicConfig: read model frozen della configurazione attiva
- get_stock_logic_config: legge la configurazione da DB con fallback ai default
- set_stock_logic_config: aggiorna (upsert) la configurazione singleton

Regola (DL-ARCH-V2-030 §4):
- monthly_stock_base_qty usa una strategy selezionabile nel registry
- capacity_from_containers_v1 e logica fissa: il suo key non e cambiabile
- i parametri devono essere leggibili dal Core stock metrics (TASK-V2-084)
- nessun parametro hardcoded nel codice applicativo

Default V1:
- strategy: monthly_stock_base_from_sales_v1
- params: {}  (parametri specifici definiti in TASK-V2-084)
- capacity logic key: capacity_from_containers_v1
- capacity params: {}
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig

# ─── Registry e costanti ──────────────────────────────────────────────────────

# Strategy ammesse per monthly_stock_base_qty — registry chiuso nel codice
KNOWN_MONTHLY_BASE_STRATEGIES: list[str] = [
    "monthly_stock_base_from_sales_v1",
]

# Logica capacity fissa — non switchabile (DL-ARCH-V2-030 §2)
CAPACITY_LOGIC_KEY: str = "capacity_from_containers_v1"

# Default di sistema — usati se la tabella e vuota
_DEFAULT_MONTHLY_BASE_STRATEGY: str = "monthly_stock_base_from_sales_v1"
_DEFAULT_MONTHLY_BASE_PARAMS: dict = {}
_DEFAULT_CAPACITY_LOGIC_PARAMS: dict = {}


# ─── Read model ───────────────────────────────────────────────────────────────

class StockLogicConfig(BaseModel):
    """Configurazione attiva delle logiche stock V1.

    is_default=True: nessuna riga in DB — si stanno usando i default di sistema.
    is_default=False: configurazione persistita esplicita.
    updated_at=None quando is_default=True.
    """

    model_config = ConfigDict(frozen=True)

    # Strategy monthly_stock_base_qty
    monthly_base_strategy_key: str
    monthly_base_params: dict

    # Logica capacity (sempre capacity_from_containers_v1)
    capacity_logic_key: str
    capacity_logic_params: dict

    is_default: bool
    updated_at: datetime | None = None


# ─── Query ────────────────────────────────────────────────────────────────────

def get_stock_logic_config(session: Session) -> StockLogicConfig:
    """Restituisce la configurazione attiva delle logiche stock V1.

    Se la tabella e vuota, restituisce i default di sistema (is_default=True).
    Se esiste una riga in DB (id=1), restituisce quella (is_default=False).
    """
    row = session.scalar(select(CoreStockLogicConfig))
    if row is None:
        return StockLogicConfig(
            monthly_base_strategy_key=_DEFAULT_MONTHLY_BASE_STRATEGY,
            monthly_base_params=dict(_DEFAULT_MONTHLY_BASE_PARAMS),
            capacity_logic_key=CAPACITY_LOGIC_KEY,
            capacity_logic_params=dict(_DEFAULT_CAPACITY_LOGIC_PARAMS),
            is_default=True,
            updated_at=None,
        )
    return StockLogicConfig(
        monthly_base_strategy_key=row.monthly_base_strategy_key,
        monthly_base_params=dict(row.monthly_base_params_json),
        capacity_logic_key=row.capacity_logic_key,
        capacity_logic_params=dict(row.capacity_logic_params_json),
        is_default=False,
        updated_at=row.updated_at,
    )


def set_stock_logic_config(
    session: Session,
    monthly_base_strategy_key: str,
    monthly_base_params: dict,
    capacity_logic_params: dict,
) -> StockLogicConfig:
    """Aggiorna (upsert singleton) la configurazione delle logiche stock V1.

    monthly_base_strategy_key deve essere in KNOWN_MONTHLY_BASE_STRATEGIES.
    Lancia ValueError se la strategy non e nel registry.
    capacity_logic_key e sempre CAPACITY_LOGIC_KEY (non modificabile).
    Dopo il commit restituisce il read model aggiornato.
    """
    if monthly_base_strategy_key not in KNOWN_MONTHLY_BASE_STRATEGIES:
        raise ValueError(
            f"Strategy non ammessa: '{monthly_base_strategy_key}'. "
            f"Ammesse: {KNOWN_MONTHLY_BASE_STRATEGIES}"
        )

    now = datetime.now(timezone.utc)
    row = session.scalar(select(CoreStockLogicConfig))

    if row is None:
        row = CoreStockLogicConfig(
            monthly_base_strategy_key=monthly_base_strategy_key,
            monthly_base_params_json=dict(monthly_base_params),
            capacity_logic_key=CAPACITY_LOGIC_KEY,
            capacity_logic_params_json=dict(capacity_logic_params),
            updated_at=now,
        )
        session.add(row)
    else:
        row.monthly_base_strategy_key = monthly_base_strategy_key
        row.monthly_base_params_json = dict(monthly_base_params)
        row.capacity_logic_key = CAPACITY_LOGIC_KEY  # immutabile
        row.capacity_logic_params_json = dict(capacity_logic_params)
        row.updated_at = now

    session.commit()

    return StockLogicConfig(
        monthly_base_strategy_key=monthly_base_strategy_key,
        monthly_base_params=dict(monthly_base_params),
        capacity_logic_key=CAPACITY_LOGIC_KEY,
        capacity_logic_params=dict(capacity_logic_params),
        is_default=False,
        updated_at=now,
    )
