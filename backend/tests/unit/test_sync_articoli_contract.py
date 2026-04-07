"""
Test unit per la sync unit `articoli` — contratto, source adapter, modelli.

Non richiedono DB attivo.
Verificano:
- contratto obbligatorio dichiarato (DL-ARCH-V2-009)
- source adapter read-only (nessun metodo write)
- FakeArticoloSource comportamento
- EasyArticoloSource contratto (senza connessione reale)
- ArticoloRecord campi EASY_ARTICOLI.md
"""

import inspect
from decimal import Decimal

from nssp_v2.sync.articoli.source import (
    ArticoloRecord,
    ArticoloSourceAdapter,
    EasyArticoloSource,
    FakeArticoloSource,
)
from nssp_v2.sync.articoli.unit import ArticoloSyncUnit
from nssp_v2.sync.contract import (
    ALIGNMENT_STRATEGIES,
    CHANGE_ACQUISITION_STRATEGIES,
    DELETE_HANDLING_POLICIES,
)


# ─── Contratto sync unit (DL-ARCH-V2-009) ────────────────────────────────────

def test_entity_code_declared():
    assert ArticoloSyncUnit.ENTITY_CODE == "articoli"


def test_source_identity_key_declared():
    assert ArticoloSyncUnit.SOURCE_IDENTITY_KEY == "codice_articolo"


def test_alignment_strategy_declared_and_valid():
    assert ArticoloSyncUnit.ALIGNMENT_STRATEGY in ALIGNMENT_STRATEGIES


def test_change_acquisition_declared_and_valid():
    assert ArticoloSyncUnit.CHANGE_ACQUISITION in CHANGE_ACQUISITION_STRATEGIES


def test_delete_handling_declared_and_valid():
    assert ArticoloSyncUnit.DELETE_HANDLING in DELETE_HANDLING_POLICIES


def test_dependencies_declared():
    assert isinstance(ArticoloSyncUnit.DEPENDENCIES, list)


def test_articoli_has_no_sync_dependencies():
    """articoli non dipende da altre sync unit."""
    assert ArticoloSyncUnit.DEPENDENCIES == []


# ─── Source adapter read-only (DL-ARCH-V2-007 §2) ────────────────────────────

