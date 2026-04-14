"""
Modello ORM per la configurazione delle logiche stock V1 (TASK-V2-086, DL-ARCH-V2-030).

Tabella `core_stock_logic_config`:
- singleton: al massimo un record con id=1
- monthly_base_strategy_key: strategy selezionata per monthly_stock_base_qty
- monthly_base_params_json: parametri JSON della strategy (struttura dipende dalla strategy)
- capacity_logic_key: logica capacity — fisso a 'capacity_from_containers_v1'
- capacity_logic_params_json: parametri JSON della logica capacity
- updated_at: timestamp aggiornamento

Se la tabella e vuota, il Core usa i valori di default definiti in config.py.

Regola architetturale (DL-ARCH-V2-030 §4):
- monthly_stock_base_qty usa una strategy switchable (registry chiuso nel codice)
- capacity_from_containers_v1 e logica fissa di setup (non switchabile)
- i parametri numerici non devono essere hardcoded nel codice applicativo
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from nssp_v2.shared.db import Base


class CoreStockLogicConfig(Base):
    """Configurazione singleton delle logiche stock V1.

    Singleton: il sistema mantiene al massimo un record (id=1).
    Se la tabella e vuota, il Core usa i default di config.py.
    """

    __tablename__ = "core_stock_logic_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Strategy monthly_stock_base_qty (switchable via registry)
    monthly_base_strategy_key: Mapped[str] = mapped_column(String(64), nullable=False)
    monthly_base_params_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Logica capacity (fissa: capacity_from_containers_v1)
    capacity_logic_key: Mapped[str] = mapped_column(String(64), nullable=False)
    capacity_logic_params_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
