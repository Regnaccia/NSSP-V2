"""
Test di esecuzione della sync unit `destinazioni` con SQLite in-memory.

Non richiedono PostgreSQL o Easy online.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.destinazioni.models import SyncDestinazione
from nssp_v2.sync.destinazioni.source import DestinazioneRecord, FakeDestinazioneSource
from nssp_v2.sync.destinazioni.unit import DestinazioneSyncUnit
from nssp_v2.sync.models import SyncEntityState, SyncRunLog


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def make_source(*records: tuple) -> FakeDestinazioneSource:
    return FakeDestinazioneSource([
        DestinazioneRecord(codice_destinazione=cod, codice_cli=cli)
        for cod, cli in records
    ])


# ─── Upsert e allineamento ────────────────────────────────────────────────────

def test_run_inserts_new_records(session):
    source = make_source(("D001", "C001"), ("D002", "C002"))
    unit = DestinazioneSyncUnit()
    meta = unit.run(session, source)

    rows = session.query(SyncDestinazione).order_by(SyncDestinazione.codice_destinazione).all()
    assert len(rows) == 2
    assert rows[0].codice_destinazione == "D001"
    assert rows[0].codice_cli == "C001"
    assert meta.rows_written == 2
    assert meta.rows_seen == 2


def test_run_updates_existing_record(session):
    rec1 = DestinazioneRecord(codice_destinazione="D001", citta="Milano")
    rec2 = DestinazioneRecord(codice_destinazione="D001", citta="Roma")
    unit = DestinazioneSyncUnit()
    unit.run(session, FakeDestinazioneSource([rec1]))
    unit.run(session, FakeDestinazioneSource([rec2]))

    row = session.query(SyncDestinazione).filter_by(codice_destinazione="D001").one()
    assert row.citta == "Roma"
    assert session.query(SyncDestinazione).count() == 1


# ─── Idempotenza ─────────────────────────────────────────────────────────────

def test_double_run_is_idempotent(session):
    source = make_source(("D001", "C001"), ("D002", "C001"))
    unit = DestinazioneSyncUnit()
    unit.run(session, source)
    unit.run(session, source)
    assert session.query(SyncDestinazione).count() == 2


def test_triple_run_same_source_same_state(session):
    source = make_source(("D001", "C001"))
    unit = DestinazioneSyncUnit()
    for _ in range(3):
        unit.run(session, source)
    assert session.query(SyncDestinazione).count() == 1


# ─── Delete handling: mark_inactive ──────────────────────────────────────────

def test_missing_in_source_marks_inactive(session):
    source1 = make_source(("D001", "C001"), ("D002", "C001"))
    source2 = make_source(("D001", "C001"))
    unit = DestinazioneSyncUnit()
    unit.run(session, source1)
    meta2 = unit.run(session, source2)

    d001 = session.query(SyncDestinazione).filter_by(codice_destinazione="D001").one()
    d002 = session.query(SyncDestinazione).filter_by(codice_destinazione="D002").one()
    assert d001.attivo is True
    assert d002.attivo is False
    assert meta2.rows_deleted == 1


def test_reappearing_destinazione_reactivated(session):
    source1 = make_source(("D001", "C001"), ("D002", "C001"))
    source2 = make_source(("D001", "C001"))
    source3 = make_source(("D001", "C001"), ("D002", "C001"))
    unit = DestinazioneSyncUnit()
    unit.run(session, source1)
    unit.run(session, source2)
    unit.run(session, source3)

    d002 = session.query(SyncDestinazione).filter_by(codice_destinazione="D002").one()
    assert d002.attivo is True


# ─── Run metadata ─────────────────────────────────────────────────────────────

def test_run_metadata_persisted(session):
    source = make_source(("D001", "C001"))
    unit = DestinazioneSyncUnit()
    meta = unit.run(session, source)

    log = session.get(SyncRunLog, meta.run_id)
    assert log is not None
    assert log.entity_code == "destinazioni"
    assert log.status == "success"
    assert log.rows_written == 1


def test_each_run_produces_distinct_log(session):
    source = make_source(("D001", "C001"))
    unit = DestinazioneSyncUnit()
    meta1 = unit.run(session, source)
    meta2 = unit.run(session, source)
    assert meta1.run_id != meta2.run_id
    assert session.query(SyncRunLog).filter_by(entity_code="destinazioni").count() == 2


# ─── Freshness anchor ─────────────────────────────────────────────────────────

def test_freshness_anchor_set_after_success(session):
    source = make_source(("D001", "C001"))
    unit = DestinazioneSyncUnit()
    unit.run(session, source)

    state = session.get(SyncEntityState, "destinazioni")
    assert state is not None
    assert state.last_success_at is not None
    assert state.last_status == "success"


# ─── Campi opzionali ─────────────────────────────────────────────────────────

def test_optional_fields_persisted(session):
    rec = DestinazioneRecord(
        codice_destinazione="D001",
        codice_cli="C001",
        numero_progressivo_cliente="001",
        indirizzo="Via Roma 1",
        nazione_codice="IT",
        citta="Milano",
        provincia="MI",
        telefono_1="02 123456",
    )
    unit = DestinazioneSyncUnit()
    unit.run(session, FakeDestinazioneSource([rec]))

    row = session.query(SyncDestinazione).filter_by(codice_destinazione="D001").one()
    assert row.numero_progressivo_cliente == "001"
    assert row.indirizzo == "Via Roma 1"
    assert row.citta == "Milano"
    assert row.provincia == "MI"
    assert row.telefono_1 == "02 123456"
