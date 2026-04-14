"""
Test Planning Candidates stock-driven V1 (TASK-V2-085, DL-ARCH-V2-030).

Copertura:
- is_planning_candidate_with_stock_v1: condizione estesa con trigger
- customer_shortage_qty_v1: formula max(-fav, 0)
- stock_replenishment_qty_v1: formula max(target - max(fav, 0), 0); None se no target
- required_qty_total_v1: somma shortage + replenishment
- Integrazione list_planning_candidates_v1:
  - articolo con fav < 0: candidate con breakdown (shortage + replenishment)
  - articolo con fav >= 0 ma < trigger: candidate "stock_below_trigger"
  - articolo con fav >= 0 e fav >= trigger: non candidate
  - breakdown: nessun doppio conteggio shortage + replenishment
  - ramo by_customer_order_line invariato (no stock policy)
  - articolo by_article senza stock policy: comportamento V1 retrocompatibile
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    customer_shortage_qty_v1,
    is_planning_candidate_with_stock_v1,
    required_qty_total_v1,
    stock_replenishment_qty_v1,
    resolve_primary_driver_v1,
    required_qty_minimum_by_primary_driver_v1,
)
from nssp_v2.core.planning_candidates.queries import list_planning_candidates_v1
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401

# Modelli per registrare Base.metadata
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def _famiglia(session, code="FAM1", stock_months=None, stock_trigger_months=None, aggrega=True, gestione_scorte_attiva=True):
    session.add(ArticoloFamiglia(
        code=code,
        label=f"Famiglia {code}",
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=aggrega,
        stock_months=stock_months,
        stock_trigger_months=stock_trigger_months,
        gestione_scorte_attiva=gestione_scorte_attiva,
    ))
    session.flush()


def _art(session, codice="ART001"):
    session.add(SyncArticolo(
        codice_articolo=codice,
        attivo=True,
        synced_at=_NOW,
    ))
    session.flush()


def _config(session, codice="ART001", famiglia_code="FAM1", **kwargs):
    session.add(CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        updated_at=_NOW,
        **kwargs,
    ))
    session.flush()


def _avail(session, codice="ART001", inventory=100, set_aside=0, committed=0):
    inv = Decimal(str(inventory))
    sa = Decimal(str(set_aside))
    com = Decimal(str(committed))
    session.add(CoreAvailability(
        article_code=codice,
        inventory_qty=inv,
        customer_set_aside_qty=sa,
        committed_qty=com,
        availability_qty=inv - sa - com,
        computed_at=_NOW,
    ))
    session.flush()


# ─── Test: logica pura ────────────────────────────────────────────────────────

class TestIsCandidate:
    def test_fav_negativo_sempre_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("-1"), None) is True

    def test_fav_negativo_con_trigger(self):
        assert is_planning_candidate_with_stock_v1(Decimal("-10"), Decimal("50")) is True

    def test_fav_zero_senza_trigger_non_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("0"), None) is False

    def test_fav_positivo_senza_trigger_non_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("100"), None) is False

    def test_fav_sotto_trigger_e_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("30"), Decimal("50")) is True

    def test_fav_uguale_trigger_non_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("50"), Decimal("50")) is False

    def test_fav_sopra_trigger_non_candidate(self):
        assert is_planning_candidate_with_stock_v1(Decimal("60"), Decimal("50")) is False

    def test_fav_none_non_candidate(self):
        assert is_planning_candidate_with_stock_v1(None, Decimal("50")) is False


class TestCustomerShortage:
    def test_fav_negativo(self):
        assert customer_shortage_qty_v1(Decimal("-50")) == Decimal("50")

    def test_fav_zero(self):
        assert customer_shortage_qty_v1(Decimal("0")) == Decimal("0")

    def test_fav_positivo(self):
        assert customer_shortage_qty_v1(Decimal("100")) == Decimal("0")


class TestStockReplenishment:
    def test_no_target_restituisce_none(self):
        assert stock_replenishment_qty_v1(None, Decimal("10")) is None

    def test_fav_positivo_sotto_target(self):
        # target=100, fav=30 -> replenishment = max(100-30, 0) = 70
        assert stock_replenishment_qty_v1(Decimal("100"), Decimal("30")) == Decimal("70")

    def test_fav_sopra_target(self):
        # target=50, fav=80 -> replenishment = max(50-80, 0) = 0
        assert stock_replenishment_qty_v1(Decimal("50"), Decimal("80")) == Decimal("0")

    def test_fav_negativo_no_doppio_conteggio(self):
        # fav=-20 -> max(fav,0)=0 -> replenishment = max(target - 0, 0) = target
        # Il clamp evita di sommare la componente shortage al replenishment
        assert stock_replenishment_qty_v1(Decimal("100"), Decimal("-20")) == Decimal("100")

    def test_fav_zero(self):
        assert stock_replenishment_qty_v1(Decimal("80"), Decimal("0")) == Decimal("80")


class TestRequiredTotal:
    def test_solo_shortage(self):
        assert required_qty_total_v1(Decimal("50"), None) == Decimal("50")

    def test_shortage_e_replenishment(self):
        assert required_qty_total_v1(Decimal("20"), Decimal("80")) == Decimal("100")

    def test_zero_shortage_solo_replenishment(self):
        assert required_qty_total_v1(Decimal("0"), Decimal("60")) == Decimal("60")

    def test_entrambi_zero(self):
        assert required_qty_total_v1(Decimal("0"), Decimal("0")) == Decimal("0")


class TestPrimaryDriver:
    def test_customer_shortage_precede_stock(self):
        assert resolve_primary_driver_v1(Decimal("10"), Decimal("5")) == "customer"

    def test_stock_quando_solo_scorta(self):
        assert resolve_primary_driver_v1(Decimal("0"), Decimal("7")) == "stock"

    def test_required_minimum_customer(self):
        assert required_qty_minimum_by_primary_driver_v1(
            Decimal("12"),
            Decimal("30"),
            "customer",
        ) == Decimal("12")

    def test_required_minimum_stock(self):
        assert required_qty_minimum_by_primary_driver_v1(
            Decimal("0"),
            Decimal("30"),
            "stock",
        ) == Decimal("30")


# ─── Test: integrazione list_planning_candidates_v1 ──────────────────────────

def _setup_stock_logic(session, windows_months=None, min_movements=0):
    """Configura core_stock_logic_config con parametri di test."""
    from nssp_v2.core.stock_policy.config import set_stock_logic_config
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={
            "windows_months": windows_months or [3],
            "percentile": 50,
            "zscore_threshold": 0.0,
            "min_nonzero_months": 1,
            "min_movements": min_movements,
        },
        capacity_logic_params={},
    )
    session.flush()


def _add_movement(session, codice, scaricata, data):
    """Aggiunge un movimento di scarico per generare monthly_stock_base_qty."""
    from nssp_v2.sync.mag_reale.models import SyncMagReale
    session.add(SyncMagReale(
        id_movimento=abs(hash((codice, scaricata, str(data)))) % 999999,
        codice_articolo=codice,
        quantita_scaricata=float(scaricata),
        data_movimento=data,
        synced_at=_NOW,
    ))
    session.flush()


# ─── Candidatura shortage cliente (fav < 0) ───────────────────────────────────

def test_shortage_cliente_senza_stock_policy_retrocompatibile(session):
    """by_article con fav < 0 senza stock policy: comportamento V1 invariato."""
    _famiglia(session, aggrega=True)
    _art(session)
    _config(session)
    # inventory=50, set_aside=0, committed=0 -> avail=50
    # incoming=0 -> fav=50 >= 0 -> NO candidate (nessun trigger configurato)
    _avail(session, inventory=50)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert result == []


def test_shortage_cliente_genera_candidate(session):
    """fav < 0: candidate con reason_code='future_availability_negative'."""
    _famiglia(session, aggrega=True)
    _art(session)
    _config(session)
    # inventory=10, demand=0, incoming=0 -> avail=10 -> fav=10 >= 0 -> NO
    # inventory=0, set_aside=0, committed=80 -> avail=-80 -> fav=-80 -> YES
    _avail(session, inventory=0, set_aside=0, committed=80)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 1
    item = result[0]
    assert item.reason_code == "future_availability_negative"
    assert item.customer_shortage_qty == Decimal("80")
    assert item.future_availability_qty == Decimal("-80")


def test_shortage_cliente_required_qty_minimum(session):
    """required_qty_minimum = abs(fav) per shortage cliente."""
    _famiglia(session, aggrega=True)
    _art(session)
    _config(session)
    _avail(session, inventory=0, set_aside=0, committed=50)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert result[0].required_qty_minimum == Decimal("50")


# ─── Candidatura stock trigger (fav >= 0 ma < trigger) ───────────────────────

def test_stock_trigger_genera_candidate(session):
    """fav=25, trigger=30 -> candidate con reason_code='stock_below_trigger'."""
    _setup_stock_logic(session)
    # Famiglia con trigger_months=2 (trigger = 2 * monthly_base)
    # Movimenti: 3 mesi da 15/mese -> monthly_base=15 -> trigger=30
    # target_months=6 -> target=90
    _famiglia(session, stock_months=Decimal("6"), stock_trigger_months=Decimal("2"))
    _art(session)
    _config(session)
    # Movimenti recenti per generare monthly_base
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # fav = 25 < trigger=30 -> candidate (fav >= 0 quindi non shortage)
    _avail(session, inventory=25)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 1
    item = result[0]
    assert item.reason_code == "stock_below_trigger"
    assert item.primary_driver == "stock"
    assert item.future_availability_qty == Decimal("25")
    # customer_shortage = max(-25, 0) = 0
    assert item.customer_shortage_qty == Decimal("0")
    # replenishment = max(90 - max(25, 0), 0) = max(90-25, 0) = 65
    assert item.stock_replenishment_qty == Decimal("65")
    assert item.required_qty_minimum == Decimal("65")
    # total = 0 + 65 = 65
    assert item.required_qty_total == Decimal("65")


def test_stock_trigger_non_raggiunto_non_candidate(session):
    """fav >= trigger: nessun candidate."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("6"), stock_trigger_months=Decimal("2"))
    _art(session)
    _config(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # trigger = 2 * 15 = 30; fav = 100 >= 30 -> NO candidate
    _avail(session, inventory=100)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert result == []


# ─── Nessun doppio conteggio (DL-ARCH-V2-030 §9) ────────────────────────────

def test_nessun_doppio_conteggio_shortage_e_replenishment(session):
    """Caso spec §9: fav=-50, target=500 -> un solo candidate con breakdown separato."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("6"), stock_trigger_months=Decimal("2"))
    _art(session)
    _config(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # monthly_base=15, target=6*15=90, trigger=2*15=30
    # inventory=0, committed=50 -> avail=-50 -> fav=-50
    _avail(session, inventory=0, set_aside=0, committed=50)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 1  # un solo candidate
    item = result[0]
    assert item.primary_driver == "customer"
    # customer_shortage = max(-(-50), 0) = 50
    assert item.customer_shortage_qty == Decimal("50")
    # replenishment = max(90 - max(-50, 0), 0) = max(90-0, 0) = 90
    assert item.stock_replenishment_qty == Decimal("90")
    # total = 50 + 90 = 140
    assert item.required_qty_total == Decimal("140")
    assert item.required_qty_minimum == Decimal("50")


# ─── Articolo senza stock policy: campi None ──────────────────────────────────

def test_shortage_senza_stock_policy_campi_none(session):
    """fav < 0 senza stock policy: customer_shortage e required_qty_total valorizzati,
    ma stock_replenishment_qty = None (no target configurato)."""
    _famiglia(session, aggrega=True, stock_months=None, stock_trigger_months=None)
    _art(session)
    _config(session)
    _avail(session, inventory=0, committed=30)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 1
    item = result[0]
    assert item.primary_driver == "customer"
    assert item.customer_shortage_qty == Decimal("30")
    assert item.stock_replenishment_qty is None
    assert item.required_qty_total == Decimal("30")  # = 30 + 0 (None trattato come 0)


# ─── Test: gestione_scorte_attiva (TASK-V2-099) ──────────────────────────────

def test_stock_trigger_escluso_se_gestione_scorte_off(session):
    """Articolo by_article con gestione_scorte_off non genera candidato su trigger.

    La disponibilita e positiva (fav > 0) quindi nessun shortage.
    Senza gestione_scorte_attiva non c'e trigger_qty → non e candidato.
    """
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("3"), stock_trigger_months=Decimal("2"), gestione_scorte_attiva=False)
    _art(session)
    _config(session)
    # Disponibilita positiva ma inferiore al trigger (se trigger fosse attivo sarebbe candidato)
    _avail(session, inventory=5, set_aside=0, committed=0)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 0


def test_shortage_ancora_candidato_senza_gestione_scorte(session):
    """Articolo by_article con gestione_scorte_off e ancora candidato se ha shortage (fav < 0).

    stock_eff = max(inventory, 0) = 10; avail_eff = 10 - 0 - 50 = -40 → fav < 0.
    """
    _famiglia(session, gestione_scorte_attiva=False)
    _art(session)
    _config(session)
    # committed > stock_eff → avail_eff negativa → fav < 0
    _avail(session, inventory=10, set_aside=0, committed=50)
    session.commit()

    result = list_planning_candidates_v1(session)
    assert len(result) == 1
    item = result[0]
    assert item.reason_code == "future_availability_negative"
    assert item.stock_replenishment_qty is None  # nessuna stock policy


# ─── Ramo by_customer_order_line invariato ───────────────────────────────────

def test_by_customer_order_line_no_stock_fields(session):
    """Il ramo by_customer_order_line non ha campi stock policy."""
    session.add(ArticoloFamiglia(
        code="FAM_COL",
        label="Famiglia COL",
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=False,  # by_customer_order_line
    ))
    session.flush()
    _art(session, codice="ART_COL")
    session.add(CoreArticoloConfig(
        codice_articolo="ART_COL",
        famiglia_code="FAM_COL",
        updated_at=_NOW,
    ))
    session.flush()
    session.add(SyncRigaOrdineCliente(
        order_reference="ORD001",
        line_reference=1,
        article_code="ART_COL",
        ordered_qty=Decimal("100"),
        set_aside_qty=Decimal("0"),
        fulfilled_qty=Decimal("0"),
        synced_at=_NOW,
    ))
    session.commit()

    result = list_planning_candidates_v1(session)
    by_col = [r for r in result if r.planning_mode == "by_customer_order_line"]
    assert len(by_col) == 1
    item = by_col[0]
    assert item.primary_driver == "customer"
    assert item.customer_shortage_qty is None
    assert item.stock_replenishment_qty is None
    assert item.required_qty_total is None
    assert item.reason_code == "line_demand_uncovered"
