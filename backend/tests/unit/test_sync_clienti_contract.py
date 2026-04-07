"""
Test unit per la sync unit `clienti` — contratto, source adapter, RunMetadata.

Non richiedono DB attivo.
Verificano:
- contratto obbligatorio dichiarato (DL-ARCH-V2-009)
- source adapter read-only (nessun metodo write)
- RunMetadata struttura
- FakeClienteSource comportamento
"""

import inspect

import pytest

from nssp_v2.sync.clienti.source import ClienteRecord, ClienteSourceAdapter, FakeClienteSource
from nssp_v2.sync.clienti.unit import ClienteSyncUnit
from nssp_v2.sync.contract import (
    ALIGNMENT_STRATEGIES,
    CHANGE_ACQUISITION_STRATEGIES,
    DELETE_HANDLING_POLICIES,
    RunMetadata,
)


# ─── Contratto sync unit (DL-ARCH-V2-009) ────────────────────────────────────

def test_entity_code_declared():
    assert ClienteSyncUnit.ENTITY_CODE == "clienti"


def test_source_identity_key_declared():
    assert ClienteSyncUnit.SOURCE_IDENTITY_KEY == "codice_cli"


def test_alignment_strategy_declared_and_valid():
    assert ClienteSyncUnit.ALIGNMENT_STRATEGY in ALIGNMENT_STRATEGIES


def test_change_acquisition_declared_and_valid():
    assert ClienteSyncUnit.CHANGE_ACQUISITION in CHANGE_ACQUISITION_STRATEGIES


def test_delete_handling_declared_and_valid():
    assert ClienteSyncUnit.DELETE_HANDLING in DELETE_HANDLING_POLICIES


def test_dependencies_declared():
    assert isinstance(ClienteSyncUnit.DEPENDENCIES, list)


def test_clienti_has_no_sync_dependencies():
    """clienti e la prima entita: nessuna dipendenza da altre sync unit."""
    assert ClienteSyncUnit.DEPENDENCIES == []


# ─── Source adapter read-only (DL-ARCH-V2-007 §2) ────────────────────────────

def test_source_adapter_has_no_write_methods():
    """L'interfaccia ClienteSourceAdapter non deve esporre metodi write."""
    write_keywords = ("write", "insert", "update", "delete", "save", "create", "push", "send")
    methods = [
        name for name, _ in inspect.getmembers(ClienteSourceAdapter, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    for method in methods:
        for kw in write_keywords:
            assert kw not in method.lower(), (
                f"ClienteSourceAdapter espone un metodo con semantica write: '{method}'"
            )


def test_fake_source_fetch_all_returns_records():
    records = [
        ClienteRecord(codice_cli="C001", ragione_sociale="Alfa Srl"),
        ClienteRecord(codice_cli="C002", ragione_sociale="Beta Spa"),
    ]
    source = FakeClienteSource(records)
    result = source.fetch_all()
    assert len(result) == 2
    assert result[0].codice_cli == "C001"
    assert result[1].ragione_sociale == "Beta Spa"


def test_fake_source_fetch_all_is_non_destructive():
    """fetch_all puo essere chiamato piu volte con lo stesso risultato."""
    records = [ClienteRecord(codice_cli="C001", ragione_sociale="Alfa Srl")]
    source = FakeClienteSource(records)
    first = source.fetch_all()
    second = source.fetch_all()
    assert first == second


def test_fake_source_empty():
    source = FakeClienteSource([])
    assert source.fetch_all() == []


# ─── RunMetadata struttura ────────────────────────────────────────────────────

def test_run_metadata_required_fields():
    from datetime import datetime, timezone
    meta = RunMetadata(
        run_id="test-run-id",
        entity_code="clienti",
        started_at=datetime.now(timezone.utc),
    )
    assert meta.run_id == "test-run-id"
    assert meta.entity_code == "clienti"
    assert meta.status == "running"
    assert meta.rows_seen == 0
    assert meta.rows_written == 0
    assert meta.rows_deleted == 0
    assert meta.finished_at is None
    assert meta.error_message is None


def test_run_metadata_status_values():
    """I valori di status attesi sono running, success, error."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for status in ("running", "success", "error"):
        meta = RunMetadata(run_id="x", entity_code="clienti", started_at=now, status=status)
        assert meta.status == status


# ─── Modelli SQLAlchemy — struttura tabelle (no DB) ──────────────────────────

def test_sync_cliente_tablename():
    from nssp_v2.sync.clienti.models import SyncCliente
    assert SyncCliente.__tablename__ == "sync_clienti"


def test_sync_cliente_has_required_columns():
    from nssp_v2.sync.clienti.models import SyncCliente
    cols = {c.name for c in SyncCliente.__table__.columns}
    assert {"id", "codice_cli", "ragione_sociale", "attivo", "synced_at"} <= cols


def test_sync_cliente_codice_cli_is_unique():
    from nssp_v2.sync.clienti.models import SyncCliente
    unique_cols = {
        list(c.columns)[0].name
        for c in SyncCliente.__table__.constraints
        if hasattr(c, "columns") and len(list(c.columns)) == 1
    }
    assert "codice_cli" in unique_cols


def test_sync_run_log_tablename():
    from nssp_v2.sync.clienti.models import SyncRunLog
    assert SyncRunLog.__tablename__ == "sync_run_log"


def test_sync_run_log_has_required_columns():
    from nssp_v2.sync.clienti.models import SyncRunLog
    cols = {c.name for c in SyncRunLog.__table__.columns}
    assert {"run_id", "entity_code", "started_at", "finished_at", "status",
            "rows_seen", "rows_written", "rows_deleted", "error_message"} <= cols


def test_sync_entity_state_tablename():
    from nssp_v2.sync.clienti.models import SyncEntityState
    assert SyncEntityState.__tablename__ == "sync_entity_state"


def test_sync_entity_state_has_required_columns():
    from nssp_v2.sync.clienti.models import SyncEntityState
    cols = {c.name for c in SyncEntityState.__table__.columns}
    assert {"entity_code", "last_run_at", "last_success_at", "last_status", "last_error"} <= cols
