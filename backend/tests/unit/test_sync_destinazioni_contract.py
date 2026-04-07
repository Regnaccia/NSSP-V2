"""
Test unit per la sync unit `destinazioni` — contratto, source adapter, modelli.

Non richiedono DB attivo.
"""

import inspect

from nssp_v2.sync.destinazioni.source import (
    DestinazioneRecord,
    DestinazioneSourceAdapter,
    EasyDestinazioneSource,
    FakeDestinazioneSource,
)
from nssp_v2.sync.destinazioni.unit import DestinazioneSyncUnit
from nssp_v2.sync.contract import (
    ALIGNMENT_STRATEGIES,
    CHANGE_ACQUISITION_STRATEGIES,
    DELETE_HANDLING_POLICIES,
)


# ─── Contratto sync unit (DL-ARCH-V2-009) ────────────────────────────────────

def test_entity_code_declared():
    assert DestinazioneSyncUnit.ENTITY_CODE == "destinazioni"


def test_source_identity_key_declared():
    assert DestinazioneSyncUnit.SOURCE_IDENTITY_KEY == "codice_destinazione"


def test_alignment_strategy_declared_and_valid():
    assert DestinazioneSyncUnit.ALIGNMENT_STRATEGY in ALIGNMENT_STRATEGIES


def test_change_acquisition_declared_and_valid():
    assert DestinazioneSyncUnit.CHANGE_ACQUISITION in CHANGE_ACQUISITION_STRATEGIES


def test_delete_handling_declared_and_valid():
    assert DestinazioneSyncUnit.DELETE_HANDLING in DELETE_HANDLING_POLICIES


def test_dependencies_declared():
    assert isinstance(DestinazioneSyncUnit.DEPENDENCIES, list)


def test_destinazioni_depends_on_clienti():
    """destinazioni dichiara dipendenza esplicita da clienti (DL-ARCH-V2-009 §8)."""
    assert "clienti" in DestinazioneSyncUnit.DEPENDENCIES


# ─── Source adapter read-only (DL-ARCH-V2-007 §2) ────────────────────────────

def test_source_adapter_has_no_write_methods():
    write_keywords = ("write", "insert", "update", "delete", "save", "create", "push", "send")
    methods = [
        name for name, _ in inspect.getmembers(DestinazioneSourceAdapter, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    for method in methods:
        for kw in write_keywords:
            assert kw not in method.lower()


def test_fake_source_returns_records():
    records = [
        DestinazioneRecord(codice_destinazione="D001", codice_cli="C001"),
        DestinazioneRecord(codice_destinazione="D002", codice_cli="C001"),
    ]
    source = FakeDestinazioneSource(records)
    result = source.fetch_all()
    assert len(result) == 2
    assert result[0].codice_destinazione == "D001"


def test_fake_source_is_non_destructive():
    records = [DestinazioneRecord(codice_destinazione="D001")]
    source = FakeDestinazioneSource(records)
    assert source.fetch_all() == source.fetch_all()


def test_fake_source_empty():
    assert FakeDestinazioneSource([]).fetch_all() == []


# ─── DestinazioneRecord campi ─────────────────────────────────────────────────

def test_destinazione_record_required_field():
    rec = DestinazioneRecord(codice_destinazione="D001")
    assert rec.codice_destinazione == "D001"


def test_destinazione_record_optional_fields_default_none():
    rec = DestinazioneRecord(codice_destinazione="D001")
    assert rec.codice_cli is None
    assert rec.numero_progressivo_cliente is None
    assert rec.indirizzo is None
    assert rec.nazione_codice is None
    assert rec.citta is None
    assert rec.provincia is None
    assert rec.telefono_1 is None


# ─── EasyDestinazioneSource contratto ────────────────────────────────────────

def test_easy_source_is_subclass_of_adapter():
    assert issubclass(EasyDestinazioneSource, DestinazioneSourceAdapter)


def test_easy_source_has_no_write_methods():
    write_keywords = ("write", "insert", "update", "delete", "save", "create", "push", "send")
    methods = [
        name for name, _ in inspect.getmembers(EasyDestinazioneSource, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    for method in methods:
        for kw in write_keywords:
            assert kw not in method.lower()


def test_easy_source_query_is_select_only():
    query = EasyDestinazioneSource._QUERY.strip().upper()
    assert query.startswith("SELECT")
    for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"):
        assert keyword not in query


# ─── Modello SQLAlchemy — struttura tabella (no DB) ──────────────────────────

def test_sync_destinazione_tablename():
    from nssp_v2.sync.destinazioni.models import SyncDestinazione
    assert SyncDestinazione.__tablename__ == "sync_destinazioni"


def test_sync_destinazione_has_required_columns():
    from nssp_v2.sync.destinazioni.models import SyncDestinazione
    cols = {c.name for c in SyncDestinazione.__table__.columns}
    assert {
        "id", "codice_destinazione", "codice_cli", "numero_progressivo_cliente",
        "indirizzo", "nazione_codice", "citta", "provincia", "telefono_1",
        "attivo", "synced_at",
    } <= cols


def test_sync_destinazione_codice_destinazione_is_unique():
    from nssp_v2.sync.destinazioni.models import SyncDestinazione
    unique_cols = {
        list(c.columns)[0].name
        for c in SyncDestinazione.__table__.constraints
        if hasattr(c, "columns") and len(list(c.columns)) == 1
    }
    assert "codice_destinazione" in unique_cols


def test_sync_destinazione_optional_fields_nullable():
    from nssp_v2.sync.destinazioni.models import SyncDestinazione
    nullable = {c.name: c.nullable for c in SyncDestinazione.__table__.columns}
    for field in ("codice_cli", "numero_progressivo_cliente", "indirizzo",
                  "nazione_codice", "citta", "provincia", "telefono_1"):
        assert nullable[field] is True, f"Campo '{field}' deve essere nullable"
