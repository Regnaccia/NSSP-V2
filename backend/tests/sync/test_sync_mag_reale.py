"""
Test di integrazione per la sync unit `mag_reale` (TASK-V2-036).

Verificano:
- mapping da record sorgente a target interno
- normalizzazione codice_articolo (strip + uppercase)
- idempotenza del bootstrap
- sync incrementale (cursor)
- assenza di delete handling
- aggiornamento run metadata e freshness anchor
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.mag_reale.source import FakeMagRealeSource, MagRealeRecord
from nssp_v2.sync.mag_reale.unit import MagRealeSyncUnit
from nssp_v2.sync.models import SyncEntityState, SyncRunLog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 8, 10, 0, 0)


def _record(id_movimento: int, **kwargs) -> MagRealeRecord:
    defaults = dict(
        codice_articolo="ART001",
        quantita_caricata=Decimal("10.000000"),
        quantita_scaricata=None,
        causale_movimento_codice="ENT",
        data_movimento=_NOW,
    )
    defaults.update(kwargs)
    return MagRealeRecord(id_movimento=id_movimento, **defaults)


# ─── Mapping ──────────────────────────────────────────────────────────────────

def test_inserisce_record(session):
    source = FakeMagRealeSource([_record(1001)])
    unit = MagRealeSyncUnit()
    meta = unit.run(session, source)

    assert meta.status == "success"
    assert meta.rows_seen == 1
    assert meta.rows_written == 1

    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj.codice_articolo == "ART001"
    assert obj.quantita_caricata == Decimal("10.000000")
    assert obj.quantita_scaricata is None
    assert obj.causale_movimento_codice == "ENT"
    assert obj.data_movimento == _NOW


def test_mapping_tutti_i_campi(session):
    rec = _record(
        9999,
        codice_articolo="  art999  ",  # sara normalizzato
        quantita_caricata=Decimal("5.500000"),
        quantita_scaricata=Decimal("2.000000"),
        causale_movimento_codice="USC",
        data_movimento=datetime(2026, 1, 15, 8, 30),
    )
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))

    obj = session.query(SyncMagReale).filter_by(id_movimento=9999).one()
    assert obj.codice_articolo == "ART999"  # normalizzato
    assert obj.quantita_caricata == Decimal("5.500000")
    assert obj.quantita_scaricata == Decimal("2.000000")
    assert obj.causale_movimento_codice == "USC"
    assert obj.data_movimento == datetime(2026, 1, 15, 8, 30)


def test_campi_nullable_none(session):
    rec = _record(
        2000,
        codice_articolo=None,
        quantita_caricata=None,
        quantita_scaricata=None,
        causale_movimento_codice=None,
        data_movimento=None,
    )
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))

    obj = session.query(SyncMagReale).filter_by(id_movimento=2000).one()
    assert obj.codice_articolo is None
    assert obj.quantita_caricata is None
    assert obj.quantita_scaricata is None
    assert obj.causale_movimento_codice is None
    assert obj.data_movimento is None


# ─── Normalizzazione codice_articolo ──────────────────────────────────────────

def test_normalizzazione_uppercase(session):
    """codice_articolo viene convertito in maiuscolo."""
    rec = _record(1001, codice_articolo="art001")
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))
    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj.codice_articolo == "ART001"


def test_normalizzazione_trim(session):
    """codice_articolo viene trimmato."""
    rec = _record(1001, codice_articolo="  ART001  ")
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))
    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj.codice_articolo == "ART001"


def test_normalizzazione_trim_e_uppercase_combinati(session):
    """codice_articolo: trim + uppercase combinati."""
    rec = _record(1001, codice_articolo="  art Mix  ")
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))
    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj.codice_articolo == "ART MIX"


def test_normalizzazione_stringa_vuota_diventa_none(session):
    """Una stringa solo spazi diventa None dopo normalizzazione."""
    rec = _record(1001, codice_articolo="   ")
    MagRealeSyncUnit().run(session, FakeMagRealeSource([rec]))
    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj.codice_articolo is None


# ─── Bootstrap iniziale ────────────────────────────────────────────────────────

def test_bootstrap_completo(session):
    """Senza record nel mirror, il bootstrap scarica tutto (cursor=0)."""
    records = [_record(1000 + i) for i in range(1, 6)]
    meta = MagRealeSyncUnit().run(session, FakeMagRealeSource(records))

    assert meta.rows_seen == 5
    assert meta.rows_written == 5
    assert session.query(SyncMagReale).count() == 5


def test_bootstrap_idempotente(session):
    """Eseguire il bootstrap due volte non duplica i record."""
    records = [_record(1001), _record(1002)]
    unit = MagRealeSyncUnit()
    unit.run(session, FakeMagRealeSource(records))
    meta2 = unit.run(session, FakeMagRealeSource(records))

    assert session.query(SyncMagReale).count() == 2
    assert meta2.rows_written == 0  # nessun nuovo record
    assert meta2.rows_seen == 0     # cursor > tutti gli id, fetch_since non ritorna nulla


# ─── Sync incrementale (cursor) ───────────────────────────────────────────────

def test_incrementale_aggiunge_solo_nuovi(session):
    """Dopo il bootstrap, la sync successiva aggiunge solo i movimenti nuovi."""
    unit = MagRealeSyncUnit()

    # Bootstrap: movimenti 1001, 1002
    unit.run(session, FakeMagRealeSource([_record(1001), _record(1002)]))
    assert session.query(SyncMagReale).count() == 2

    # Incrementale: aggiunge 1003, 1004
    all_records = [_record(1001), _record(1002), _record(1003), _record(1004)]
    meta = unit.run(session, FakeMagRealeSource(all_records))

    assert session.query(SyncMagReale).count() == 4
    assert meta.rows_seen == 2   # solo i nuovi (cursor=1002, fetch 1003 e 1004)
    assert meta.rows_written == 2


def test_incrementale_cursor_corretto(session):
    """Il cursor e il massimo id_movimento gia presente."""
    unit = MagRealeSyncUnit()
    unit.run(session, FakeMagRealeSource([_record(100), _record(200), _record(150)]))

    # Cursor sara 200; il prossimo fetch deve restituire solo id > 200
    all_records = [_record(100), _record(150), _record(200), _record(300)]
    meta = unit.run(session, FakeMagRealeSource(all_records))

    assert meta.rows_seen == 1
    assert meta.rows_written == 1
    obj = session.query(SyncMagReale).filter_by(id_movimento=300).one()
    assert obj.id_movimento == 300


def test_incrementale_senza_nuovi_zero_written(session):
    """Se non ci sono movimenti nuovi, rows_written e rows_seen sono 0."""
    unit = MagRealeSyncUnit()
    unit.run(session, FakeMagRealeSource([_record(1001)]))
    meta = unit.run(session, FakeMagRealeSource([_record(1001)]))

    assert meta.rows_seen == 0
    assert meta.rows_written == 0


# ─── No delete handling ───────────────────────────────────────────────────────

def test_record_esistente_non_eliminato(session):
    """Con no_delete_handling, i record non piu in sorgente rimangono nel mirror."""
    unit = MagRealeSyncUnit()
    unit.run(session, FakeMagRealeSource([_record(1001), _record(1002)]))

    # La sorgente ora non contiene piu 1001 — non deve essere eliminato
    meta = unit.run(session, FakeMagRealeSource([_record(1003)]))

    assert session.query(SyncMagReale).count() == 3
    assert meta.rows_deleted == 0
    obj = session.query(SyncMagReale).filter_by(id_movimento=1001).one()
    assert obj is not None  # ancora presente


# ─── Run metadata e freshness ─────────────────────────────────────────────────

def test_run_log_creato(session):
    MagRealeSyncUnit().run(session, FakeMagRealeSource([_record(1001)]))
    log = session.query(SyncRunLog).filter_by(entity_code="mag_reale").one()
    assert log.status == "success"
    assert log.rows_seen == 1


def test_freshness_anchor_aggiornato(session):
    MagRealeSyncUnit().run(session, FakeMagRealeSource([_record(1001)]))
    state = session.get(SyncEntityState, "mag_reale")
    assert state is not None
    assert state.last_status == "success"
    assert state.last_success_at is not None


def test_run_log_multipli(session):
    unit = MagRealeSyncUnit()
    unit.run(session, FakeMagRealeSource([_record(1001)]))
    unit.run(session, FakeMagRealeSource([_record(1002)]))
    assert session.query(SyncRunLog).filter_by(entity_code="mag_reale").count() == 2
