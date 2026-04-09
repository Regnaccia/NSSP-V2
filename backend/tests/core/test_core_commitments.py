"""
Test di integrazione per il Core slice `commitments` (TASK-V2-042, DL-ARCH-V2-017).

Verificano:
- committed_qty = open_qty (formula V1)
- righe con open_qty <= 0 non generano commitments
- righe con article_code None non generano commitments
- source_type = "customer_order"
- source_reference = "{order_reference}/{line_reference}"
- aggregazione per article_code (total_committed_qty, commitment_count)
- piu righe dello stesso articolo aggregate correttamente
- articoli diversi aggregati separatamente
- rebuild deterministico: stesso input stesso output
- rebuild ricalcola dopo cambiamento dati
- rebuild rimuove commitments di articoli non piu attivi
- mirror vuoto -> 0 commitments
- get_commitments_by_article per singolo articolo
- list_commitments con filtro source_type
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.core.commitments.queries import (
    rebuild_commitments,
    list_commitments,
    get_commitments_by_article,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


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
        set_aside_qty=Decimal("10.00000"),
        net_unit_price=Decimal("5.50000"),
        continues_previous_line=False,
        synced_at=datetime.now(timezone.utc),
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


# ─── committed_qty = open_qty ─────────────────────────────────────────────────

def test_committed_qty_uguale_a_open_qty(session):
    """committed_qty e esattamente open_qty: max(ordered - set_aside - fulfilled, 0)."""
    # 100 - 10 - 20 = 70
    _insert_riga(session, "ORD001", 1,
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("20.00000"),
                 set_aside_qty=Decimal("10.00000"))

    n = rebuild_commitments(session)
    assert n == 1

    items = list_commitments(session)
    assert items[0].committed_qty == Decimal("70.00000")


def test_source_type_customer_order(session):
    _insert_riga(session, "ORD001", 1)
    rebuild_commitments(session)

    items = list_commitments(session)
    assert items[0].source_type == "customer_order"


def test_source_reference_formato(session):
    """source_reference ha il formato '{order_reference}/{line_reference}'."""
    _insert_riga(session, "ORD001", 3)
    rebuild_commitments(session)

    items = list_commitments(session)
    assert items[0].source_reference == "ORD001/3"


# ─── Righe chiuse escluse ─────────────────────────────────────────────────────

def test_riga_open_qty_zero_non_genera_commitment(session):
    """open_qty = 0: riga evasa completamente, nessun commitment."""
    _insert_riga(session, "ORD001", 1,
                 ordered_qty=Decimal("50.00000"),
                 fulfilled_qty=Decimal("30.00000"),
                 set_aside_qty=Decimal("20.00000"))
    # 50 - 30 - 20 = 0

    n = rebuild_commitments(session)
    assert n == 0
    assert list_commitments(session) == []


def test_riga_open_qty_negativo_non_genera_commitment(session):
    """open_qty < 0 (clampato a 0): nessun commitment."""
    _insert_riga(session, "ORD001", 1,
                 ordered_qty=Decimal("10.00000"),
                 fulfilled_qty=Decimal("8.00000"),
                 set_aside_qty=Decimal("5.00000"))
    # 10 - 8 - 5 = -3 -> 0

    n = rebuild_commitments(session)
    assert n == 0


def test_righe_parzialmente_chiuse_e_aperte(session):
    """Solo le righe con open_qty > 0 generano commitments."""
    _insert_riga(session, "ORD001", 1,
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("50.00000"),
                 set_aside_qty=Decimal("0.00000"))   # open = 50 -> commitment
    _insert_riga(session, "ORD001", 2,
                 ordered_qty=Decimal("30.00000"),
                 fulfilled_qty=Decimal("30.00000"),
                 set_aside_qty=Decimal("0.00000"))   # open = 0 -> no commitment

    n = rebuild_commitments(session)
    assert n == 1
    items = list_commitments(session)
    assert items[0].source_reference == "ORD001/1"


# ─── Righe senza article_code escluse ────────────────────────────────────────

def test_riga_senza_article_code_non_genera_commitment(session):
    """Le righe descrittive (article_code=None) non generano commitments."""
    _insert_riga(session, "ORD001", 1, article_code="ART001")
    _insert_riga(session, "ORD001", 2,
                 article_code=None,
                 continues_previous_line=True,
                 ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    n = rebuild_commitments(session)
    assert n == 1  # solo la riga principale


def test_rebuild_normalizza_article_code_customer_order(session):
    """I commitments cliente usano article_code canonico trim+uppercase."""
    _insert_riga(
        session,
        "ORD001",
        1,
        article_code=" art001 ",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("0.00000"),
        set_aside_qty=Decimal("0.00000"),
    )

    rebuild_commitments(session)

    items = list_commitments(session, source_type="customer_order")
    assert len(items) == 1
    assert items[0].article_code == "ART001"


# ─── Aggregazione per articolo ────────────────────────────────────────────────

def test_aggregazione_per_articolo_piu_righe(session):
    """Piu righe dello stesso articolo sommano il loro open_qty."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("20.00000"),
                 set_aside_qty=Decimal("0.00000"))   # open = 80
    _insert_riga(session, "ORD001", 2, article_code="ART001",
                 ordered_qty=Decimal("50.00000"),
                 fulfilled_qty=Decimal("0.00000"),
                 set_aside_qty=Decimal("10.00000"))  # open = 40

    rebuild_commitments(session)
    agg = get_commitments_by_article(session)
    assert len(agg) == 1
    assert agg[0].article_code == "ART001"
    assert agg[0].total_committed_qty == Decimal("120.00000")  # 80 + 40
    assert agg[0].commitment_count == 2


