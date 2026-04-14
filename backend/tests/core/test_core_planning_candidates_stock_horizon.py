"""
Test Planning Candidates stock horizon cap on commitments (TASK-V2-101, DL-ARCH-V2-031 §4-5).

Copertura:
- stock_horizon_availability_qty_v1: helper puro
- _capped_commitments_from_lines: logica di capping con/senza delivery date
- Integrazione list_planning_candidates_v1:
  - ordine lontano escluso dal capping -> stock_replenishment_qty ridotta
  - ordine entro orizzonte incluso nel capping
  - ordine senza data_consegna incluso (conservativo)
  - nessun articolo beyond horizon: stessa logica di prima
  - effective_stock_months=None -> nessun capping (fallback a avail_eff)
  - customer_shortage_qty invariata (usa fav, non stock_horizon)
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    stock_horizon_availability_qty_v1,
)
from nssp_v2.core.planning_candidates.queries import (
    _capped_commitments_from_lines,
    list_planning_candidates_v1,
)
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente

# Registrazione Base.metadata
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)
_TODAY = date.today()


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


# ─── Helper builders ──────────────────────────────────────────────────────────

def _setup_stock_logic(session: Session):
    from nssp_v2.core.stock_policy.config import set_stock_logic_config
    set_stock_logic_config(
        session,
        monthly_base_strategy_key="monthly_stock_base_from_sales_v1",
        monthly_base_params={
            "windows_months": [3],
            "percentile": 50,
            "zscore_threshold": 0.0,
            "min_nonzero_months": 1,
            "min_movements": 0,
        },
        capacity_logic_params={},
    )
    session.flush()


def _add_movement(session: Session, codice: str, scaricata: Decimal, data: datetime):
    session.add(SyncMagReale(
        id_movimento=abs(hash((codice, float(scaricata), str(data)))) % 999999,
        codice_articolo=codice,
        quantita_scaricata=float(scaricata),
        data_movimento=data,
        synced_at=_NOW,
    ))
    session.flush()


def _famiglia(session: Session, stock_months: Decimal | None = None,
              stock_trigger_months: Decimal | None = None) -> ArticoloFamiglia:
    f = ArticoloFamiglia(
        code="FAM1",
        label="Famiglia Test",
        sort_order=1,
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=True,
        stock_months=stock_months,
        stock_trigger_months=stock_trigger_months,
        gestione_scorte_attiva=True,
    )
    session.add(f)
    session.flush()
    return f


def _articolo(session: Session, codice: str = "ART001") -> SyncArticolo:
    art = SyncArticolo(
        codice_articolo=codice,
        descrizione_1=codice,
        attivo=True,
        synced_at=_NOW,
    )
    session.add(art)
    config = CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code="FAM1",
        updated_at=_NOW,
    )
    session.add(config)
    session.flush()
    return art


def _avail(session: Session, codice: str = "ART001",
           inventory: int = 100, committed: int = 0, set_aside: int = 0) -> CoreAvailability:
    inv = Decimal(str(inventory))
    com = Decimal(str(committed))
    sa = Decimal(str(set_aside))
    av = CoreAvailability(
        article_code=codice.strip().upper(),
        inventory_qty=inv,
        committed_qty=com,
        customer_set_aside_qty=sa,
        availability_qty=inv - sa - com,
        computed_at=_NOW,
    )
    session.add(av)
    session.flush()
    return av


def _riga(session: Session, codice: str, qty: Decimal, delivery: datetime | None,
          order_ref: str = "ORD1", line_ref: int = 1) -> SyncRigaOrdineCliente:
    r = SyncRigaOrdineCliente(
        order_reference=order_ref,
        line_reference=line_ref,
        article_code=codice,
        ordered_qty=qty,
        fulfilled_qty=Decimal("0"),
        set_aside_qty=Decimal("0"),
        expected_delivery_date=delivery,
        synced_at=_NOW,
    )
    session.add(r)
    session.flush()
    return r


# ─── Test: stock_horizon_availability_qty_v1 (puro) ─────────────────────────

def test_stock_horizon_avail_base():
    # stock_eff=100, set_aside=10, capped_committed=50, incoming=20
    # result = 100 - 10 - 50 + 20 = 60
    result = stock_horizon_availability_qty_v1(
        Decimal("100"), Decimal("10"), Decimal("50"), Decimal("20")
    )
    assert result == Decimal("60")


def test_stock_horizon_avail_negativo():
    # capped_committed > stock_eff -> negativo possibile
    result = stock_horizon_availability_qty_v1(
        Decimal("50"), Decimal("0"), Decimal("100"), Decimal("0")
    )
    assert result == Decimal("-50")


def test_stock_horizon_avail_zero_committed():
    result = stock_horizon_availability_qty_v1(
        Decimal("100"), Decimal("0"), Decimal("0"), Decimal("0")
    )
    assert result == Decimal("100")


# ─── Test: _capped_commitments_from_lines ────────────────────────────────────

def test_capped_tutto_entro_orizzonte():
    lookahead = _TODAY + timedelta(days=60)
    lines = [
        (Decimal("50"), _TODAY + timedelta(days=10)),
        (Decimal("30"), _TODAY + timedelta(days=30)),
    ]
    assert _capped_commitments_from_lines(lines, lookahead) == Decimal("80")


def test_capped_nulla_entro_orizzonte():
    lookahead = _TODAY + timedelta(days=30)
    lines = [
        (Decimal("50"), _TODAY + timedelta(days=60)),
        (Decimal("30"), _TODAY + timedelta(days=90)),
    ]
    assert _capped_commitments_from_lines(lines, lookahead) == Decimal("0")


def test_capped_misto():
    lookahead = _TODAY + timedelta(days=60)
    lines = [
        (Decimal("50"), _TODAY + timedelta(days=30)),   # dentro
        (Decimal("40"), _TODAY + timedelta(days=90)),   # fuori
        (Decimal("20"), None),                           # None -> dentro (conservativo)
    ]
    assert _capped_commitments_from_lines(lines, lookahead) == Decimal("70")


def test_capped_none_incluso_conservativo():
    lookahead = _TODAY + timedelta(days=30)
    lines = [(Decimal("100"), None)]
    assert _capped_commitments_from_lines(lines, lookahead) == Decimal("100")


def test_capped_boundary():
    """Data esattamente al limite -> inclusa."""
    lookahead = _TODAY + timedelta(days=60)
    lines = [(Decimal("50"), _TODAY + timedelta(days=60))]
    assert _capped_commitments_from_lines(lines, lookahead) == Decimal("50")


def test_capped_lista_vuota():
    lookahead = _TODAY + timedelta(days=60)
    assert _capped_commitments_from_lines([], lookahead) == Decimal("0")


# ─── Test: integrazione list_planning_candidates_v1 ─────────────────────────

def test_stock_horizon_riduce_replenishment(session: Session):
    """Ordini lontani esclusi: stock_horizon_avail > fav -> replenishment ridotta.

    Setup:
      inventory=100, committed_avail=150 (2 righe da 90 e 60)
      Line A: qty=90, delivery today+20 (entro 60gg di 2 mesi)
      Line B: qty=60, delivery today+90 (oltre 60gg)
      monthly_base=15, stock_months=6 -> target=90, trigger=30

    Senza capping: replenishment = max(90 - max(-50, 0), 0) = 90
    Con capping:   capped=90 (solo linea A)
                   stock_horizon_avail = 100 - 0 - 90 = 10
                   replenishment = max(90 - max(10, 0), 0) = 80
    """
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("2"), stock_trigger_months=Decimal("1"))
    _articolo(session)
    # Movimenti: 3 mesi da 15/mese -> monthly_base=15; trigger=1*15=15; target=2*15=30
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # inventory=100, committed_avail=150 -> avail_eff=100-150=-50, fav=-50 (shortage)
    _avail(session, inventory=100, committed=150)
    # Linea A: qty=90, within 60gg
    delivery_a = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=20)
    _riga(session, "ART001", Decimal("90"), delivery_a, line_ref=1)
    # Linea B: qty=60, outside 60gg
    delivery_b = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=90)
    _riga(session, "ART001", Decimal("60"), delivery_b, line_ref=2)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    c = candidates[0]

    # customer_shortage usa fav completo (non cappato)
    assert c.customer_shortage_qty == Decimal("50")  # max(-(-50),0) = 50
    assert c.future_availability_qty == Decimal("-50")

    # stock_replenishment usa stock_horizon_avail (con capping a 60gg)
    # capped_committed = 90, stock_horizon_avail = 100-90=10
    # replenishment = max(30 - max(10,0), 0) = max(20, 0) = 20
    assert c.stock_replenishment_qty == Decimal("20")


def test_stock_horizon_customer_shortage_invariata(session: Session):
    """customer_shortage_qty usa fav completo, non il valore cappato."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("2"), stock_trigger_months=Decimal("1"))
    _articolo(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # fav = 50 - 120 = -70
    _avail(session, inventory=50, committed=120)
    delivery_within = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=10)
    _riga(session, "ART001", Decimal("60"), delivery_within, line_ref=1)
    delivery_outside = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=90)
    _riga(session, "ART001", Decimal("60"), delivery_outside, line_ref=2)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    # customer_shortage = max(-fav, 0) = max(70, 0) = 70 (usa fav completo)
    assert candidates[0].customer_shortage_qty == Decimal("70")


