"""
Test di integrazione per la sync unit `righe_ordine_cliente` (TASK-V2-040).

Verificano:
- mapping da record sorgente a target interno (tutti i campi)
- source identity (order_reference, line_reference) = (DOC_NUM, NUM_PROGR)
- righe descrittive con continues_previous_line=True salvate come record separati
- upsert: aggiornamento riga gia presente
- idempotenza: stessa sorgente, stesso risultato
- no_delete_handling: righe non piu in sorgente restano nel mirror
- set_aside_qty preservato come dato sorgente distinto
- campi nullable gestiti come None
- aggiornamento run metadata e freshness anchor
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from nssp_v2.sync.righe_ordine_cliente.source import FakeRigheOrdineClienteSource, RigaOrdineClienteRecord
from nssp_v2.sync.righe_ordine_cliente.unit import RigheOrdineClienteSyncUnit
from nssp_v2.sync.models import SyncEntityState, SyncRunLog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_DATE = datetime(2026, 3, 10)
_DELIVERY = datetime(2026, 4, 15)


def _riga(order_ref: str = "ORD001", line_ref: int = 1, **kwargs) -> RigaOrdineClienteRecord:
    defaults = dict(
        order_date=_DATE,
        expected_delivery_date=_DELIVERY,
        customer_code="CLI001",
        destination_code="DEST01",
        customer_destination_progressive=None,
        customer_order_reference="REF-CLIENTE-001",
        article_code="ART001",
        article_description_segment="Descrizione articolo",
        article_measure="150x50x30",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("20.00000"),
        set_aside_qty=Decimal("10.00000"),
        net_unit_price=Decimal("5.50000"),
        continues_previous_line=False,
    )
    defaults.update(kwargs)
    return RigaOrdineClienteRecord(order_reference=order_ref, line_reference=line_ref, **defaults)


def _run(session, records):
    source = FakeRigheOrdineClienteSource(records)
    unit = RigheOrdineClienteSyncUnit()
    return unit.run(session, source)


# ─── Mapping ──────────────────────────────────────────────────────────────────

def test_inserisce_record(session):
    meta = _run(session, [_riga()])

    assert meta.status == "success"
    assert meta.rows_seen == 1
    assert meta.rows_written == 1

    obj = session.query(SyncRigaOrdineCliente).one()
    assert obj.order_reference == "ORD001"
    assert obj.line_reference == 1


def test_mapping_tutti_i_campi(session):
    rec = _riga(
        order_ref="ORD999",
        line_ref=5,
        order_date=_DATE,
        expected_delivery_date=_DELIVERY,
        customer_code="CLI999",
        destination_code="DEST99",
        customer_destination_progressive="001",
        customer_order_reference="REF-EXT-999",
        article_code="ART999",
        article_description_segment="Desc segmento",
        article_measure="200x100",
        ordered_qty=Decimal("50.00000"),
        fulfilled_qty=Decimal("10.00000"),
        set_aside_qty=Decimal("5.00000"),
        net_unit_price=Decimal("12.34500"),
        continues_previous_line=False,
    )
    _run(session, [rec])

    obj = session.query(SyncRigaOrdineCliente).filter_by(
        order_reference="ORD999", line_reference=5
    ).one()
    assert obj.order_reference == "ORD999"
    assert obj.line_reference == 5
    assert obj.order_date == _DATE
    assert obj.expected_delivery_date == _DELIVERY
    assert obj.customer_code == "CLI999"
    assert obj.destination_code == "DEST99"
    assert obj.customer_destination_progressive == "001"
    assert obj.customer_order_reference == "REF-EXT-999"
    assert obj.article_code == "ART999"
    assert obj.article_description_segment == "Desc segmento"
    assert obj.article_measure == "200x100"
    assert obj.ordered_qty == Decimal("50.00000")
    assert obj.fulfilled_qty == Decimal("10.00000")
    assert obj.set_aside_qty == Decimal("5.00000")
    assert obj.net_unit_price == Decimal("12.34500")
    assert obj.continues_previous_line is False


def test_campi_nullable_gestiti_come_none(session):
    rec = RigaOrdineClienteRecord(
        order_reference="ORD100",
        line_reference=1,
    )
    _run(session, [rec])

    obj = session.query(SyncRigaOrdineCliente).one()
    assert obj.order_date is None
    assert obj.expected_delivery_date is None
    assert obj.customer_code is None
    assert obj.destination_code is None
    assert obj.customer_destination_progressive is None
    assert obj.customer_order_reference is None
    assert obj.article_code is None
    assert obj.article_description_segment is None
    assert obj.article_measure is None
    assert obj.ordered_qty is None
    assert obj.fulfilled_qty is None
    assert obj.set_aside_qty is None
    assert obj.net_unit_price is None
    assert obj.continues_previous_line is None


# ─── Source identity ──────────────────────────────────────────────────────────

def test_source_identity_order_e_line(session):
    """Righe diverse dello stesso ordine vengono inserite come record separati."""
    records = [
        _riga("ORD001", 1, article_code="ART001"),
        _riga("ORD001", 2, article_code="ART002"),
        _riga("ORD001", 3, article_code="ART003"),
    ]
    meta = _run(session, records)

    assert meta.rows_written == 3
    count = session.query(SyncRigaOrdineCliente).count()
    assert count == 3


def test_source_identity_ordini_diversi(session):
    """Righe con stesso line_reference ma ordini diversi vengono inserite come record separati."""
    records = [
        _riga("ORD001", 1, article_code="ART001"),
        _riga("ORD002", 1, article_code="ART002"),
    ]
    _run(session, records)

    count = session.query(SyncRigaOrdineCliente).count()
    assert count == 2
    obj1 = session.query(SyncRigaOrdineCliente).filter_by(order_reference="ORD001").one()
    obj2 = session.query(SyncRigaOrdineCliente).filter_by(order_reference="ORD002").one()
    assert obj1.article_code == "ART001"
    assert obj2.article_code == "ART002"


# ─── Righe descrittive (continues_previous_line) ─────────────────────────────

def test_riga_descrittiva_salvata_come_record_separato(session):
    """Una riga con continues_previous_line=True viene salvata come record distinto."""
    records = [
        _riga("ORD001", 1, article_code="ART001", continues_previous_line=False),
        _riga("ORD001", 2, article_code=None, continues_previous_line=True,
              article_description_segment="Riga di continuazione descrittiva"),
    ]
    _run(session, records)

    count = session.query(SyncRigaOrdineCliente).count()
    assert count == 2

    riga_desc = session.query(SyncRigaOrdineCliente).filter_by(line_reference=2).one()
    assert riga_desc.continues_previous_line is True
    assert riga_desc.article_code is None
    assert riga_desc.article_description_segment == "Riga di continuazione descrittiva"


def test_righe_descrittive_non_fuse_nel_mirror(session):
    """Il mirror non fonde le righe descrittive: ogni riga resta separata."""
    records = [
        _riga("ORD001", 1, article_code="ART001", continues_previous_line=False),
        _riga("ORD001", 2, article_code=None, continues_previous_line=True),
        _riga("ORD001", 3, article_code=None, continues_previous_line=True),
    ]
    meta = _run(session, records)
    assert meta.rows_written == 3
    assert session.query(SyncRigaOrdineCliente).count() == 3


# ─── Upsert ───────────────────────────────────────────────────────────────────

def test_upsert_aggiorna_riga_esistente(session):
    """Una seconda sync con dati aggiornati aggiorna la riga gia presente."""
    _run(session, [_riga("ORD001", 1, ordered_qty=Decimal("100.00000"))])

    meta = _run(session, [_riga("ORD001", 1, ordered_qty=Decimal("120.00000"))])

    assert meta.rows_seen == 1
    assert meta.rows_written == 1
    obj = session.query(SyncRigaOrdineCliente).one()
    assert obj.ordered_qty == Decimal("120.00000")


def test_upsert_non_duplica_la_riga(session):
    """Dopo l'upsert, nel mirror c'e esattamente un record per chiave."""
    _run(session, [_riga("ORD001", 1)])
    _run(session, [_riga("ORD001", 1)])

    count = session.query(SyncRigaOrdineCliente).count()
    assert count == 1


def test_upsert_aggiorna_set_aside_qty(session):
    """set_aside_qty viene aggiornato dalla sync senza alterazioni."""
    _run(session, [_riga("ORD001", 1, set_aside_qty=Decimal("5.00000"))])
    _run(session, [_riga("ORD001", 1, set_aside_qty=Decimal("8.00000"))])

    obj = session.query(SyncRigaOrdineCliente).one()
    assert obj.set_aside_qty == Decimal("8.00000")


# ─── Idempotenza ──────────────────────────────────────────────────────────────

def test_idempotenza_stessa_sorgente(session):
    """Piu run con la stessa sorgente producono lo stesso stato nel mirror."""
    records = [_riga("ORD001", 1), _riga("ORD001", 2)]
    _run(session, records)
    _run(session, records)

    assert session.query(SyncRigaOrdineCliente).count() == 2


# ─── No delete handling ───────────────────────────────────────────────────────

def test_no_delete_handling_riga_sparita_dalla_sorgente(session):
    """Una riga non piu presente in sorgente resta nel mirror."""
    _run(session, [_riga("ORD001", 1), _riga("ORD001", 2)])
    # Seconda sync: solo la riga 1
    _run(session, [_riga("ORD001", 1)])

    count = session.query(SyncRigaOrdineCliente).count()
    assert count == 2  # la riga 2 e ancora nel mirror


# ─── set_aside_qty come dato sorgente distinto ───────────────────────────────

def test_set_aside_qty_preservato_senza_business_logic(session):
    """set_aside_qty viene salvato identico alla sorgente, senza calcoli derivati."""
    rec = _riga("ORD001", 1,
                ordered_qty=Decimal("100.00000"),
                fulfilled_qty=Decimal("20.00000"),
                set_aside_qty=Decimal("15.00000"))
    _run(session, [rec])

    obj = session.query(SyncRigaOrdineCliente).one()
    assert obj.set_aside_qty == Decimal("15.00000")
    # Il layer sync non calcola open_qty ne commitments
    assert obj.ordered_qty == Decimal("100.00000")
    assert obj.fulfilled_qty == Decimal("20.00000")


# ─── Run metadata ─────────────────────────────────────────────────────────────

def test_run_log_creato(session):
    _run(session, [_riga()])
    logs = session.query(SyncRunLog).filter_by(entity_code="righe_ordine_cliente").all()
    assert len(logs) == 1
    assert logs[0].status == "success"
    assert logs[0].rows_seen == 1
    assert logs[0].rows_written == 1


def test_freshness_anchor_aggiornato(session):
    _run(session, [_riga()])
    state = session.get(SyncEntityState, "righe_ordine_cliente")
    assert state is not None
    assert state.last_status == "success"
    assert state.last_success_at is not None


def test_sorgente_vuota_zero_righe(session):
    """Mirror vuoto su sorgente vuota: nessuna riga, run di successo."""
    meta = _run(session, [])
    assert meta.status == "success"
    assert meta.rows_seen == 0
    assert meta.rows_written == 0
    assert session.query(SyncRigaOrdineCliente).count() == 0