def test_aggregazione_articoli_diversi_separati(session):
    """Articoli diversi vengono aggregati separatamente."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("0.00000"), set_aside_qty=Decimal("0.00000"))
    _insert_riga(session, "ORD001", 2, article_code="ART002",
                 ordered_qty=Decimal("50.00000"),
                 fulfilled_qty=Decimal("0.00000"), set_aside_qty=Decimal("0.00000"))

    rebuild_commitments(session)
    agg = get_commitments_by_article(session)
    assert len(agg) == 2
    codes = {a.article_code for a in agg}
    assert codes == {"ART001", "ART002"}


def test_get_commitments_by_article_singolo(session):
    """get_commitments_by_article filtra per singolo articolo."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("0.00000"), set_aside_qty=Decimal("0.00000"))
    _insert_riga(session, "ORD001", 2, article_code="ART002",
                 ordered_qty=Decimal("50.00000"),
                 fulfilled_qty=Decimal("0.00000"), set_aside_qty=Decimal("0.00000"))

    rebuild_commitments(session)
    agg = get_commitments_by_article(session, article_code="ART001")
    assert len(agg) == 1
    assert agg[0].article_code == "ART001"
    assert agg[0].total_committed_qty == Decimal("100.00000")


def test_get_commitments_by_article_inesistente(session):
    agg = get_commitments_by_article(session, article_code="ARTXXX")
    assert agg == []


# ─── Determinismo del rebuild ─────────────────────────────────────────────────

def test_rebuild_deterministico(session):
    """Lo stesso input produce lo stesso output."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("10.00000"), set_aside_qty=Decimal("5.00000"))

    rebuild_commitments(session)
    n1 = session.query(CoreCommitment).count()
    c1 = session.query(CoreCommitment).one().committed_qty

    rebuild_commitments(session)
    n2 = session.query(CoreCommitment).count()
    c2 = session.query(CoreCommitment).one().committed_qty

    assert n1 == n2
    assert c1 == c2


def test_rebuild_ricalcola_dopo_aggiornamento(session):
    """Dopo un aggiornamento al mirror, il rebuild ricalcola correttamente."""
    riga = _insert_riga(session, "ORD001", 1, article_code="ART001",
                        ordered_qty=Decimal("100.00000"),
                        fulfilled_qty=Decimal("0.00000"),
                        set_aside_qty=Decimal("0.00000"))
    rebuild_commitments(session)
    assert list_commitments(session)[0].committed_qty == Decimal("100.00000")

    # Simula evasione parziale: aggiorna fulfilled_qty nel mirror
    riga.fulfilled_qty = Decimal("60.00000")
    session.flush()

    rebuild_commitments(session)
    assert list_commitments(session)[0].committed_qty == Decimal("40.00000")


def test_rebuild_rimuove_commitments_di_righe_chiuse(session):
    """Il rebuild rimuove i commitments di righe nel frattempo chiuse."""
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("50.00000"),
                 fulfilled_qty=Decimal("0.00000"),
                 set_aside_qty=Decimal("0.00000"))
    rebuild_commitments(session)
    assert session.query(CoreCommitment).count() == 1

    # Simula chiusura completa
    riga = session.query(SyncRigaOrdineCliente).one()
    riga.fulfilled_qty = Decimal("50.00000")
    session.flush()

    rebuild_commitments(session)
    assert session.query(CoreCommitment).count() == 0


# ─── Mirror vuoto ─────────────────────────────────────────────────────────────

def test_mirror_vuoto_zero_commitments(session):
    n = rebuild_commitments(session)
    assert n == 0
    assert list_commitments(session) == []
    assert get_commitments_by_article(session) == []


# ─── list_commitments con filtro source_type ─────────────────────────────────

def test_list_commitments_filtro_source_type(session):
    _insert_riga(session, "ORD001", 1, article_code="ART001",
                 ordered_qty=Decimal("100.00000"),
                 fulfilled_qty=Decimal("0.00000"), set_aside_qty=Decimal("0.00000"))
    rebuild_commitments(session)

    items = list_commitments(session, source_type="customer_order")
    assert len(items) == 1

    items_other = list_commitments(session, source_type="production")
    assert items_other == []
