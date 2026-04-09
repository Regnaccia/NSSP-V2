"""
Test di integrazione per il Core slice `customer_set_aside` (TASK-V2-044, DL-ARCH-V2-019).

Verificano:
- set_aside_qty = DOC_QTAP (set_aside_qty dalla riga canonica)
- source_type = "customer_order"
- source_reference = "{order_reference}/{line_reference}"
- righe con set_aside_qty = None non generano record
- righe con set_aside_qty <= 0 non generano record
- righe senza article_code non generano record
- aggregazione per article_code (total_set_aside_qty, set_aside_count)
- piu righe dello stesso articolo aggregate correttamente
- articoli diversi aggregati separatamente
- get_customer_set_aside_by_article per singolo articolo
- list_customer_set_aside con filtro source_type
- rebuild deterministico: stesso input stesso output
- rebuild ricalcola dopo aggiornamento mirror
- rebuild rimuove record di righe nel frattempo azzerate
- mirror vuoto -> 0 record
- separazione da commitments: i due fact coesistono indipendentemente
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.customer_set_aside.queries import (
    rebuild_customer_set_aside,
    list_customer_set_aside,
    get_customer_set_aside_by_article,
)
# Importati per registrare i modelli in Base.metadata prima di create_all
# (necessari per test_separazione_da_commitments che usa rebuild_commitments)
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


def _insert_riga(session, order_ref, line_ref, **kwargs):
    defaults = dict(
        order_date=datetime(2026, 3, 10),
        expected_delivery_date=datetime(2026, 4, 15),
        customer_code="CLI001",
        destination_code="DEST01",
        customer_destination_progressive=None,
        customer_order_reference="REF-001",
        article_code="ART001",
        article_description_segment="Articolo",
        article_measure="150x50",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("20.00000"),
        set_aside_qty=Decimal("15.00000"),
        net_unit_price=Decimal("5.50000"),
        continues_previous_line=False,
        synced_at=_NOW,
    )
    defaults.update(kwargs)
    obj = SyncRigaOrdineCliente(
        order_reference=order_ref,
        line_reference=line_ref,
        **defaults,
    )
    session.add(obj)
    session.flush()
    return obj


# ─── Mapping di base ──────────────────────────────────────────────────────────

def test_set_aside_qty_uguale_a_doc_qtap(session):
    """set_aside_qty e esattamente DOC_QTAP dalla riga canonica."""
    _insert_riga(session, "ORD001", 1, set_aside_qty=Decimal("15.00000"))

    n = rebuild_customer_set_aside(session)
    assert n == 1

    items = list_customer_set_aside(session)
    assert items[0].set_aside_qty == Decimal("15.00000")


def test_source_type_customer_order(session):
    _insert_riga(session, "ORD001", 1)
    rebuild_customer_set_aside(session)

    items = list_customer_set_aside(session)
    assert items[0].source_type == "customer_order"


def test_source_reference_formato(session):
    """source_reference ha il formato '{order_reference}/{line_reference}'."""
    _insert_riga(session, "ORD001", 3)
    rebuild_customer_set_aside(session)

    items = list_customer_set_aside(session)
    assert items[0].source_reference == "ORD001/3"


# ─── Righe escluse ────────────────────────────────────────────────────────────

def test_set_aside_qty_none_non_genera_record(session):
    """Righe con set_aside_qty = None non generano record."""
    _insert_riga(session, "ORD001", 1, set_aside_qty=None)

    n = rebuild_customer_set_aside(session)
    assert n == 0
    assert list_customer_set_aside(session) == []


def test_set_aside_qty_zero_non_genera_record(session):
    """Righe con set_aside_qty = 0 non generano record."""
    _insert_riga(session, "ORD001", 1, set_aside_qty=Decimal("0.00000"))

    n = rebuild_customer_set_aside(session)
    assert n == 0


def test_set_aside_qty_negativo_non_genera_record(session):
    """Righe con set_aside_qty < 0 non generano record."""
    _insert_riga(session, "ORD001", 1, set_aside_qty=Decimal("-5.00000"))

    n = rebuild_customer_set_aside(session)
    assert n == 0


def test_riga_senza_article_code_non_genera_record(session):
    """Righe con article_code=None non generano record."""
    _insert_riga(session, "ORD001", 1,
                 article_code=None,
                 continues_previous_line=True,
                 ordered_qty=None, fulfilled_qty=None, set_aside_qty=Decimal("5.00000"))

    n = rebuild_customer_set_aside(session)
    assert n == 0


def test_riga_con_set_aside_positivo_inclusa(session):
    """Riga con article_code valorizzato e set_aside_qty > 0 genera record."""
    _insert_riga(session, "ORD001", 1, set_aside_qty=Decimal("10.00000"))

    n = rebuild_customer_set_aside(session)
    assert n == 1


def test_rebuild_normalizza_article_code(session):
    """Il fact usa article_code canonico trim+uppercase."""
    _insert_riga(
        session,
        "ORD001",
        1,
        article_code=" art001 ",
        set_aside_qty=Decimal("10.00000"),
    )

    rebuild_customer_set_aside(session)

    items = list_customer_set_aside(session)
    assert len(items) == 1
    assert items[0].article_code == "ART001"


# ─── Aggregazione per articolo ────────────────────────────────────────────────

def test_aggregazione_per_articolo_piu_righe(session):
    """Piu righe dello stesso articolo sommano il loro set_aside_qty."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 set_aside_qty=Decimal("10.00000"))
    _insert_riga(session, "ORD001", 2, article_code="ART001",
                 set_aside_qty=Decimal("5.00000"))

    rebuild_customer_set_aside(session)
    agg = get_customer_set_aside_by_article(session)
    assert len(agg) == 1
    assert agg[0].article_code == "ART001"
    assert agg[0].total_set_aside_qty == Decimal("15.00000")
    assert agg[0].set_aside_count == 2


