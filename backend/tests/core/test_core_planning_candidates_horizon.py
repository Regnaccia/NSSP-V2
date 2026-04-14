"""
Test Planning Candidates customer horizon flag (TASK-V2-100, DL-ARCH-V2-031 §3).

Copertura:
- _is_within_customer_horizon: helper puro
- is_within_customer_horizon = True  se nearest delivery <= oggi + 30
- is_within_customer_horizon = False se nearest delivery > oggi + 30
- is_within_customer_horizon = None  se nessuna riga ordine ha expected_delivery_date
- boundary: delivery = oggi + 30 -> True (incluso)
- nearest delivery usata: piu riga con date diverse -> si usa la piu vicina
- by_customer_order_line: flag sempre None
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.queries import (
    _DEFAULT_CUSTOMER_HORIZON_DAYS,
    _is_within_customer_horizon,
    list_planning_candidates_v1,
)
from nssp_v2.core.stock_policy.config_model import CoreStockLogicConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
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

def _famiglia(session: Session, code: str = "FAM") -> ArticoloFamiglia:
    f = ArticoloFamiglia(
        code=code,
        label=code,
        sort_order=1,
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=True,
        stock_months=None,
        stock_trigger_months=None,
        gestione_scorte_attiva=False,  # stock policy off — test solo horizon
    )
    session.add(f)
    session.flush()
    return f


def _articolo(session: Session, codice: str, famiglia_code: str = "FAM") -> SyncArticolo:
    art = SyncArticolo(
        codice_articolo=codice,
        descrizione_1=codice,
        descrizione_2=None,
        attivo=True,
        source_modified_at=_NOW,
        synced_at=_NOW,
    )
    session.add(art)
    config = CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        updated_at=_NOW,
    )
    session.add(config)
    session.flush()
    return art


def _avail(session: Session, codice: str, inventory: Decimal = Decimal("0"),
           committed: Decimal = Decimal("100"), set_aside: Decimal = Decimal("0")) -> CoreAvailability:
    """Disponibilita con fav < 0 (candidate per shortage cliente)."""
    av = CoreAvailability(
        article_code=codice.strip().upper(),
        inventory_qty=inventory,
        committed_qty=committed,
        customer_set_aside_qty=set_aside,
        availability_qty=inventory - set_aside - committed,
        computed_at=_NOW,
    )
    session.add(av)
    session.flush()
    return av


def _riga(
    session: Session,
    codice: str,
    delivery_date: datetime | None,
    order_ref: str = "ORD001",
    line_ref: int = 1,
    ordered: Decimal = Decimal("10"),
) -> SyncRigaOrdineCliente:
    r = SyncRigaOrdineCliente(
        order_reference=order_ref,
        line_reference=line_ref,
        article_code=codice,
        ordered_qty=ordered,
        fulfilled_qty=Decimal("0"),
        set_aside_qty=Decimal("0"),
        expected_delivery_date=delivery_date,
        synced_at=_NOW,
    )
    session.add(r)
    session.flush()
    return r


def _setup(session: Session, codice: str = "ART001") -> None:
    """Setup minimo: famiglia + articolo + disponibilita con shortage."""
    _famiglia(session)
    _articolo(session, codice)
    _avail(session, codice)
    session.commit()


# ─── Test helper puro _is_within_customer_horizon ────────────────────────────

def test_helper_none_se_nessuna_data():
    assert _is_within_customer_horizon(None, 30) is None


def test_helper_true_data_passata():
    yesterday = date.today() - timedelta(days=1)
    assert _is_within_customer_horizon(yesterday, 30) is True


def test_helper_true_data_oggi():
    assert _is_within_customer_horizon(date.today(), 30) is True


def test_helper_true_boundary():
    """Data esattamente al limite dell'orizzonte -> True (incluso)."""
    boundary = date.today() + timedelta(days=30)
    assert _is_within_customer_horizon(boundary, 30) is True


def test_helper_false_oltre_orizzonte():
    futura = date.today() + timedelta(days=31)
    assert _is_within_customer_horizon(futura, 30) is False