def test_stock_horizon_ordini_senza_data_inclusi(session: Session):
    """Ordini senza data_consegna inclusi nel capping (conservativo)."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("2"), stock_trigger_months=Decimal("1"))
    _articolo(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # inventory=100, committed=90 -> avail_eff=100-90=10, fav=10 >= 0
    # trigger=1*15=15, fav=10 < trigger=15 -> candidate stock_below_trigger
    _avail(session, inventory=100, committed=90)
    # Riga senza data -> inclusa nel capping
    _riga(session, "ART001", Decimal("90"), None)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    # capped_committed = 90 (inclusa perche senza data)
    # stock_horizon_avail = 100 - 90 = 10 (stesso di avail_eff qui)
    # replenishment = max(30 - max(10,0), 0) = max(20,0) = 20
    assert candidates[0].stock_replenishment_qty == Decimal("20")


def test_stock_horizon_nessun_ordine_nessun_capping(session: Session):
    """Senza righe ordine: capped_committed=0, stock_horizon_avail = stock_eff."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("2"), stock_trigger_months=Decimal("1"))
    _articolo(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    # fav=10 < trigger=15 -> candidate
    _avail(session, inventory=10)
    # nessuna riga ordine
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    # capped_committed = 0, stock_horizon_avail = 10
    # target=30, replenishment = max(30-10, 0) = 20
    assert candidates[0].stock_replenishment_qty == Decimal("20")


def test_stock_horizon_effective_months_none_no_capping(session: Session):
    """Se effective_stock_months=None (no stock policy), usa avail_eff senza capping.

    In questo caso target=None e replenishment=None (no stock policy).
    """
    # Famiglia senza stock_months -> effective_stock_months=None
    _famiglia(session, stock_months=None, stock_trigger_months=None)
    _articolo(session)
    # fav = -50 -> shortage candidate
    _avail(session, inventory=0, committed=50)
    delivery_outside = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=90)
    _riga(session, "ART001", Decimal("50"), delivery_outside)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    c = candidates[0]
    # shortage = 50, replenishment = None (no stock policy)
    assert c.customer_shortage_qty == Decimal("50")
    assert c.stock_replenishment_qty is None


def test_customer_horizon_non_influenza_stock_replenishment(session: Session):
    """Il customer_horizon_days e solo presentazione customer, non cap stock."""
    _setup_stock_logic(session)
    _famiglia(session, stock_months=Decimal("2"), stock_trigger_months=Decimal("1"))
    _articolo(session)
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 4, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 3, 1))
    _add_movement(session, "ART001", Decimal("15"), datetime(2026, 2, 1))
    _avail(session, inventory=100, committed=150)
    delivery_within_stock = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=20)
    delivery_outside_stock = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=90)
    _riga(session, "ART001", Decimal("90"), delivery_within_stock, line_ref=1)
    _riga(session, "ART001", Decimal("60"), delivery_outside_stock, line_ref=2)
    session.commit()

    r_short = list_planning_candidates_v1(session, customer_horizon_days=10)
    r_long = list_planning_candidates_v1(session, customer_horizon_days=365)

    assert len(r_short) == 1
    assert len(r_long) == 1
    assert r_short[0].stock_replenishment_qty == Decimal("20")
    assert r_long[0].stock_replenishment_qty == Decimal("20")
