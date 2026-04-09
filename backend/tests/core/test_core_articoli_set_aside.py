"""
Test di integrazione per l'estensione `customer_set_aside_qty` nel dettaglio articolo (TASK-V2-045).

Verificano:
- customer_set_aside_qty = None quando non esistono quote appartate per l'articolo
- customer_set_aside_qty = somma delle quote appartate quando esistono
- set_aside_computed_at popolato quando la quota e presente
- set_aside_computed_at = None quando non ci sono quote appartate
- piu record set_aside per lo stesso articolo sommati correttamente
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.articoli.queries import get_articolo_detail


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


def _insert_articolo(session, codice: str, **kwargs) -> SyncArticolo:
    art = SyncArticolo(
        codice_articolo=codice,
        descrizione_1="Articolo test",
        descrizione_2=None,
        unita_misura_codice="PZ",
        attivo=True,
        synced_at=_NOW,
        **kwargs,
    )
    session.add(art)
    session.flush()
    return art


def _insert_set_aside(session, article_code: str, qty: Decimal) -> CoreCustomerSetAside:
    r = CoreCustomerSetAside(
        article_code=article_code,
        source_type="customer_order",
        source_reference=f"ORD001/1",
        set_aside_qty=qty,
        computed_at=_NOW,
    )
    session.add(r)
    session.flush()
    return r


# ─── Test ─────────────────────────────────────────────────────────────────────

def test_customer_set_aside_qty_none_se_nessun_record(session):
    """Se non ci sono quote appartate, customer_set_aside_qty e None."""
    _insert_articolo(session, "ART001")
    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.customer_set_aside_qty is None
    assert detail.set_aside_computed_at is None


def test_customer_set_aside_qty_uguale_al_record(session):
    """Se esiste un record set_aside, customer_set_aside_qty rispecchia la qty."""
    _insert_articolo(session, "ART001")
    _insert_set_aside(session, "ART001", Decimal("15.00000"))

    detail = get_articolo_detail(session, "ART001")
    assert detail is not None
    assert detail.customer_set_aside_qty == Decimal("15.00000")


def test_set_aside_computed_at_popolato(session):
    """set_aside_computed_at e valorizzato quando la quota e presente."""
    _insert_articolo(session, "ART001")
    _insert_set_aside(session, "ART001", Decimal("10.00000"))

    detail = get_articolo_detail(session, "ART001")
    assert detail.set_aside_computed_at is not None


def test_customer_set_aside_qty_somma_piu_record(session):
    """Piu record set_aside per lo stesso articolo vengono sommati."""
    _insert_articolo(session, "ART001")
    r1 = CoreCustomerSetAside(
        article_code="ART001",
        source_type="customer_order",
        source_reference="ORD001/1",
        set_aside_qty=Decimal("10.00000"),
        computed_at=_NOW,
    )
    r2 = CoreCustomerSetAside(
        article_code="ART001",
        source_type="customer_order",
        source_reference="ORD002/1",
        set_aside_qty=Decimal("7.00000"),
        computed_at=_NOW,
    )
    session.add_all([r1, r2])
    session.flush()

    detail = get_articolo_detail(session, "ART001")
    assert detail.customer_set_aside_qty == Decimal("17.00000")


def test_customer_set_aside_isolato_per_articolo(session):
    """Le quote appartate di un articolo non interferiscono con quelle di un altro."""
    _insert_articolo(session, "ART001")
    _insert_articolo(session, "ART002")
    _insert_set_aside(session, "ART002", Decimal("20.00000"))

    detail = get_articolo_detail(session, "ART001")
    assert detail.customer_set_aside_qty is None
