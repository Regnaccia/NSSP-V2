"""
Test di esecuzione della sync unit `clienti` con SQLite in-memory.

Non richiedono PostgreSQL o Easy online.
Verificano:
- upsert/allineamento corretto
- idempotenza (doppia esecuzione = stesso stato)
- run metadata persistiti
- freshness anchor aggiornato
- mark_inactive per clienti non piu in sorgente
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.clienti.models import SyncCliente
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.clienti.source import ClienteRecord, FakeClienteSource
from nssp_v2.sync.clienti.unit import ClienteSyncUnit


@pytest.fixture()
def session():
    """Sessione SQLite in-memory con schema fresco per ogni test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def make_source(*records: tuple[str, str]) -> FakeClienteSource:
    return FakeClienteSource([
        ClienteRecord(codice_cli=cod, ragione_sociale=rag)
        for cod, rag in records
    ])


# ─── Upsert e allineamento ────────────────────────────────────────────────────

def test_run_inserts_new_records(session):
    source = make_source(("C001", "Alfa Srl"), ("C002", "Beta Spa"))
    unit = ClienteSyncUnit()
    meta = unit.run(session, source)

    rows = session.query(SyncCliente).order_by(SyncCliente.codice_cli).all()
    assert len(rows) == 2
    assert rows[0].codice_cli == "C001"
    assert rows[0].ragione_sociale == "Alfa Srl"
    assert rows[0].attivo is True
    assert meta.rows_written == 2
    assert meta.rows_seen == 2


def test_run_updates_existing_record(session):
    source1 = make_source(("C001", "Alfa Srl Vecchia"))
    source2 = make_source(("C001", "Alfa Srl Nuova"))
    unit = ClienteSyncUnit()
    unit.run(session, source1)
    unit.run(session, source2)

    row = session.query(SyncCliente).filter_by(codice_cli="C001").one()
    assert row.ragione_sociale == "Alfa Srl Nuova"
    assert session.query(SyncCliente).count() == 1


# ─── Idempotenza ─────────────────────────────────────────────────────────────

def test_double_run_is_idempotent(session):
    """Due esecuzioni con la stessa sorgente non producono duplicazioni."""
    source = make_source(("C001", "Alfa Srl"), ("C002", "Beta Spa"))
    unit = ClienteSyncUnit()
    unit.run(session, source)
    unit.run(session, source)

    count = session.query(SyncCliente).count()
    assert count == 2


def test_triple_run_same_source_same_state(session):
    source = make_source(("C001", "Alfa Srl"))
    unit = ClienteSyncUnit()
    for _ in range(3):
        unit.run(session, source)
    assert session.query(SyncCliente).count() == 1
    assert session.query(SyncCliente).one().ragione_sociale == "Alfa Srl"


# ─── Delete handling: mark_inactive ──────────────────────────────────────────

def test_missing_in_source_marks_inactive(session):
    source1 = make_source(("C001", "Alfa Srl"), ("C002", "Beta Spa"))
    source2 = make_source(("C001", "Alfa Srl"))   # C002 sparisce
    unit = ClienteSyncUnit()
    unit.run(session, source1)
    meta2 = unit.run(session, source2)

    c001 = session.query(SyncCliente).filter_by(codice_cli="C001").one()
    c002 = session.query(SyncCliente).filter_by(codice_cli="C002").one()
    assert c001.attivo is True
    assert c002.attivo is False
    assert meta2.rows_deleted == 1


def test_reappearing_client_reactivated(session):
    source1 = make_source(("C001", "Alfa Srl"), ("C002", "Beta Spa"))
    source2 = make_source(("C001", "Alfa Srl"))   # C002 sparisce
    source3 = make_source(("C001", "Alfa Srl"), ("C002", "Beta Spa"))  # C002 riappare
    unit = ClienteSyncUnit()
    unit.run(session, source1)
    unit.run(session, source2)
    unit.run(session, source3)

    c002 = session.query(SyncCliente).filter_by(codice_cli="C002").one()
    assert c002.attivo is True


# ─── Run metadata ─────────────────────────────────────────────────────────────

def test_run_metadata_persisted(session):
    source = make_source(("C001", "Alfa Srl"))
    unit = ClienteSyncUnit()
    meta = unit.run(session, source)

    log = session.get(SyncRunLog, meta.run_id)
    assert log is not None
    assert log.entity_code == "clienti"
    assert log.status == "success"
    assert log.rows_seen == 1
    assert log.rows_written == 1
    assert log.finished_at is not None


def test_each_run_produces_distinct_log(session):
    source = make_source(("C001", "Alfa Srl"))
    unit = ClienteSyncUnit()
    meta1 = unit.run(session, source)
    meta2 = unit.run(session, source)

    assert meta1.run_id != meta2.run_id
    assert session.query(SyncRunLog).count() == 2


# ─── Freshness anchor ─────────────────────────────────────────────────────────

def test_freshness_anchor_set_after_success(session):
    source = make_source(("C001", "Alfa Srl"))
    unit = ClienteSyncUnit()
    unit.run(session, source)

    state = session.get(SyncEntityState, "clienti")
    assert state is not None
    assert state.last_success_at is not None
    assert state.last_status == "success"


def test_freshness_anchor_updated_on_second_run(session):
    source = make_source(("C001", "Alfa Srl"))
    unit = ClienteSyncUnit()
    unit.run(session, source)
    state1_ts = session.get(SyncEntityState, "clienti").last_success_at

    import time
    time.sleep(0.01)   # garantisce timestamp distinto

    unit.run(session, source)
    state2_ts = session.get(SyncEntityState, "clienti").last_success_at

    assert state2_ts >= state1_ts
