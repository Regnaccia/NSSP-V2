"""
Test di integrazione per i commitments dalla provenienza `production` (TASK-V2-043).

Verificano:
- source_type = "production"
- source_reference = str(id_dettaglio)
- committed_qty = materiale_partenza_per_pezzo (MM_PEZZO)
- solo produzioni attive bucket=active incluse
- produzione completata (quantita_prodotta >= ordinata) esclusa
- produzione con forza_completata=True esclusa
- materiale con CAT_ART1 = "0" escluso
- materiale con CAT_ART1 = None (non trovato in sync_articoli) escluso
- materiale con CAT_ART1 != "0" incluso
- materiale_partenza_codice None -> escluso
- materiale_partenza_per_pezzo None o <= 0 -> escluso
- aggregazione per articolo con contributi da production
- coesistenza customer_order + production nello stesso rebuild
- rebuild deterministico per production
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.produzioni.models import CoreProduzioneOverride
from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.core.commitments.queries import rebuild_commitments, list_commitments, get_commitments_by_article


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


def _insert_produzione(session, id_dettaglio, **kwargs):
    defaults = dict(
        cliente_ragione_sociale="Cliente Srl",
        codice_articolo="PROD001",
        descrizione_articolo="Articolo prodotto",
        numero_documento="DP001",
        numero_riga_documento=1,
        quantita_ordinata=Decimal("100.00000"),
        quantita_prodotta=Decimal("10.00000"),
        materiale_partenza_codice="MAT001",
        materiale_partenza_per_pezzo=Decimal("5.00000"),
        misura_articolo="150x50",
        codice_immagine=None,
        riferimento_numero_ordine_cliente=None,
        riferimento_riga_ordine_cliente=None,
        note_articolo=None,
        attivo=True,
        synced_at=_NOW,
    )
    defaults.update(kwargs)
    obj = SyncProduzioneAttiva(id_dettaglio=id_dettaglio, **defaults)
    session.add(obj)
    session.flush()
    return obj


def _insert_articolo(session, codice, cat_art1="1", **kwargs):
    """Inserisce un articolo in sync_articoli con CAT_ART1 specificato."""
    defaults = dict(
        descrizione_1="Articolo",
        descrizione_2=None,
        unita_misura_codice="PZ",
        source_modified_at=None,
        materiale_grezzo_codice=None,
        quantita_materiale_grezzo_occorrente=None,
        quantita_materiale_grezzo_scarto=None,
        misura_articolo=None,
        codice_immagine=None,
        contenitori_magazzino=None,
        peso_grammi=None,
        attivo=True,
        synced_at=_NOW,
    )
    defaults.update(kwargs)
    defaults["categoria_articolo_1"] = cat_art1
    obj = SyncArticolo(codice_articolo=codice, **defaults)
    session.add(obj)
    session.flush()
    return obj


def _insert_override(session, id_dettaglio, forza_completata=True):
    obj = CoreProduzioneOverride(
        id_dettaglio=id_dettaglio,
        bucket="active",
        forza_completata=forza_completata,
    )
    session.add(obj)
    session.flush()
    return obj


# ─── Mapping di base ──────────────────────────────────────────────────────────

def test_production_source_type(session):
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001)
    rebuild_commitments(session)

    items = list_commitments(session, source_type="production")
    assert len(items) == 1
    assert items[0].source_type == "production"


def test_production_source_reference_e_id_dettaglio(session):
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001)
    rebuild_commitments(session)

    items = list_commitments(session, source_type="production")
    assert items[0].source_reference == "1001"


def test_committed_qty_uguale_a_mm_pezzo(session):
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_per_pezzo=Decimal("7.50000"))
    rebuild_commitments(session)

    items = list_commitments(session, source_type="production")
    assert items[0].committed_qty == Decimal("7.50000")


def test_article_code_e_materiale_non_articolo_prodotto(session):
    """article_code del commitment e il materiale (MAT_COD), non l'articolo prodotto."""
    _insert_articolo(session, "MAT001", cat_art1="2")
    _insert_produzione(session, 1001,
                       codice_articolo="PROD_FINITO",
                       materiale_partenza_codice="MAT001",
                       materiale_partenza_per_pezzo=Decimal("3.00000"))
    rebuild_commitments(session)

    items = list_commitments(session, source_type="production")
    assert items[0].article_code == "MAT001"


def test_materiale_codice_case_insensitive_vs_sync_articoli(session):
    """Il lookup MAT_COD -> CAT_ART1 resta valido anche con differenze di casing/spazi."""
    _insert_articolo(session, "MAT001", cat_art1="2")
    _insert_produzione(
        session,
        1001,
        materiale_partenza_codice=" mat001 ",
        materiale_partenza_per_pezzo=Decimal("3.00000"),
    )

    rebuild_commitments(session)

    items = list_commitments(session, source_type="production")
    assert len(items) == 1
    assert items[0].article_code == "MAT001"


# ─── Filtro stato attiva ──────────────────────────────────────────────────────

def test_produzione_completata_per_quantita_esclusa(session):
    """Produzione completata (prodotta >= ordinata) non genera commitment."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001,
                       quantita_ordinata=Decimal("100.00000"),
                       quantita_prodotta=Decimal("100.00000"))
    n = rebuild_commitments(session)
    assert n == 0
    assert list_commitments(session, source_type="production") == []


def test_produzione_forza_completata_esclusa(session):
    """Produzione con override forza_completata=True non genera commitment."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001,
                       quantita_ordinata=Decimal("100.00000"),
                       quantita_prodotta=Decimal("10.00000"))
    _insert_override(session, 1001, forza_completata=True)
    n = rebuild_commitments(session)
    assert n == 0


