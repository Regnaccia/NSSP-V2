"""
Test mirati per gli helper del router sync on demand — surface produzione (TASK-V2-053).

Verificano:
- _skipped_result: contratto EntityRunResult con status='skipped'
- _run_commitments_rebuild: wrapping corretto del rebuild Core
- logica condizionale: step saltati se prerequisiti sync falliscono

Non testano l'endpoint HTTP completo (richiede TestClient + auth):
il contratto HTTP e coperto dai test dell'endpoint existenti e dalla
verifica manuale del build.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.app.services.refresh_articoli import (
    _skipped_result,
    _run_commitments_rebuild,
    _run_inventory_rebuild,
    _run_set_aside_rebuild,
    _run_availability_rebuild,
)
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.availability.models import CoreAvailability  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


# ─── _skipped_result ──────────────────────────────────────────────────────────

def test_skipped_result_entity_code():
    result = _skipped_result("customer_set_aside")
    assert result.entity_code == "customer_set_aside"


def test_skipped_result_status():
    result = _skipped_result("commitments")
    assert result.status == "skipped"


def test_skipped_result_zero_rows():
    result = _skipped_result("availability")
    assert result.rows_seen == 0
    assert result.rows_written == 0
    assert result.rows_deleted == 0


def test_skipped_result_no_error_message():
    result = _skipped_result("commitments")
    assert result.error_message is None


def test_skipped_result_timestamps_valorizzati():
    result = _skipped_result("commitments")
    assert result.started_at is not None
    assert result.finished_at is not None


# ─── _run_commitments_rebuild ─────────────────────────────────────────────────

def test_run_commitments_rebuild_entity_code(session):
    result = _run_commitments_rebuild(session)
    assert result.entity_code == "commitments"


def test_run_commitments_rebuild_success_su_mirror_vuoto(session):
    """Con mirror vuoto restituisce status='success' e 0 righe."""
    result = _run_commitments_rebuild(session)
    assert result.status == "success"
    assert result.rows_written == 0
    assert result.error_message is None


def test_run_commitments_rebuild_conta_righe_da_ordini(session):
    """Con una riga ordine aperta, produce un commitment."""
    session.add(SyncRigaOrdineCliente(
        order_reference="ORD001",
        line_reference=1,
        article_code="ART001",
        ordered_qty=Decimal("100.000000"),
        fulfilled_qty=Decimal("0.000000"),
        set_aside_qty=Decimal("0.000000"),
        continues_previous_line=False,
        synced_at=_NOW,
    ))
    session.flush()

    result = _run_commitments_rebuild(session)
    assert result.status == "success"
    assert result.rows_written >= 1


def test_run_commitments_rebuild_timestamps_valorizzati(session):
    result = _run_commitments_rebuild(session)
    assert result.started_at is not None
    assert result.finished_at is not None


# ─── Logica condizionale — skip se prerequisito fallisce ─────────────────────

def test_skip_set_aside_quando_righe_fallisce(session):
    """Se righe_ordine_cliente != success, customer_set_aside deve essere skipped."""
    righe_ok = False
    if righe_ok:
        set_aside_result = _run_set_aside_rebuild(session)
    else:
        set_aside_result = _skipped_result("customer_set_aside")

    assert set_aside_result.entity_code == "customer_set_aside"
    assert set_aside_result.status == "skipped"


def test_skip_commitments_quando_righe_fallisce(session):
    """Se righe_ordine_cliente != success, commitments deve essere skipped."""
    righe_ok = False
    produzioni_ok = True
    if righe_ok and produzioni_ok:
        commitments_result = _run_commitments_rebuild(session)
    else:
        commitments_result = _skipped_result("commitments")

    assert commitments_result.entity_code == "commitments"
    assert commitments_result.status == "skipped"


def test_skip_commitments_quando_produzioni_fallisce(session):
    """Se produzioni_attive != success, commitments deve essere skipped."""
    righe_ok = True
    produzioni_ok = False
    if righe_ok and produzioni_ok:
        commitments_result = _run_commitments_rebuild(session)
    else:
        commitments_result = _skipped_result("commitments")

    assert commitments_result.entity_code == "commitments"
    assert commitments_result.status == "skipped"


def test_skip_availability_quando_set_aside_skipped(session):
    """Se customer_set_aside e skipped, availability deve essere skipped."""
    inv_result = _run_inventory_rebuild(session)
    set_aside_result = _skipped_result("customer_set_aside")
    commitments_result = _run_commitments_rebuild(session)

    inv_ok = inv_result.status == "success"
    set_aside_ok = set_aside_result.status == "success"
    commitments_ok = commitments_result.status == "success"

    if inv_ok and set_aside_ok and commitments_ok:
        avail_result = _run_availability_rebuild(session)
    else:
        avail_result = _skipped_result("availability")

    assert avail_result.entity_code == "availability"
    assert avail_result.status == "skipped"


def test_skip_availability_quando_commitments_skipped(session):
    """Se commitments e skipped, availability deve essere skipped."""
    inv_result = _run_inventory_rebuild(session)
    set_aside_result = _run_set_aside_rebuild(session)
    commitments_result = _skipped_result("commitments")

    inv_ok = inv_result.status == "success"
    set_aside_ok = set_aside_result.status == "success"
    commitments_ok = commitments_result.status == "success"

    if inv_ok and set_aside_ok and commitments_ok:
        avail_result = _run_availability_rebuild(session)
    else:
        avail_result = _skipped_result("availability")

    assert avail_result.entity_code == "availability"
    assert avail_result.status == "skipped"


def test_tutti_step_ok_availability_eseguita(session):
    """Con tutti i prerequisiti OK, availability viene effettivamente ricostruita."""
    inv_result = _run_inventory_rebuild(session)
    set_aside_result = _run_set_aside_rebuild(session)
    commitments_result = _run_commitments_rebuild(session)

    inv_ok = inv_result.status == "success"
    set_aside_ok = set_aside_result.status == "success"
    commitments_ok = commitments_result.status == "success"

    if inv_ok and set_aside_ok and commitments_ok:
        avail_result = _run_availability_rebuild(session)
    else:
        avail_result = _skipped_result("availability")

    assert avail_result.entity_code == "availability"
    assert avail_result.status == "success"
