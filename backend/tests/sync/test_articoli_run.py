"""
Test di esecuzione della sync unit `articoli` con SQLite in-memory.

Non richiedono PostgreSQL o Easy online.
Verificano:
- upsert/allineamento corretto
- idempotenza (doppia esecuzione = stesso stato)
- run metadata persistiti
- freshness anchor aggiornato
- mark_inactive per articoli non piu in sorgente
- campi numerici e nullable
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.sync.models import SyncEntityState, SyncRunLog
from nssp_v2.sync.articoli.source import ArticoloRecord, FakeArticoloSource
from nssp_v2.sync.articoli.unit import ArticoloSyncUnit


@pytest.fixture()
def session():
    """Sessione SQLite in-memory con schema fresco per ogni test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def make_source(*codici: str) -> FakeArticoloSource:
    return FakeArticoloSource([
        ArticoloRecord(codice_articolo=cod, descrizione_1=f"Desc {cod}")
        for cod in codici
    ])


# ─── Upsert e allineamento ────────────────────────────────────────────────────

def test_run_inserts_new_records(session):
    source = make_source("ART001", "ART002")
    unit = ArticoloSyncUnit()
    meta = unit.run(session, source)

    rows = session.query(SyncArticolo).order_by(SyncArticolo.codice_articolo).all()
    assert len(rows) == 2
    assert rows[0].codice_articolo == "ART001"
    assert rows[0].descrizione_1 == "Desc ART001"
    assert rows[0].attivo is True
    assert meta.rows_written == 2
    assert meta.rows_seen == 2


def test_run_updates_existing_record(session):
    source1 = FakeArticoloSource([ArticoloRecord(codice_articolo="ART001", descrizione_1="Vecchia")])
    source2 = FakeArticoloSource([ArticoloRecord(codice_articolo="ART001", descrizione_1="Nuova")])
    unit = ArticoloSyncUnit()
    unit.run(session, source1)
    unit.run(session, source2)

    row = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert row.descrizione_1 == "Nuova"
    assert session.query(SyncArticolo).count() == 1


# ─── Idempotenza ─────────────────────────────────────────────────────────────

def test_double_run_is_idempotent(session):
    """Due esecuzioni con la stessa sorgente non producono duplicazioni."""
    source = make_source("ART001", "ART002")
    unit = ArticoloSyncUnit()
    unit.run(session, source)
    unit.run(session, source)

    assert session.query(SyncArticolo).count() == 2


def test_triple_run_same_source_same_state(session):
    source = make_source("ART001")
    unit = ArticoloSyncUnit()
    for _ in range(3):
        unit.run(session, source)
    assert session.query(SyncArticolo).count() == 1
    assert session.query(SyncArticolo).one().descrizione_1 == "Desc ART001"


# ─── Delete handling: mark_inactive ──────────────────────────────────────────

def test_missing_in_source_marks_inactive(session):
    source1 = make_source("ART001", "ART002")
    source2 = make_source("ART001")   # ART002 sparisce
    unit = ArticoloSyncUnit()
    unit.run(session, source1)
    meta2 = unit.run(session, source2)

    art001 = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    art002 = session.query(SyncArticolo).filter_by(codice_articolo="ART002").one()
    assert art001.attivo is True
    assert art002.attivo is False
    assert meta2.rows_deleted == 1


def test_reappearing_articolo_reactivated(session):
    source1 = make_source("ART001", "ART002")
    source2 = make_source("ART001")
    source3 = make_source("ART001", "ART002")  # ART002 riappare
    unit = ArticoloSyncUnit()
    unit.run(session, source1)
    unit.run(session, source2)
    unit.run(session, source3)

    art002 = session.query(SyncArticolo).filter_by(codice_articolo="ART002").one()
    assert art002.attivo is True


# ─── Run metadata ─────────────────────────────────────────────────────────────

def test_run_metadata_persisted(session):
    source = make_source("ART001")
    unit = ArticoloSyncUnit()
    meta = unit.run(session, source)

    log = session.get(SyncRunLog, meta.run_id)
    assert log is not None
    assert log.entity_code == "articoli"
    assert log.status == "success"
    assert log.rows_seen == 1
    assert log.rows_written == 1
    assert log.finished_at is not None


