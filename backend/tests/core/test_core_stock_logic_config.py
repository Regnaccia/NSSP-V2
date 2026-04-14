"""
Test della configurazione logiche stock V1 (TASK-V2-086, DL-ARCH-V2-030).

Copertura:
- get_stock_logic_config: default se tabella vuota, config DB se presente
- set_stock_logic_config: crea, aggiorna, valida strategy_key
- registry KNOWN_MONTHLY_BASE_STRATEGIES
- CAPACITY_LOGIC_KEY e immutabile (non modificabile tramite set)
- StockLogicConfig read model: is_default, updated_at, campi
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.stock_policy import (
    KNOWN_MONTHLY_BASE_STRATEGIES,
    CAPACITY_LOGIC_KEY,
    StockLogicConfig,
    get_stock_logic_config,
    set_stock_logic_config,
)
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig

# Registra il modello nella metadata
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401
from nssp_v2.core.warnings.config_model import WarningTypeConfig  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


# ─── Registry ─────────────────────────────────────────────────────────────────

def test_known_strategies_non_vuoto():
    assert "monthly_stock_base_from_sales_v1" in KNOWN_MONTHLY_BASE_STRATEGIES


def test_capacity_logic_key_fisso():
    assert CAPACITY_LOGIC_KEY == "capacity_from_containers_v1"


# ─── get_stock_logic_config: default ─────────────────────────────────────────

def test_default_se_tabella_vuota(session):
    config = get_stock_logic_config(session)
    assert config.is_default is True
    assert config.updated_at is None
    assert config.monthly_base_strategy_key == "monthly_stock_base_from_sales_v1"
    assert isinstance(config.monthly_base_params, dict)
    assert config.capacity_logic_key == CAPACITY_LOGIC_KEY
    assert isinstance(config.capacity_logic_params, dict)


def test_default_restituisce_stock_logic_config(session):
    config = get_stock_logic_config(session)
    assert isinstance(config, StockLogicConfig)


# ─── set_stock_logic_config ───────────────────────────────────────────────────

def test_crea_config(session):
    result = set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={"lookback_months": 6},
        capacity_logic_params={"units_per_container": 10},
    )
    assert result.is_default is False
    assert result.monthly_base_strategy_key == "monthly_stock_base_from_sales_v1"
    assert result.monthly_base_params == {"lookback_months": 6}
    assert result.capacity_logic_key == CAPACITY_LOGIC_KEY
    assert result.capacity_logic_params == {"units_per_container": 10}
    assert result.updated_at is not None


def test_crea_config_persistita(session):
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={"lookback_months": 6},
        capacity_logic_params={},
    )
    row = session.query(CoreStockLogicConfig).first()
    assert row is not None
    assert row.monthly_base_strategy_key == "monthly_stock_base_from_sales_v1"
    assert row.monthly_base_params_json == {"lookback_months": 6}
    assert row.capacity_logic_key == CAPACITY_LOGIC_KEY


def test_aggiorna_config_esistente(session):
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={"lookback_months": 6},
        capacity_logic_params={},
    )
    result = set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={"lookback_months": 12},
        capacity_logic_params={"units_per_container": 5},
    )
    assert result.monthly_base_params == {"lookback_months": 12}
    assert result.capacity_logic_params == {"units_per_container": 5}

    # Solo un record in tabella (singleton)
    count = session.query(CoreStockLogicConfig).count()
    assert count == 1


def test_strategy_sconosciuta_lancia_value_error(session):
    with pytest.raises(ValueError, match="Strategy non ammessa"):
        set_stock_logic_config(
            session,
            monthly_base_strategy_key="STRATEGIA_INESISTENTE",
            monthly_base_params={},
            capacity_logic_params={},
        )


def test_capacity_logic_key_immutabile(session):
    """Il capacity_logic_key e sempre CAPACITY_LOGIC_KEY indipendentemente dall'input."""
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={},
        capacity_logic_params={"p": 1},
    )
    config = get_stock_logic_config(session)
    assert config.capacity_logic_key == CAPACITY_LOGIC_KEY


# ─── get_stock_logic_config: usa DB ──────────────────────────────────────────

def test_get_usa_config_da_db(session):
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={"lookback_months": 3},
        capacity_logic_params={"units_per_container": 20},
    )
    config = get_stock_logic_config(session)
    assert config.is_default is False
    assert config.monthly_base_params == {"lookback_months": 3}
    assert config.capacity_logic_params == {"units_per_container": 20}
    assert config.updated_at is not None


def test_params_vuoti_ammessi(session):
    """Params vuoti sono validi — struttura definita dalla strategy in TASK-V2-084."""
    result = set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={},
        capacity_logic_params={},
    )
    assert result.monthly_base_params == {}
    assert result.capacity_logic_params == {}