def test_source_adapter_has_no_write_methods():
    """L'interfaccia ArticoloSourceAdapter non deve esporre metodi write."""
    write_keywords = ("write", "insert", "update", "delete", "save", "create", "push", "send")
    methods = [
        name for name, _ in inspect.getmembers(ArticoloSourceAdapter, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    for method in methods:
        for kw in write_keywords:
            assert kw not in method.lower(), (
                f"ArticoloSourceAdapter espone un metodo con semantica write: '{method}'"
            )


def test_fake_source_fetch_all_returns_records():
    records = [
        ArticoloRecord(codice_articolo="ART001", descrizione_1="Desc 1"),
        ArticoloRecord(codice_articolo="ART002", descrizione_1="Desc 2"),
    ]
    source = FakeArticoloSource(records)
    result = source.fetch_all()
    assert len(result) == 2
    assert result[0].codice_articolo == "ART001"
    assert result[1].descrizione_1 == "Desc 2"


def test_fake_source_fetch_all_is_non_destructive():
    """fetch_all puo essere chiamato piu volte con lo stesso risultato."""
    records = [ArticoloRecord(codice_articolo="ART001")]
    source = FakeArticoloSource(records)
    first = source.fetch_all()
    second = source.fetch_all()
    assert first == second


def test_fake_source_empty():
    source = FakeArticoloSource([])
    assert source.fetch_all() == []


# ─── Modelli SQLAlchemy — struttura tabelle (no DB) ──────────────────────────

def test_sync_articolo_tablename():
    from nssp_v2.sync.articoli.models import SyncArticolo
    assert SyncArticolo.__tablename__ == "sync_articoli"


def test_sync_articolo_has_required_columns():
    from nssp_v2.sync.articoli.models import SyncArticolo
    cols = {c.name for c in SyncArticolo.__table__.columns}
    assert {
        "id", "codice_articolo", "descrizione_1", "descrizione_2",
        "unita_misura_codice", "source_modified_at",
        "categoria_articolo_1", "materiale_grezzo_codice",
        "quantita_materiale_grezzo_occorrente", "quantita_materiale_grezzo_scarto",
        "misura_articolo", "codice_immagine", "contenitori_magazzino",
        "peso_grammi", "attivo", "synced_at",
    } <= cols


def test_sync_articolo_nullable_fields():
    from nssp_v2.sync.articoli.models import SyncArticolo
    nullable_fields = {c.name: c.nullable for c in SyncArticolo.__table__.columns}
    for field in (
        "descrizione_1", "descrizione_2", "unita_misura_codice", "source_modified_at",
        "categoria_articolo_1", "materiale_grezzo_codice",
        "quantita_materiale_grezzo_occorrente", "quantita_materiale_grezzo_scarto",
        "misura_articolo", "codice_immagine", "contenitori_magazzino", "peso_grammi",
    ):
        assert nullable_fields[field] is True, f"Campo '{field}' deve essere nullable"


def test_sync_articolo_codice_articolo_is_unique():
    from nssp_v2.sync.articoli.models import SyncArticolo
    unique_cols = {
        list(c.columns)[0].name
        for c in SyncArticolo.__table__.constraints
        if hasattr(c, "columns") and len(list(c.columns)) == 1
    }
    assert "codice_articolo" in unique_cols


# ─── ArticoloRecord campi EASY_ARTICOLI.md ───────────────────────────────────

def test_articolo_record_required_fields():
    rec = ArticoloRecord(codice_articolo="ART001")
    assert rec.codice_articolo == "ART001"


def test_articolo_record_optional_fields_default_none():
    rec = ArticoloRecord(codice_articolo="ART001")
    assert rec.descrizione_1 is None
    assert rec.descrizione_2 is None
    assert rec.unita_misura_codice is None
    assert rec.source_modified_at is None
    assert rec.categoria_articolo_1 is None
    assert rec.materiale_grezzo_codice is None
    assert rec.quantita_materiale_grezzo_occorrente is None
    assert rec.quantita_materiale_grezzo_scarto is None
    assert rec.misura_articolo is None
    assert rec.codice_immagine is None
    assert rec.contenitori_magazzino is None
    assert rec.peso_grammi is None


def test_articolo_record_optional_fields_settable():
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc)
    rec = ArticoloRecord(
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
    )
    assert rec.descrizione_1 == "Desc 1"
    assert rec.unita_misura_codice == "PZ"
    assert rec.peso_grammi == Decimal("250.00000")
    assert rec.source_modified_at == ts


# ─── EasyArticoloSource contratto (senza connessione reale) ──────────────────

def test_easy_source_has_no_write_methods():
    """EasyArticoloSource non deve esporre metodi write."""
    write_keywords = ("write", "insert", "update", "delete", "save", "create", "push", "send")
    methods = [
        name for name, _ in inspect.getmembers(EasyArticoloSource, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    for method in methods:
        for kw in write_keywords:
            assert kw not in method.lower(), (
                f"EasyArticoloSource espone un metodo con semantica write: '{method}'"
            )


def test_easy_source_is_subclass_of_adapter():
    """EasyArticoloSource deve implementare ArticoloSourceAdapter."""
    assert issubclass(EasyArticoloSource, ArticoloSourceAdapter)


def test_easy_source_query_is_select_only():
    """La query usata da EasyArticoloSource deve essere SELECT, non write."""
    query = EasyArticoloSource._QUERY.strip().upper()
    assert query.startswith("SELECT"), "La query deve iniziare con SELECT"
    for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"):
        assert keyword not in query, f"La query non deve contenere '{keyword}'"


def test_easy_source_query_contains_all_mapped_fields():
    """La query deve includere tutti i campi del mapping EASY_ARTICOLI.md."""
    query = EasyArticoloSource._QUERY.upper()
    for field in (
        "ART_COD", "ART_DES1", "ART_DES2", "UM_COD", "ART_DTMO",
        "CAT_ART1", "MAT_COD", "REGN_QT_OCCORR", "REGN_QT_SCARTO",
        "ART_MISURA", "COD_IMM", "ART_CONTEN", "ART_KG",
    ):
        assert field in query, f"La query non include il campo '{field}'"
