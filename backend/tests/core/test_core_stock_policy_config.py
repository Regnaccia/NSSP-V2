"""
Test del modello configurativo stock policy V1 (TASK-V2-083, DL-ARCH-V2-030).

Copertura:
- resolve_stock_policy: logica pura di risoluzione effective
  - override presente -> usa override
  - override None, default presente -> usa default famiglia
  - entrambi None -> None
  - override zero -> usa zero (non None)
- get_articolo_detail: espone effective_stock_months, effective_stock_trigger_months, capacity_override_qty
  - senza famiglia: tutti None
  - con famiglia (default): effective = default famiglia
  - con override articolo: effective = override
  - override zero: effective = 0 (non default)
- list_famiglie_catalog: FamigliaRow espone stock_months, stock_trigger_months
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
from nssp_v2.core.articoli.queries import (
    resolve_stock_policy,
    get_articolo_detail,
    list_famiglie_catalog,
)
from nssp_v2.sync.articoli.models import SyncArticolo

# Importati per registrare tutti i modelli in Base.metadata
from nssp_v2.core.availability.models import CoreAvailability  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.core.warnings.config_model import WarningTypeConfig  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


def _art(session, codice="ART001"):
    session.add(SyncArticolo(codice_articolo=codice, attivo=True, synced_at=_NOW))
    session.flush()


def _famiglia(session, code="FAM1", stock_months=None, stock_trigger_months=None):
    session.add(ArticoloFamiglia(
        code=code,
        label=f"Famiglia {code}",
        is_active=True,
        considera_in_produzione=False,
        aggrega_codice_in_produzione=False,
        stock_months=stock_months,
        stock_trigger_months=stock_trigger_months,
    ))
    session.flush()


def _config(
    session,
    codice="ART001",
    famiglia_code=None,
    override_stock_months=None,
    override_stock_trigger_months=None,
    capacity_override_qty=None,
):
    session.add(CoreArticoloConfig(
        codice_articolo=codice,
        famiglia_code=famiglia_code,
        updated_at=_NOW,
        override_stock_months=override_stock_months,
        override_stock_trigger_months=override_stock_trigger_months,
        capacity_override_qty=capacity_override_qty,
    ))
    session.flush()


# ─── resolve_stock_policy: logica pura ───────────────────────────────────────

def test_resolve_override_presente():
    result = resolve_stock_policy(Decimal("2.0"), Decimal("6.0"))
    assert result == Decimal("2.0")


def test_resolve_override_none_usa_default():
    result = resolve_stock_policy(None, Decimal("6.0"))
    assert result == Decimal("6.0")


def test_resolve_entrambi_none():
    assert resolve_stock_policy(None, None) is None


def test_resolve_override_zero_usa_zero():
    """Override=0 e un valore esplicito: non deve cadere sul default."""
    result = resolve_stock_policy(Decimal("0"), Decimal("6.0"))
    assert result == Decimal("0")


def test_resolve_override_none_default_none():
    assert resolve_stock_policy(None, None) is None


# ─── get_articolo_detail: campi stock policy ──────────────────────────────────

def test_articolo_senza_famiglia_stock_policy_none(session):
    _art(session)
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.effective_stock_months is None
    assert detail.effective_stock_trigger_months is None
    assert detail.capacity_override_qty is None


def test_articolo_con_default_famiglia(session):
    _famiglia(session, stock_months=Decimal("3.0"), stock_trigger_months=Decimal("1.5"))
    _art(session)
    _config(session, famiglia_code="FAM1")
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.effective_stock_months == Decimal("3.0")
    assert detail.effective_stock_trigger_months == Decimal("1.5")
    assert detail.capacity_override_qty is None


def test_articolo_con_override_sovrascrive_famiglia(session):
    _famiglia(session, stock_months=Decimal("3.0"), stock_trigger_months=Decimal("1.5"))
    _art(session)
    _config(
        session,
        famiglia_code="FAM1",
        override_stock_months=Decimal("1.0"),
        override_stock_trigger_months=Decimal("0.5"),
        capacity_override_qty=Decimal("500"),
    )
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.effective_stock_months == Decimal("1.0")
    assert detail.effective_stock_trigger_months == Decimal("0.5")
    assert detail.capacity_override_qty == Decimal("500")


def test_articolo_override_parziale(session):
    """Override solo su stock_months — stock_trigger_months eredita dalla famiglia."""
    _famiglia(session, stock_months=Decimal("3.0"), stock_trigger_months=Decimal("1.5"))
    _art(session)
    _config(session, famiglia_code="FAM1", override_stock_months=Decimal("1.0"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.effective_stock_months == Decimal("1.0")
    assert detail.effective_stock_trigger_months == Decimal("1.5")


def test_articolo_capacity_override_senza_famiglia(session):
    """capacity_override_qty e articolo-specifico: funziona anche senza famiglia."""
    _art(session)
    _config(session, capacity_override_qty=Decimal("200"))
    session.commit()

    detail = get_articolo_detail(session, "ART001")
    assert detail.capacity_override_qty == Decimal("200")
    assert detail.effective_stock_months is None


# ─── list_famiglie_catalog: FamigliaRow espone stock fields ──────────────────

def test_famiglia_catalog_espone_stock_fields(session):
    _famiglia(session, stock_months=Decimal("4.0"), stock_trigger_months=Decimal("2.0"))
    session.commit()

    rows = list_famiglie_catalog(session)
    assert len(rows) == 1
    assert rows[0].stock_months == Decimal("4.0")
    assert rows[0].stock_trigger_months == Decimal("2.0")


def test_famiglia_catalog_stock_fields_none_se_non_configurati(session):
    _famiglia(session)
    session.commit()

    rows = list_famiglie_catalog(session)
    assert rows[0].stock_months is None
    assert rows[0].stock_trigger_months is None