def test_each_run_produces_distinct_log(session):
    source = make_source("ART001")
    unit = ArticoloSyncUnit()
    meta1 = unit.run(session, source)
    meta2 = unit.run(session, source)

    assert meta1.run_id != meta2.run_id
    assert session.query(SyncRunLog).count() == 2


# ─── Freshness anchor ─────────────────────────────────────────────────────────

def test_freshness_anchor_set_after_success(session):
    source = make_source("ART001")
    unit = ArticoloSyncUnit()
    unit.run(session, source)

    state = session.get(SyncEntityState, "articoli")
    assert state is not None
    assert state.last_success_at is not None
    assert state.last_status == "success"


def test_freshness_anchor_updated_on_second_run(session):
    source = make_source("ART001")
    unit = ArticoloSyncUnit()
    unit.run(session, source)
    state1_ts = session.get(SyncEntityState, "articoli").last_success_at

    import time
    time.sleep(0.01)

    unit.run(session, source)
    state2_ts = session.get(SyncEntityState, "articoli").last_success_at

    assert state2_ts >= state1_ts


# ─── Campi numerici e nullable ────────────────────────────────────────────────

def test_upsert_persists_all_optional_fields(session):
    from datetime import datetime
    ts = datetime(2026, 1, 15, 10, 0, 0)
    records = [ArticoloRecord(
        codice_articolo="ART001",
        descrizione_1="Desc 1",
        descrizione_2="Desc 2",
        unita_misura_codice="PZ",
        source_modified_at=ts,
        categoria_articolo_1="CAT01",
        materiale_grezzo_codice="MAT01",
        quantita_materiale_grezzo_occorrente=Decimal("1.50000"),
        quantita_materiale_grezzo_scarto=Decimal("0.10000"),
        misura_articolo="100x200",
        codice_immagine="IMG",
        contenitori_magazzino="BIN-A1",
        peso_grammi=Decimal("250.00000"),
    )]
    source = FakeArticoloSource(records)
    unit = ArticoloSyncUnit()
    unit.run(session, source)

    row = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert row.descrizione_1 == "Desc 1"
    assert row.descrizione_2 == "Desc 2"
    assert row.unita_misura_codice == "PZ"
    assert row.source_modified_at == ts
    assert row.categoria_articolo_1 == "CAT01"
    assert row.materiale_grezzo_codice == "MAT01"
    assert row.quantita_materiale_grezzo_occorrente == Decimal("1.50000")
    assert row.quantita_materiale_grezzo_scarto == Decimal("0.10000")
    assert row.misura_articolo == "100x200"
    assert row.codice_immagine == "IMG"
    assert row.contenitori_magazzino == "BIN-A1"
    assert row.peso_grammi == Decimal("250.00000")


def test_upsert_updates_optional_fields_on_second_run(session):
    rec1 = ArticoloRecord(codice_articolo="ART001", unita_misura_codice="PZ", peso_grammi=Decimal("100.00000"))
    rec2 = ArticoloRecord(codice_articolo="ART001", unita_misura_codice="KG", peso_grammi=Decimal("200.00000"))
    unit = ArticoloSyncUnit()
    unit.run(session, FakeArticoloSource([rec1]))
    unit.run(session, FakeArticoloSource([rec2]))

    row = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert row.unita_misura_codice == "KG"
    assert row.peso_grammi == Decimal("200.00000")
    assert session.query(SyncArticolo).count() == 1


def test_upsert_nullable_fields_can_become_none(session):
    rec1 = ArticoloRecord(codice_articolo="ART001", categoria_articolo_1="CAT01")
    rec2 = ArticoloRecord(codice_articolo="ART001", categoria_articolo_1=None)
    unit = ArticoloSyncUnit()
    unit.run(session, FakeArticoloSource([rec1]))
    unit.run(session, FakeArticoloSource([rec2]))

    row = session.query(SyncArticolo).filter_by(codice_articolo="ART001").one()
    assert row.categoria_articolo_1 is None


def test_run_empty_source(session):
    """Sync con sorgente vuota: nessun record inserito, status success."""
    source = FakeArticoloSource([])
    unit = ArticoloSyncUnit()
    meta = unit.run(session, source)

    assert meta.status == "success"
    assert meta.rows_seen == 0
    assert meta.rows_written == 0
    assert session.query(SyncArticolo).count() == 0