def test_aggregazione_articoli_diversi_separati(session):
    """Articoli diversi vengono aggregati separatamente."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 set_aside_qty=Decimal("10.00000"))
    _insert_riga(session, "ORD001", 2, article_code="ART002",
                 set_aside_qty=Decimal("7.00000"))

    rebuild_customer_set_aside(session)
    agg = get_customer_set_aside_by_article(session)
    assert len(agg) == 2
    codes = {a.article_code for a in agg}
    assert codes == {"ART001", "ART002"}


def test_get_customer_set_aside_by_article_singolo(session):
    """get_customer_set_aside_by_article filtra per singolo articolo."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 set_aside_qty=Decimal("10.00000"))
    _insert_riga(session, "ORD001", 2, article_code="ART002",
                 set_aside_qty=Decimal("7.00000"))

    rebuild_customer_set_aside(session)
    agg = get_customer_set_aside_by_article(session, article_code="ART001")
    assert len(agg) == 1
    assert agg[0].article_code == "ART001"
    assert agg[0].total_set_aside_qty == Decimal("10.00000")


def test_get_customer_set_aside_by_article_inesistente(session):
    agg = get_customer_set_aside_by_article(session, article_code="ARTXXX")
    assert agg == []


# ─── Filtro source_type ──────────────────────────────────────────────────────

def test_list_customer_set_aside_filtro_source_type(session):
    _insert_riga(session, "ORD001", 1, set_aside_qty=Decimal("5.00000"))
    rebuild_customer_set_aside(session)

    items = list_customer_set_aside(session, source_type="customer_order")
    assert len(items) == 1

    items_other = list_customer_set_aside(session, source_type="production")
    assert items_other == []


# ─── Determinismo del rebuild ─────────────────────────────────────────────────

def test_rebuild_deterministico(session):
    """Lo stesso input produce lo stesso output."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 set_aside_qty=Decimal("12.00000"))

    rebuild_customer_set_aside(session)
    n1 = session.query(CoreCustomerSetAside).count()
    c1 = session.query(CoreCustomerSetAside).one().set_aside_qty

    rebuild_customer_set_aside(session)
    n2 = session.query(CoreCustomerSetAside).count()
    c2 = session.query(CoreCustomerSetAside).one().set_aside_qty

    assert n1 == n2
    assert c1 == c2


def test_rebuild_ricalcola_dopo_aggiornamento(session):
    """Dopo un aggiornamento al mirror, il rebuild ricalcola correttamente."""
    riga = _insert_riga(session, "ORD001", 1, article_code="ART001",
                        set_aside_qty=Decimal("20.00000"))
    rebuild_customer_set_aside(session)
    assert list_customer_set_aside(session)[0].set_aside_qty == Decimal("20.00000")

    riga.set_aside_qty = Decimal("8.00000")
    session.flush()

    rebuild_customer_set_aside(session)
    assert list_customer_set_aside(session)[0].set_aside_qty == Decimal("8.00000")


def test_rebuild_rimuove_record_di_righe_azzerate(session):
    """Il rebuild rimuove i record di righe nel frattempo azzerate."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 set_aside_qty=Decimal("10.00000"))
    rebuild_customer_set_aside(session)
    assert session.query(CoreCustomerSetAside).count() == 1

    riga = session.query(SyncRigaOrdineCliente).one()
    riga.set_aside_qty = Decimal("0.00000")
    session.flush()

    rebuild_customer_set_aside(session)
    assert session.query(CoreCustomerSetAside).count() == 0


# ─── Mirror vuoto ─────────────────────────────────────────────────────────────

def test_mirror_vuoto_zero_record(session):
    n = rebuild_customer_set_aside(session)
    assert n == 0
    assert list_customer_set_aside(session) == []
    assert get_customer_set_aside_by_article(session) == []


# ─── Separazione da commitments ───────────────────────────────────────────────

def test_separazione_da_commitments(session):
    """customer_set_aside e commitments sono fact distinti e indipendenti."""
    from nssp_v2.core.commitments.queries import rebuild_commitments, list_commitments

    # Una riga con set_aside_qty=10 e open_qty=90 (100-10-0)
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("0.00000"),
                 set_aside_qty=Decimal("10.00000"))

    rebuild_customer_set_aside(session)
    rebuild_commitments(session)

    set_aside_items = list_customer_set_aside(session)
    commitment_items = list_commitments(session, source_type="customer_order")

    assert len(set_aside_items) == 1
    assert len(commitment_items) == 1

    # set_aside_qty = 10 (DOC_QTAP)
    assert set_aside_items[0].set_aside_qty == Decimal("10.00000")
    # committed_qty = open_qty = 100 - 10 - 0 = 90
    assert commitment_items[0].committed_qty == Decimal("90.00000")