def test_produzione_attiva_inclusa(session):
    """Produzione con prodotta < ordinata e senza override e attiva."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001,
                       quantita_ordinata=Decimal("100.00000"),
                       quantita_prodotta=Decimal("30.00000"))
    n = rebuild_commitments(session)
    assert n == 1


def test_produzione_non_attiva_flag_esclusa(session):
    """Produzione con attivo=False non genera commitment."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, attivo=False)
    n = rebuild_commitments(session)
    assert n == 0


# ─── Filtro CAT_ART1 ──────────────────────────────────────────────────────────

def test_cat_art1_zero_escluso(session):
    """Materiale con CAT_ART1 = '0' (mm) e escluso dal V1."""
    _insert_articolo(session, "MAT001", cat_art1="0")
    _insert_produzione(session, 1001, materiale_partenza_codice="MAT001")
    n = rebuild_commitments(session)
    assert n == 0


def test_cat_art1_non_trovato_escluso(session):
    """Materiale non presente in sync_articoli (CAT_ART1 non verificabile) e escluso."""
    # Non inserisco l'articolo MAT001 in sync_articoli
    _insert_produzione(session, 1001, materiale_partenza_codice="MAT001")
    n = rebuild_commitments(session)
    assert n == 0


def test_cat_art1_diverso_da_zero_incluso(session):
    """Materiale con CAT_ART1 != '0' genera commitment."""
    _insert_articolo(session, "MAT001", cat_art1="3")
    _insert_produzione(session, 1001, materiale_partenza_codice="MAT001")
    n = rebuild_commitments(session)
    assert n == 1


def test_cat_art1_none_nel_db_escluso(session):
    """Articolo con categoria_articolo_1 = None in sync_articoli e escluso."""
    _insert_articolo(session, "MAT001", cat_art1=None)
    _insert_produzione(session, 1001, materiale_partenza_codice="MAT001")
    n = rebuild_commitments(session)
    assert n == 0


# ─── Filtri su materiale ──────────────────────────────────────────────────────

def test_materiale_codice_none_escluso(session):
    _insert_produzione(session, 1001, materiale_partenza_codice=None)
    n = rebuild_commitments(session)
    assert n == 0


def test_materiale_per_pezzo_none_escluso(session):
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_per_pezzo=None)
    n = rebuild_commitments(session)
    assert n == 0


def test_materiale_per_pezzo_zero_escluso(session):
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_per_pezzo=Decimal("0.00000"))
    n = rebuild_commitments(session)
    assert n == 0


# ─── Aggregazione ─────────────────────────────────────────────────────────────

def test_piu_produzioni_stesso_materiale_aggregate(session):
    """Piu produzioni attive che usano lo stesso materiale sommano nel commitment aggregato."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_per_pezzo=Decimal("5.00000"))
    _insert_produzione(session, 1002, materiale_partenza_per_pezzo=Decimal("3.00000"))
    rebuild_commitments(session)

    agg = get_commitments_by_article(session, article_code="MAT001")
    assert len(agg) == 1
    assert agg[0].total_committed_qty == Decimal("8.00000")
    assert agg[0].commitment_count == 2


# ─── Coesistenza customer_order + production ──────────────────────────────────

def test_rebuild_include_entrambe_le_provenienze(session):
    """Il rebuild include sia customer_order che production nella stessa fact."""
    from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente

    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_codice="MAT001",
                       materiale_partenza_per_pezzo=Decimal("5.00000"))

    riga = SyncRigaOrdineCliente(
        order_reference="ORD001",
        line_reference=1,
        article_code="ART001",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("0.00000"),
        set_aside_qty=Decimal("0.00000"),
        continues_previous_line=False,
        synced_at=_NOW,
    )
    session.add(riga)
    session.flush()

    n = rebuild_commitments(session)
    assert n == 2

    prod_items = list_commitments(session, source_type="production")
    co_items = list_commitments(session, source_type="customer_order")
    assert len(prod_items) == 1
    assert len(co_items) == 1


def test_aggregazione_cross_source_stesso_articolo(session):
    """Commitments da production e customer_order sullo stesso article_code si sommano."""
    from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente

    _insert_articolo(session, "ART001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_codice="ART001",
                       materiale_partenza_per_pezzo=Decimal("10.00000"))

    riga = SyncRigaOrdineCliente(
        order_reference="ORD001",
        line_reference=1,
        article_code="ART001",
        ordered_qty=Decimal("50.00000"),
        fulfilled_qty=Decimal("0.00000"),
        set_aside_qty=Decimal("0.00000"),
        continues_previous_line=False,
        synced_at=_NOW,
    )
    session.add(riga)
    session.flush()

    rebuild_commitments(session)
    agg = get_commitments_by_article(session, article_code="ART001")
    assert len(agg) == 1
    assert agg[0].total_committed_qty == Decimal("60.00000")  # 10 (prod) + 50 (order)
    assert agg[0].commitment_count == 2


# ─── Determinismo ─────────────────────────────────────────────────────────────

def test_rebuild_deterministico_production(session):
    """Stesso input, stesso output dal rebuild."""
    _insert_articolo(session, "MAT001", cat_art1="1")
    _insert_produzione(session, 1001, materiale_partenza_per_pezzo=Decimal("5.00000"))

    rebuild_commitments(session)
    c1 = session.query(CoreCommitment).filter_by(source_type="production").one().committed_qty

    rebuild_commitments(session)
    c2 = session.query(CoreCommitment).filter_by(source_type="production").one().committed_qty

    assert c1 == c2
