"""
Test del Core slice `warnings` V1 (TASK-V2-076, DL-ARCH-V2-029).

Copertura:
- is_negative_stock: logica pura
  - inventory_qty < 0 -> True
  - inventory_qty == 0 -> False
  - inventory_qty > 0 -> False
  - None -> False
- list_warnings_v1: query + read model con SQLite in-memory
  - articolo con stock negativo -> genera NEGATIVE_STOCK
  - articolo con stock positivo -> nessun warning
  - articolo con stock zero -> nessun warning
  - articolo non attivo in sync_articoli -> nessun warning (fuori perimetro)
  - articolo non presente in sync_articoli -> nessun warning
  - piu articoli negativi -> un warning per articolo (no duplicati)
  - warning_id unico per articolo
  - campi shape canonica verificati
  - anomaly_qty = abs(stock_calculated)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.warnings import is_negative_stock, list_warnings_v1

# Importati per registrare tutti i modelli in Base.metadata prima di create_all
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _art(session, codice_articolo, attivo=True):
    session.add(SyncArticolo(
        codice_articolo=codice_articolo,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _avail(session, article_code, inventory_qty, set_aside_qty=Decimal("0"), committed_qty=Decimal("0")):
    availability_qty = inventory_qty - set_aside_qty - committed_qty
    session.add(CoreAvailability(
        article_code=article_code,
        inventory_qty=inventory_qty,
        customer_set_aside_qty=set_aside_qty,
        committed_qty=committed_qty,
        availability_qty=availability_qty,
        computed_at=_NOW,
    ))
    session.flush()


# ─── Logica pura ──────────────────────────────────────────────────────────────

def test_is_negative_stock_negativo():
    assert is_negative_stock(Decimal("-1")) is True


def test_is_negative_stock_molto_negativo():
    assert is_negative_stock(Decimal("-200.5")) is True


def test_is_negative_stock_zero():
    assert is_negative_stock(Decimal("0")) is False


def test_is_negative_stock_positivo():
    assert is_negative_stock(Decimal("25")) is False


def test_is_negative_stock_none():
    assert is_negative_stock(None) is False


# ─── Query: NEGATIVE_STOCK generato ──────────────────────────────────────────

def test_stock_negativo_genera_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    w = warnings[0]
    assert w.type == "NEGATIVE_STOCK"
    assert w.entity_type == "article"
    assert w.entity_key == "ART001"
    assert w.article_code == "ART001"
    assert w.stock_calculated == Decimal("-10")
    assert w.anomaly_qty == Decimal("10")
    assert w.warning_id == "NEGATIVE_STOCK:ART001"
    assert w.source_module == "warnings"
    assert "produzione" in w.visible_to_areas
    assert w.severity == "warning"
    # SQLite restituisce datetime naive — confronto senza timezone
    assert w.created_at.replace(tzinfo=None) == _NOW.replace(tzinfo=None)


def test_anomaly_qty_e_abs_stock(session):
    """anomaly_qty = abs(stock_calculated)."""
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("-37.5"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    assert warnings[0].anomaly_qty == Decimal("37.5")
    assert warnings[0].stock_calculated == Decimal("-37.5")


# ─── Query: nessun warning ────────────────────────────────────────────────────

def test_stock_positivo_nessun_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("25"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_stock_zero_nessun_warning(session):
    _art(session, "ART001")
    _avail(session, "ART001", Decimal("0"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_articolo_non_attivo_nessun_warning(session):
    """Articolo fuori perimetro operativo (attivo=False) non genera warning."""
    _art(session, "ART001", attivo=False)
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_articolo_non_in_sync_nessun_warning(session):
    """Stock negativo senza corrispondente in sync_articoli non genera warning."""
    _avail(session, "ART001", Decimal("-5"))
    session.commit()

    assert list_warnings_v1(session) == []


def test_tabella_vuota_nessun_warning(session):
    assert list_warnings_v1(session) == []


# ─── Query: piu articoli, no duplicati ────────────────────────────────────────

def test_piu_articoli_un_warning_ciascuno(session):
    """Ogni articolo con stock negativo genera esattamente un warning."""
    _art(session, "ART001")
    _art(session, "ART002")
    _art(session, "ART003")
    _avail(session, "ART001", Decimal("-5"))
    _avail(session, "ART002", Decimal("10"))
    _avail(session, "ART003", Decimal("-20"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 2
    codes = {w.article_code for w in warnings}
    assert codes == {"ART001", "ART003"}


def test_warning_id_unici(session):
    """warning_id distinto per ogni articolo — nessun duplicato."""
    _art(session, "ART001")
    _art(session, "ART002")
    _avail(session, "ART001", Decimal("-5"))
    _avail(session, "ART002", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)
    ids = [w.warning_id for w in warnings]

    assert len(ids) == len(set(ids))
    assert set(ids) == {"NEGATIVE_STOCK:ART001", "NEGATIVE_STOCK:ART002"}


def test_ordinamento_peggiori_prima(session):
    """Stock piu negativo appare prima nell'ordinamento."""
    _art(session, "ART001")
    _art(session, "ART002")
    _avail(session, "ART001", Decimal("-3"))
    _avail(session, "ART002", Decimal("-20"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 2
    assert warnings[0].article_code == "ART002"  # -20 < -3
    assert warnings[1].article_code == "ART001"


def test_mix_attivi_e_non_attivi(session):
    """Solo articoli attivi generano warning, anche con stock negativo gli inattivi no."""
    _art(session, "ATTIVO")
    _art(session, "INATTIVO", attivo=False)
    _avail(session, "ATTIVO", Decimal("-5"))
    _avail(session, "INATTIVO", Decimal("-10"))
    session.commit()

    warnings = list_warnings_v1(session)

    assert len(warnings) == 1
    assert warnings[0].article_code == "ATTIVO"
