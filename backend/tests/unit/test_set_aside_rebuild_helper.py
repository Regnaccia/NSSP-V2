"""
Test di integrazione per l'helper _run_set_aside_rebuild (TASK-V2-046).

Verifica che il wrapper EntityRunResult prodotto da _run_set_aside_rebuild
rispetti il contratto atteso dal router sync on demand (DL-ARCH-V2-011).
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.app.services.refresh_articoli import _run_set_aside_rebuild
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


# ─── Test ─────────────────────────────────────────────────────────────────────

def test_run_set_aside_rebuild_entity_code(session):
    """Il wrapper restituisce entity_code = 'customer_set_aside'."""
    result = _run_set_aside_rebuild(session)
    assert result.entity_code == "customer_set_aside"


def test_run_set_aside_rebuild_success_su_mirror_vuoto(session):
    """Con mirror vuoto restituisce status='success' e 0 righe."""
    result = _run_set_aside_rebuild(session)
    assert result.status == "success"
    assert result.rows_written == 0
    assert result.error_message is None


def test_run_set_aside_rebuild_conta_righe_create(session):
    """Con dati attivi restituisce il numero di righe create nel fact."""
    session.add(SyncRigaOrdineCliente(
        order_reference="ORD001",
        line_reference=1,
        article_code="ART001",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("0.00000"),
        set_aside_qty=Decimal("10.00000"),
        continues_previous_line=False,
        synced_at=_NOW,
    ))
    session.flush()

    result = _run_set_aside_rebuild(session)
    assert result.status == "success"
    assert result.rows_written == 1


def test_run_set_aside_rebuild_timestamps_valorizzati(session):
    """started_at e finished_at sono valorizzati e non nulli."""
    result = _run_set_aside_rebuild(session)
    assert result.started_at is not None
    assert result.finished_at is not None
