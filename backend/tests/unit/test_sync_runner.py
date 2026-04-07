"""
Test unit per SyncRunner — orchestratore sync on demand (DL-ARCH-V2-011).

Non richiedono DB PostgreSQL attivo.
Usano SQLite in-memory e FakeSource per isolare la logica di orchestrazione.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.clienti.source import FakeClienteSource, ClienteRecord
from nssp_v2.sync.destinazioni.source import FakeDestinazioneSource, DestinazioneRecord
from nssp_v2.app.services.sync_runner import (
    SyncRunner,
    SyncAlreadyRunningError,
    SyncEntityUnknownError,
    _RUNNING,
    _LOCK,
    _release,
)
from nssp_v2.sync.models import SyncEntityState, SyncRunLog


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_running():
    """Garantisce che il set _RUNNING sia vuoto prima di ogni test."""
    with _LOCK:
        _RUNNING.clear()
    yield
    with _LOCK:
        _RUNNING.clear()


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def fake_sources() -> dict:
    return {
        "clienti": FakeClienteSource([
            ClienteRecord(codice_cli="C001", ragione_sociale="Acme Srl"),
        ]),
        "destinazioni": FakeDestinazioneSource([
            DestinazioneRecord(codice_destinazione="D001", codice_cli="C001"),
        ]),
    }


# ─── Esecuzione base ──────────────────────────────────────────────────────────

def test_run_surface_returns_results_for_each_entity(session):
    runner = SyncRunner()
    results = runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())
    assert len(results) == 2
    assert results[0].entity_code == "clienti"
    assert results[1].entity_code == "destinazioni"


def test_run_surface_clienti_success(session):
    runner = SyncRunner()
    results = runner.run_surface(session, ["clienti"], {"clienti": FakeClienteSource([
        ClienteRecord(codice_cli="C001", ragione_sociale="Acme Srl"),
        ClienteRecord(codice_cli="C002", ragione_sociale="Beta Spa"),
    ])})
    assert results[0].status == "success"
    assert results[0].rows_seen == 2
    assert results[0].rows_written == 2
    assert results[0].run_id is not None


def test_run_surface_destinazioni_success(session):
    runner = SyncRunner()
    results = runner.run_surface(
        session,
        ["clienti", "destinazioni"],
        fake_sources(),
    )
    assert results[1].status == "success"
    assert results[1].entity_code == "destinazioni"


def test_run_surface_persists_run_log(session):
    runner = SyncRunner()
    runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())
    logs = session.query(SyncRunLog).all()
    entity_codes = {l.entity_code for l in logs}
    assert "clienti" in entity_codes
    assert "destinazioni" in entity_codes


def test_run_surface_updates_freshness_anchor(session):
    runner = SyncRunner()
    runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())
    clienti_state = session.get(SyncEntityState, "clienti")
    dest_state = session.get(SyncEntityState, "destinazioni")
    assert clienti_state.last_status == "success"
    assert clienti_state.last_success_at is not None
    assert dest_state.last_status == "success"


# ─── Ordine di esecuzione e dipendenze ───────────────────────────────────────

def test_run_surface_executes_in_declared_order(session):
    """L'ordine dei risultati corrisponde all'ordine dichiarato."""
    runner = SyncRunner()
    results = runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())
    assert results[0].entity_code == "clienti"
    assert results[1].entity_code == "destinazioni"


def test_run_surface_single_entity(session):
    runner = SyncRunner()
    results = runner.run_surface(session, ["clienti"], {"clienti": FakeClienteSource([
        ClienteRecord(codice_cli="C001", ragione_sociale="Acme"),
    ])})
    assert len(results) == 1
    assert results[0].entity_code == "clienti"
    assert results[0].status == "success"


# ─── Gestione sorgente mancante ───────────────────────────────────────────────

def test_run_surface_missing_source_returns_error_result(session):
    """Se la sorgente per un'entita e assente, produce EntityRunResult con status=error."""
    runner = SyncRunner()
    results = runner.run_surface(
        session,
        ["clienti", "destinazioni"],
        {"clienti": FakeClienteSource([ClienteRecord(codice_cli="C001", ragione_sociale="Acme")])},
        # destinazioni source assente
    )
    dest_result = next(r for r in results if r.entity_code == "destinazioni")
    assert dest_result.status == "error"
    assert dest_result.error_message is not None
    assert dest_result.run_id is None


# ─── Concorrenza ──────────────────────────────────────────────────────────────

def test_run_surface_raises_if_already_running(session):
    """SyncAlreadyRunningError se un'entita e gia in _RUNNING."""
    with _LOCK:
        _RUNNING.add("clienti")

    runner = SyncRunner()
    with pytest.raises(SyncAlreadyRunningError) as exc_info:
        runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())

    assert "clienti" in exc_info.value.running_entities


def test_run_surface_releases_lock_after_success(session):
    runner = SyncRunner()
    runner.run_surface(session, ["clienti", "destinazioni"], fake_sources())
    with _LOCK:
        assert "clienti" not in _RUNNING
        assert "destinazioni" not in _RUNNING


def test_run_surface_releases_lock_after_error(session):
    """Il lock deve essere rilasciato anche in caso di eccezione interna."""
    class BrokenSource:
        def fetch_all(self):
            raise RuntimeError("sorgente rotta")

    runner = SyncRunner()
    results = runner.run_surface(
        session, ["clienti"], {"clienti": BrokenSource()}
    )
    # La sync unit gestisce l'eccezione internamente e la riflette nel status
    assert results[0].status == "error"
    # Il lock deve essere rilasciato
    with _LOCK:
        assert "clienti" not in _RUNNING


def test_run_surface_concurrent_different_entities_not_blocked(session):
    """Entita diverse possono essere acquisite in run separati senza conflitto."""
    runner = SyncRunner()
    results1 = runner.run_surface(session, ["clienti"], {"clienti": FakeClienteSource([
        ClienteRecord(codice_cli="C001", ragione_sociale="Acme"),
    ])})
    results2 = runner.run_surface(session, ["destinazioni"], {"destinazioni": FakeDestinazioneSource([
        DestinazioneRecord(codice_destinazione="D001"),
    ])})
    assert results1[0].status == "success"
    assert results2[0].status == "success"


# ─── Entity code sconosciuto ──────────────────────────────────────────────────

def test_run_surface_unknown_entity_raises(session):
    runner = SyncRunner()
    with pytest.raises(SyncEntityUnknownError) as exc_info:
        runner.run_surface(session, ["entity_inesistente"], {})
    assert exc_info.value.entity_code == "entity_inesistente"


def test_run_surface_unknown_entity_does_not_acquire_lock(session):
    runner = SyncRunner()
    with pytest.raises(SyncEntityUnknownError):
        runner.run_surface(session, ["entity_inesistente"], {})
    with _LOCK:
        assert "entity_inesistente" not in _RUNNING
