"""
Test integrazione list_stock_metrics_v1 (TASK-V2-084, TASK-V2-087, TASK-V2-088, DL-ARCH-V2-030).

Copertura:
- lista vuota se non ci sono articoli attivi
- articolo senza movimenti -> monthly_stock_base_qty = None (min_nonzero_months=1)
- articolo con movimenti recenti -> monthly_stock_base_qty calcolata
- movimenti fuori finestra non conteggiati
- articolo con config stock -> target e trigger calcolati
- articolo senza config stock -> target e trigger None
- capacity_override sovrascrive capacity_calculated
- capacity_calculated da contenitori_magazzino
- piu articoli: metriche indipendenti per articolo
- strategy_key e params_snapshot nel risultato
- filtro planning_mode = by_article (TASK-V2-088)
- driver movimenti: quantita_scaricata > 0 (TASK-V2-088)
- min_movements: None se soglia globale non raggiunta (TASK-V2-088)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.stock_policy.queries import list_stock_metrics_v1
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.mag_reale.models import SyncMagReale

# Modelli necessari per registrare Base.metadata in SQLite
from nssp_v2.core.availability.models import CoreAvailability  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.core.warnings.config_model import WarningTypeConfig  # noqa: F401
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

_NOW_UTC = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)

# Data recente: 1 mese fa (dentro qualsiasi finestra)
_RECENT = datetime(2026, 3, 15)
# Data vecchia: 14 mesi fa (fuori dalla finestra 12)
_OLD = datetime(2025, 2, 1)

# Params di test: finestra singola [3] con min_nonzero_months=1, no filtro outlier
_TEST_PARAMS = {
    "windows_months": [3],
    "percentile": 50,
    "zscore_threshold": 0.0,
    "min_nonzero_months": 1,
    "min_movements": 0,
}

_id_seq = 0


def _next_id():
    global _id_seq
    _id_seq += 1
    return _id_seq


@pytest.fixture(autouse=True)
def reset_id_seq():
    global _id_seq
    _id_seq = 0


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_CAPACITY_PARAMS = {"max_container_weight_kg": 25}


def _config_stock_logic(session, params=None, capacity_params=None):
    from nssp_v2.core.stock_policy.config import set_stock_logic_config
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params=params or _TEST_PARAMS,
        capacity_logic_params=capacity_params if capacity_params is not None else _CAPACITY_PARAMS,
    )
    session.flush()


def _art(session, codice="ART001", attivo=True, contenitori=None, peso_grammi=None):
    session.add(SyncArticolo(
        codice_articolo=codice,
        attivo=attivo,
        contenitori_magazzino=contenitori,
        peso_grammi=peso_grammi,
        synced_at=_NOW_UTC,
    ))
    session.flush()


def _movimento(session, codice="ART001", scaricata=10.0, data=None):
    session.add(SyncMagReale(
        id_movimento=_next_id(),
        codice_articolo=codice,
        quantita_scaricata=scaricata,
        data_movimento=data or _RECENT,
        synced_at=_NOW_UTC,
    ))
    session.flush()


def _famiglia(
    session,
    code="FAM1",
    stock_months=None,
    stock_trigger_months=None,
    aggrega_codice_in_produzione=True,
    gestione_scorte_attiva=True,
):
    session.add(ArticoloFamiglia(
        code=code,
        label=f"Famiglia {code}",
        is_active=True,
        considera_in_produzione=False,
        aggrega_codice_in_produzione=aggrega_codice_in_produzione,
        stock_months=stock_months,
        stock_trigger_months=stock_trigger_months,
        gestione_scorte_attiva=gestione_scorte_attiva,
    ))
    session.flush()


def _config(
    session,
    codice="ART001",
    famiglia_code=None,
    override_stock_months=None,
    override_stock_trigger_months=None,
    capacity_override_qty=None,
    override_aggrega_codice_in_produzione=None,
    override_gestione_scorte_attiva=None,
):
    session.add(CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        updated_at=_NOW_UTC,
        override_stock_months=override_stock_months,
        override_stock_trigger_months=override_stock_trigger_months,
        capacity_override_qty=capacity_override_qty,
        override_aggrega_codice_in_produzione=override_aggrega_codice_in_produzione,
        override_gestione_scorte_attiva=override_gestione_scorte_attiva,
    ))
    session.flush()


# ─── Test: lista vuota ────────────────────────────────────────────────────────

def test_lista_vuota_senza_articoli(session):
    session.commit()
    result = list_stock_metrics_v1(session)
    assert result == []


def test_articolo_inattivo_escluso(session):
    _art(session, attivo=False)
    session.commit()
    result = list_stock_metrics_v1(session)
    assert result == []


# ─── Test: filtro planning_mode = by_article (TASK-V2-088) ───────────────────

def test_articolo_senza_planning_mode_escluso(session):
    """Articolo senza famiglia e senza override_aggrega -> effective_aggrega=None -> escluso."""
    _art(session)
    session.commit()
    result = list_stock_metrics_v1(session)
    assert result == []


def test_articolo_by_customer_order_line_escluso(session):
    """Articolo con aggrega=False -> by_customer_order_line -> escluso."""
    _famiglia(session, aggrega_codice_in_produzione=False)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()
    result = list_stock_metrics_v1(session)
    assert result == []


def test_articolo_override_by_customer_order_line_escluso(session):
    """Override articolo by_customer_order_line sovrascrive famiglia by_article."""
    _famiglia(session, aggrega_codice_in_produzione=True)
    _art(session)
    _config(session, famiglia_code="FAM1", override_aggrega_codice_in_produzione=False)
    session.commit()
    result = list_stock_metrics_v1(session)
    assert result == []


def test_articolo_by_article_incluso(session):
    """Articolo con aggrega=True -> by_article -> incluso."""
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()
    result = list_stock_metrics_v1(session)
    assert len(result) == 1
    assert result[0].article_code == "ART001"


def test_articolo_override_by_article_sovrascrive_famiglia(session):
    """Override articolo by_article sovrascrive famiglia by_customer_order_line."""
    _famiglia(session, aggrega_codice_in_produzione=False)
    _art(session)
    _config(session, famiglia_code="FAM1", override_aggrega_codice_in_produzione=True)
    session.commit()
    result = list_stock_metrics_v1(session)
    assert len(result) == 1


def test_articolo_senza_famiglia_con_override_by_article(session):
    """Articolo senza famiglia ma con override_aggrega=True e gestione_scorte_attiva=True -> incluso."""
    _art(session)
    _config(session, override_aggrega_codice_in_produzione=True, override_gestione_scorte_attiva=True)
    session.commit()
    result = list_stock_metrics_v1(session)
    assert len(result) == 1


# ─── Test: monthly_stock_base_qty ─────────────────────────────────────────────

def test_articolo_senza_movimenti_base_none(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 1
    assert result[0].article_code == "ART001"
    assert result[0].monthly_stock_base_qty is None


def test_articolo_con_movimenti_recenti(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=30.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=30.0, data=datetime(2026, 3, 1))
    _movimento(session, scaricata=30.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 1
    # finestra [3], tutti i mesi uguali -> mediana = 30
    assert result[0].monthly_stock_base_qty == Decimal("30")


def test_movimenti_fuori_finestra_non_conteggiati(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=9999.0, data=_OLD)  # fuori finestra 3 mesi
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].monthly_stock_base_qty is None


# ─── Test: driver movimenti quantita_scaricata > 0 (TASK-V2-088) ─────────────

def test_movimenti_con_scaricata_zero_non_conteggiati(session):
    """Righe con quantita_scaricata = 0 non rientrano nel calcolo (driver V1)."""
    _config_stock_logic(session)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=0.0, data=datetime(2026, 4, 1))  # driver: > 0, ignorato
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].monthly_stock_base_qty is None


def test_movimenti_con_scaricata_negativa_non_conteggiati(session):
    """Righe con quantita_scaricata <= 0 escluse: resi/rettifiche non inquinano la base."""
    _config_stock_logic(session)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=-50.0, data=datetime(2026, 4, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].monthly_stock_base_qty is None


# ─── Test: min_movements (TASK-V2-088) ───────────────────────────────────────

def test_min_movements_soglia_non_raggiunta(session):
    """Con min_movements=5 e solo 2 righe movimento -> monthly_stock_base_qty = None."""
    params = dict(_TEST_PARAMS, min_movements=5)
    _config_stock_logic(session, params=params)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=30.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=30.0, data=datetime(2026, 3, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].monthly_stock_base_qty is None


def test_min_movements_soglia_raggiunta(session):
    """Con min_movements=2 e 2 righe movimento -> calcolo procede."""
    params = dict(_TEST_PARAMS, min_movements=2)
    _config_stock_logic(session, params=params)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=30.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=30.0, data=datetime(2026, 3, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].monthly_stock_base_qty is not None


# ─── Test: capacity_calculated_qty (TASK-V2-092 — formula legacy) ────────────

def test_capacity_calcolata_da_contenitori(session):
    # containers=2, peso=500g (0.5kg), max=25kg → 25*2/0.5 = 100
    _config_stock_logic(session)
    _famiglia(session)
    _art(session, contenitori="2", peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty == Decimal("100")


def test_capacity_calcolata_none_senza_contenitori(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session, contenitori=None, peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty is None


def test_capacity_calcolata_none_se_contenitori_non_numerici(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session, contenitori="n/a", peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty is None


def test_capacity_calcolata_none_senza_peso(session):
    _config_stock_logic(session)
    _famiglia(session)
    _art(session, contenitori="2", peso_grammi=None)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty is None


def test_capacity_calcolata_none_senza_max_kg_in_params(session):
    _config_stock_logic(session, capacity_params={})  # max_container_weight_kg non configurato
    _famiglia(session)
    _art(session, contenitori="2", peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty is None


def test_capacity_calcolata_frazionaria(session):
    # containers=1/4=0.25, peso=250g (0.25kg), max=25kg → 25*0.25/0.25 = 25
    _config_stock_logic(session)
    _famiglia(session)
    _art(session, contenitori="1/4", peso_grammi=Decimal("250"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_calculated_qty == Decimal("25")


# ─── Test: capacity_effective_qty ────────────────────────────────────────────

def test_capacity_override_sovrascrive_calculated(session):
    _config_stock_logic(session)
    _famiglia(session)
    # containers=2, peso=500g, max=25 → calculated=100
    _art(session, contenitori="2", peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1", capacity_override_qty=Decimal("500"))
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    assert item.capacity_calculated_qty == Decimal("100")
    assert item.capacity_effective_qty == Decimal("500")


def test_capacity_effective_uguale_a_calculated_senza_override(session):
    _config_stock_logic(session)
    _famiglia(session)
    # containers=4, peso=1000g (1kg), max=25 → 25*4/1 = 100
    _art(session, contenitori="4", peso_grammi=Decimal("1000"))
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_effective_qty == Decimal("100")


def test_capacity_effective_none_senza_dati(session):
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].capacity_effective_qty is None


# ─── Test: target_stock_qty e trigger_stock_qty ───────────────────────────────

def test_target_e_trigger_none_senza_config_stock(session):
    """Articolo by_article senza stock_months nella famiglia -> target/trigger None."""
    _config_stock_logic(session)
    _famiglia(session, stock_months=None, stock_trigger_months=None)
    _art(session, contenitori="100")
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=30.0)
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    assert item.target_stock_qty is None
    assert item.trigger_stock_qty is None


def test_target_e_trigger_con_famiglia(session):
    _config_stock_logic(session)
    _famiglia(session, stock_months=Decimal("3"), stock_trigger_months=Decimal("1"))
    # capacity: nessun peso_grammi → capacity_calculated = None, no clamp
    _art(session, contenitori="200")
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=10.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 3, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    # monthly_base = 10, capacity_effective = None → target = 3*10 = 30
    assert item.target_stock_qty == Decimal("30")
    # trigger = 1*10 = 10
    assert item.trigger_stock_qty == Decimal("10")


def test_target_limitato_da_capacity(session):
    _config_stock_logic(session)
    _famiglia(session, stock_months=Decimal("12"), stock_trigger_months=Decimal("1"))
    # capacity: 25kg * 1 contenitore / (500g / 1000) = 50
    _art(session, contenitori="1", peso_grammi=Decimal("500"))
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=20.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=20.0, data=datetime(2026, 3, 1))
    _movimento(session, scaricata=20.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    # capacity = 50, months_target = 12*20 = 240 → target = min(50, 240) = 50
    assert item.capacity_calculated_qty == Decimal("50")
    assert item.target_stock_qty == Decimal("50")


def test_target_senza_capacity_usa_solo_formula(session):
    _config_stock_logic(session)
    _famiglia(session, stock_months=Decimal("3"), stock_trigger_months=Decimal("1"))
    _art(session)  # nessun contenitore
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=10.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 3, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    # target = 3 * 10 = 30 (nessun min con capacity)
    assert item.target_stock_qty == Decimal("30")


def test_override_articolo_sovrascrive_famiglia(session):
    _config_stock_logic(session)
    _famiglia(session, stock_months=Decimal("6"), stock_trigger_months=Decimal("2"))
    _art(session, contenitori="500")
    _config(
        session,
        famiglia_code="FAM1",
        override_stock_months=Decimal("1"),
        override_stock_trigger_months=Decimal("0.5"),
    )
    _movimento(session, scaricata=10.0, data=datetime(2026, 4, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 3, 1))
    _movimento(session, scaricata=10.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    item = result[0]
    # target = min(500, 1*10) = 10
    assert item.target_stock_qty == Decimal("10")
    # trigger = 0.5 * 10 = 5
    assert item.trigger_stock_qty == Decimal("5")


# ─── Test: piu articoli ───────────────────────────────────────────────────────

def test_piu_articoli_metriche_indipendenti(session):
    _config_stock_logic(session)
    _famiglia(session, stock_months=Decimal("3"), stock_trigger_months=Decimal("1"))
    _art(session, codice="ART001")
    _art(session, codice="ART002")
    _config(session, codice="ART001", famiglia_code="FAM1")
    _config(session, codice="ART002", famiglia_code="FAM1")
    _movimento(session, codice="ART001", scaricata=10.0, data=datetime(2026, 4, 1))
    _movimento(session, codice="ART001", scaricata=10.0, data=datetime(2026, 3, 1))
    _movimento(session, codice="ART001", scaricata=10.0, data=datetime(2026, 2, 1))
    _movimento(session, codice="ART002", scaricata=20.0, data=datetime(2026, 4, 1))
    _movimento(session, codice="ART002", scaricata=20.0, data=datetime(2026, 3, 1))
    _movimento(session, codice="ART002", scaricata=20.0, data=datetime(2026, 2, 1))
    session.commit()

    result = list_stock_metrics_v1(session)
    by_code = {item.article_code: item for item in result}

    assert "ART001" in by_code
    assert "ART002" in by_code

    assert by_code["ART001"].monthly_stock_base_qty == Decimal("10")
    assert by_code["ART001"].trigger_stock_qty == Decimal("10")

    assert by_code["ART002"].monthly_stock_base_qty == Decimal("20")
    assert by_code["ART002"].trigger_stock_qty == Decimal("20")


def test_articolo_by_customer_escluso_da_lista_mista(session):
    """In una lista mista, solo articoli by_article sono nel risultato."""
    _config_stock_logic(session)
    _famiglia(session, code="FAM_BY_ART", aggrega_codice_in_produzione=True)
    _famiglia(session, code="FAM_BY_CUST", aggrega_codice_in_produzione=False)
    _art(session, codice="ART001")
    _art(session, codice="ART002")
    _config(session, codice="ART001", famiglia_code="FAM_BY_ART")
    _config(session, codice="ART002", famiglia_code="FAM_BY_CUST")
    session.commit()

    result = list_stock_metrics_v1(session)
    codes = [item.article_code for item in result]
    assert "ART001" in codes
    assert "ART002" not in codes


# ─── Test: metadati nel risultato ────────────────────────────────────────────

def test_strategy_key_nel_risultato(session):
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].strategy_key == "monthly_stock_base_from_sales_v1"


def test_algorithm_key_nel_risultato(session):
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].algorithm_key == "capacity_from_containers_v1"


def test_computed_at_presente(session):
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].computed_at is not None


def test_params_snapshot_nel_risultato(session):
    _config_stock_logic(session, params=_TEST_PARAMS)
    _famiglia(session)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert result[0].params_snapshot == _TEST_PARAMS


# ─── Test: filtro gestione_scorte_attiva (TASK-V2-099) ───────────────────────

def test_gestione_scorte_false_esclude_articolo(session):
    """Articolo by_article con gestione_scorte_attiva=False e escluso dal perimetro stock policy."""
    _config_stock_logic(session)
    _famiglia(session, gestione_scorte_attiva=False)
    _art(session)
    _config(session, famiglia_code="FAM1")
    _movimento(session, scaricata=10.0)
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 0


def test_gestione_scorte_none_famiglia_esclude_articolo(session):
    """Articolo by_article con gestione_scorte_attiva=None su famiglia (default False) e escluso."""
    _config_stock_logic(session)
    _famiglia(session, gestione_scorte_attiva=False)
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 0


def test_override_gestione_scorte_true_sovrascrive_false_famiglia(session):
    """Override articolo gestione_scorte_attiva=True sovrascrive il False della famiglia."""
    _config_stock_logic(session)
    _famiglia(session, gestione_scorte_attiva=False)
    _art(session)
    _config(session, famiglia_code="FAM1", override_gestione_scorte_attiva=True)
    _movimento(session, scaricata=10.0)
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 1
    assert result[0].article_code == "ART001"


def test_override_gestione_scorte_false_sovrascrive_true_famiglia(session):
    """Override articolo gestione_scorte_attiva=False esclude anche se la famiglia ha True."""
    _config_stock_logic(session)
    _famiglia(session, gestione_scorte_attiva=True)
    _art(session)
    _config(session, famiglia_code="FAM1", override_gestione_scorte_attiva=False)
    _movimento(session, scaricata=10.0)
    session.commit()

    result = list_stock_metrics_v1(session)
    assert len(result) == 0


def test_lista_mista_gestione_scorte(session):
    """In lista mista, solo articoli con gestione_scorte_attiva=True compaiono."""
    _config_stock_logic(session)
    _famiglia(session, code="FAM_ON", gestione_scorte_attiva=True)
    _famiglia(session, code="FAM_OFF", gestione_scorte_attiva=False)
    _art(session, codice="ART001")
    _art(session, codice="ART002")
    _config(session, codice="ART001", famiglia_code="FAM_ON")
    _config(session, codice="ART002", famiglia_code="FAM_OFF")
    _movimento(session, codice="ART001", scaricata=10.0)
    _movimento(session, codice="ART002", scaricata=10.0)
    session.commit()

    result = list_stock_metrics_v1(session)
    codes = [item.article_code for item in result]
    assert "ART001" in codes
    assert "ART002" not in codes