def test_helper_orizzonte_zero():
    """Con horizon=0: solo oggi o passato e dentro."""
    assert _is_within_customer_horizon(date.today(), 0) is True
    assert _is_within_customer_horizon(date.today() + timedelta(days=1), 0) is False


def test_default_horizon_days():
    assert _DEFAULT_CUSTOMER_HORIZON_DAYS == 30


# ─── Test integrazione list_planning_candidates_v1 ───────────────────────────

def test_within_horizon_true(session: Session):
    """Delivery entro 30 giorni -> flag True."""
    _setup(session)
    delivery = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=10)
    _riga(session, "ART001", delivery_date=delivery)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is True


def test_within_horizon_false(session: Session):
    """Delivery oltre 30 giorni -> flag False."""
    _setup(session)
    delivery = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=45)
    _riga(session, "ART001", delivery_date=delivery)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is False


def test_within_horizon_none_no_delivery_date(session: Session):
    """Nessuna riga con delivery date -> flag None."""
    _setup(session)
    _riga(session, "ART001", delivery_date=None)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is None


def test_within_horizon_none_nessuna_riga(session: Session):
    """Nessuna riga ordine per questo articolo -> flag None."""
    _setup(session)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is None


def test_nearest_delivery_usata(session: Session):
    """Con piu righe, viene usata la data piu vicina (prossima)."""
    _setup(session)
    # Riga 1: entro orizzonte
    delivery_within = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=10)
    _riga(session, "ART001", delivery_date=delivery_within, line_ref=1)
    # Riga 2: fuori orizzonte
    delivery_outside = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=50)
    _riga(session, "ART001", delivery_date=delivery_outside, line_ref=2)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    # La piu vicina e entro orizzonte -> True
    assert candidates[0].is_within_customer_horizon is True


def test_nearest_delivery_boundary(session: Session):
    """Delivery esattamente al limite (oggi + 30) -> True."""
    _setup(session)
    boundary = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=30)
    _riga(session, "ART001", delivery_date=boundary)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is True


def test_candidati_non_persi_fuori_orizzonte(session: Session):
    """I candidate fuori orizzonte non devono essere esclusi (solo flag False)."""
    _setup(session)
    delivery = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=90)
    _riga(session, "ART001", delivery_date=delivery)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    # Il candidate esiste (non scartato)
    assert len(candidates) == 1
    assert candidates[0].is_within_customer_horizon is False
    assert candidates[0].future_availability_qty < Decimal("0")


def test_by_col_horizon_none(session: Session):
    """by_customer_order_line: is_within_customer_horizon sempre None."""
    f = ArticoloFamiglia(
        code="FAM_COL",
        label="COL",
        sort_order=1,
        is_active=True,
        considera_in_produzione=True,
        aggrega_codice_in_produzione=False,  # -> by_customer_order_line
        stock_months=None,
        stock_trigger_months=None,
        gestione_scorte_attiva=False,
    )
    session.add(f)
    art = SyncArticolo(
        codice_articolo="ARTCOL",
        descrizione_1="ARTCOL",
        attivo=True,
        source_modified_at=_NOW,
        synced_at=_NOW,
    )
    session.add(art)
    cfg = CoreArticoloConfig(
        codice_articolo="ARTCOL",
        famiglia_code="FAM_COL",
        updated_at=_NOW,
    )
    session.add(cfg)
    # Riga ordine scoperta (no supply collegata)
    delivery = datetime(_TODAY.year, _TODAY.month, _TODAY.day) + timedelta(days=5)
    riga = SyncRigaOrdineCliente(
        order_reference="ORDCOL",
        line_reference=1,
        article_code="ARTCOL",
        ordered_qty=Decimal("50"),
        fulfilled_qty=Decimal("0"),
        set_aside_qty=Decimal("0"),
        expected_delivery_date=delivery,
        synced_at=_NOW,
    )
    session.add(riga)
    session.commit()

    candidates = list_planning_candidates_v1(session)
    col_candidates = [c for c in candidates if c.planning_mode == "by_customer_order_line"]
    assert len(col_candidates) == 1
    assert col_candidates[0].is_within_customer_horizon is None
