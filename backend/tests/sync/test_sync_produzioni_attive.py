"""
Test di integrazione per la sync unit `produzioni_attive` (TASK-V2-028).

Verificano:
- mapping da record sorgente a target interno
- idempotenza dell'upsert
- mark_inactive per record non piu in sorgente
- aggiornamento run metadata e freshness anchor
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva, SyncEntityState, SyncRunLog
from nssp_v2.sync.produzioni_attive.source import FakeProduzioneAttivaSource, ProduzioneAttivaRecord
from nssp_v2.sync.produzioni_attive.unit import ProduzioneAttivaSyncUnit


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def _record(id_dettaglio: int, **kwargs) -> ProduzioneAttivaRecord:
    defaults = dict(
        cliente_ragione_sociale="ACME SRL",
        codice_articolo="ART001",
        descrizione_articolo="Bullone M8",
        descrizione_articolo_2=None,
        numero_riga_documento=1,
        quantita_ordinata=Decimal("100.00000"),
        quantita_prodotta=Decimal("0.00000"),
        materiale_partenza_codice="MAT001",
        materiale_partenza_per_pezzo=Decimal("0.05000"),
        misura_articolo="M8x20",
        numero_documento="ORD001",
        codice_immagine=None,
        riferimento_numero_ordine_cliente="CLI001",
        riferimento_riga_ordine_cliente=Decimal("1"),
        note_articolo=None,
    )
    defaults.update(kwargs)
    return ProduzioneAttivaRecord(id_dettaglio=id_dettaglio, **defaults)


# ─── Mapping ──────────────────────────────────────────────────────────────────

def test_inserisce_record(session):
    source = FakeProduzioneAttivaSource([_record(1001)])
    unit = ProduzioneAttivaSyncUnit()
    meta = unit.run(session, source)

    assert meta.status == "success"
    assert meta.rows_seen == 1
    assert meta.rows_written == 1

    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=1001).one()
    assert obj.cliente_ragione_sociale == "ACME SRL"
    assert obj.codice_articolo == "ART001"
    assert obj.quantita_ordinata == Decimal("100.00000")
    assert obj.attivo is True


def test_mapping_tutti_i_campi(session):
    rec = _record(
        9999,
        cliente_ragione_sociale="Test SRL",
        codice_articolo="ARTX",
        descrizione_articolo="Desc 1",
        descrizione_articolo_2="Desc 2",
        numero_riga_documento=5,
        quantita_ordinata=Decimal("200.00000"),
        quantita_prodotta=Decimal("50.00000"),
        materiale_partenza_codice="MATX",
        materiale_partenza_per_pezzo=Decimal("0.10000"),
        misura_articolo="10x20",
        numero_documento="DOC99",
        codice_immagine="A",
        riferimento_numero_ordine_cliente="ORD99",
        riferimento_riga_ordine_cliente=Decimal("3"),
        note_articolo="nota test",
    )
    ProduzioneAttivaSyncUnit().run(session, FakeProduzioneAttivaSource([rec]))

    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=9999).one()
    assert obj.cliente_ragione_sociale == "Test SRL"
    assert obj.descrizione_articolo_2 == "Desc 2"
    assert obj.quantita_prodotta == Decimal("50.00000")
    assert obj.codice_immagine == "A"
    assert obj.riferimento_riga_ordine_cliente == Decimal("3")
    assert obj.note_articolo == "nota test"


def test_campi_nullable_none(session):
    rec = _record(
        2000,
        cliente_ragione_sociale=None,
        codice_articolo=None,
        descrizione_articolo=None,
        descrizione_articolo_2=None,
        numero_riga_documento=None,
        quantita_ordinata=None,
        quantita_prodotta=None,
        materiale_partenza_codice=None,
        materiale_partenza_per_pezzo=None,
        misura_articolo=None,
        numero_documento=None,
        codice_immagine=None,
        riferimento_numero_ordine_cliente=None,
        riferimento_riga_ordine_cliente=None,
        note_articolo=None,
    )
    ProduzioneAttivaSyncUnit().run(session, FakeProduzioneAttivaSource([rec]))
    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=2000).one()
    assert obj.codice_articolo is None
    assert obj.quantita_ordinata is None


# ─── Idempotenza ──────────────────────────────────────────────────────────────

def test_upsert_idempotente(session):
    source = FakeProduzioneAttivaSource([_record(1001)])
    unit = ProduzioneAttivaSyncUnit()
    unit.run(session, source)
    unit.run(session, source)

    assert session.query(SyncProduzioneAttiva).count() == 1


def test_upsert_aggiorna_campo(session):
    unit = ProduzioneAttivaSyncUnit()
    unit.run(session, FakeProduzioneAttivaSource([_record(1001, quantita_prodotta=Decimal("0.00000"))]))
    unit.run(session, FakeProduzioneAttivaSource([_record(1001, quantita_prodotta=Decimal("50.00000"))]))

    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=1001).one()
    assert obj.quantita_prodotta == Decimal("50.00000")


def test_upsert_piu_record(session):
    records = [_record(i) for i in range(1, 6)]
    ProduzioneAttivaSyncUnit().run(session, FakeProduzioneAttivaSource(records))
    assert session.query(SyncProduzioneAttiva).count() == 5


# ─── Mark inactive ────────────────────────────────────────────────────────────

def test_mark_inactive_record_rimosso(session):
    unit = ProduzioneAttivaSyncUnit()
    unit.run(session, FakeProduzioneAttivaSource([_record(1001), _record(1002)]))
    meta = unit.run(session, FakeProduzioneAttivaSource([_record(1001)]))

    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=1002).one()
    assert obj.attivo is False
    assert meta.rows_deleted == 1


def test_riattiva_record_reinserito(session):
    unit = ProduzioneAttivaSyncUnit()
    unit.run(session, FakeProduzioneAttivaSource([_record(1001)]))
    unit.run(session, FakeProduzioneAttivaSource([]))          # marca inattivo
    unit.run(session, FakeProduzioneAttivaSource([_record(1001)]))  # reinserito

    obj = session.query(SyncProduzioneAttiva).filter_by(id_dettaglio=1001).one()
    assert obj.attivo is True


# ─── Run metadata e freshness ─────────────────────────────────────────────────

def test_run_log_creato(session):
    ProduzioneAttivaSyncUnit().run(session, FakeProduzioneAttivaSource([_record(1001)]))
    log = session.query(SyncRunLog).filter_by(entity_code="produzioni_attive").one()
    assert log.status == "success"
    assert log.rows_seen == 1


def test_freshness_anchor_aggiornato(session):
    ProduzioneAttivaSyncUnit().run(session, FakeProduzioneAttivaSource([_record(1001)]))
    state = session.get(SyncEntityState, "produzioni_attive")
    assert state is not None
    assert state.last_status == "success"
    assert state.last_success_at is not None


def test_run_log_multipli(session):
    unit = ProduzioneAttivaSyncUnit()
    unit.run(session, FakeProduzioneAttivaSource([_record(1001)]))
    unit.run(session, FakeProduzioneAttivaSource([_record(1001)]))
    assert session.query(SyncRunLog).filter_by(entity_code="produzioni_attive").count() == 2
