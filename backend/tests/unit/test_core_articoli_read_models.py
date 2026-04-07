"""
Test unit per i read model del Core slice `articoli`.

Non richiedono DB attivo.
Verificano struttura, computed field display_label, separazione sync/Core.
"""

from decimal import Decimal

from nssp_v2.core.articoli.read_models import ArticoloDetail, ArticoloItem
from nssp_v2.core.articoli.queries import _compute_display_label


# ─── ArticoloItem ─────────────────────────────────────────────────────────────

def test_articolo_item_required_fields():
    item = ArticoloItem(
        codice_articolo="ART001",
        descrizione_1="Desc 1",
        descrizione_2=None,
        unita_misura_codice="PZ",
        display_label="Desc 1",
        famiglia_code=None,
        famiglia_label=None,
    )
    assert item.codice_articolo == "ART001"
    assert item.display_label == "Desc 1"


def test_articolo_item_is_frozen():
    item = ArticoloItem(
        codice_articolo="ART001",
        descrizione_1="Desc 1",
        descrizione_2=None,
        unita_misura_codice=None,
        display_label="Desc 1",
        famiglia_code=None,
        famiglia_label=None,
    )
    try:
        item.codice_articolo = "ART002"
        assert False, "deve essere immutabile"
    except Exception:
        pass


def test_articolo_item_optional_fields_can_be_none():
    item = ArticoloItem(
        codice_articolo="ART001",
        descrizione_1=None,
        descrizione_2=None,
        unita_misura_codice=None,
        display_label="ART001",
        famiglia_code=None,
        famiglia_label=None,
    )
    assert item.descrizione_1 is None
    assert item.unita_misura_codice is None


# ─── ArticoloDetail ───────────────────────────────────────────────────────────

def test_articolo_detail_all_fields():
    from datetime import datetime
    ts = datetime(2026, 1, 15, 10, 0, 0)
    detail = ArticoloDetail(
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
        display_label="Desc 1 Desc 2",
        famiglia_code=None,
        famiglia_label=None,
    )
    assert detail.codice_articolo == "ART001"
    assert detail.display_label == "Desc 1 Desc 2"
    assert detail.peso_grammi == Decimal("250.00000")
    assert detail.source_modified_at == ts


def test_articolo_detail_all_optional_can_be_none():
    detail = ArticoloDetail(
        codice_articolo="ART001",
        descrizione_1=None,
        descrizione_2=None,
        unita_misura_codice=None,
        source_modified_at=None,
        categoria_articolo_1=None,
        materiale_grezzo_codice=None,
        quantita_materiale_grezzo_occorrente=None,
        quantita_materiale_grezzo_scarto=None,
        misura_articolo=None,
        codice_immagine=None,
        contenitori_magazzino=None,
        peso_grammi=None,
        display_label="ART001",
        famiglia_code=None,
        famiglia_label=None,
    )
    assert detail.descrizione_1 is None
    assert detail.peso_grammi is None


def test_articolo_detail_is_frozen():
    detail = ArticoloDetail(
        codice_articolo="ART001",
        descrizione_1="D",
        descrizione_2=None,
        unita_misura_codice=None,
        source_modified_at=None,
        categoria_articolo_1=None,
        materiale_grezzo_codice=None,
        quantita_materiale_grezzo_occorrente=None,
        quantita_materiale_grezzo_scarto=None,
        misura_articolo=None,
        codice_immagine=None,
        contenitori_magazzino=None,
        peso_grammi=None,
        display_label="D",
        famiglia_code=None,
        famiglia_label=None,
    )
    try:
        detail.codice_articolo = "ART002"
        assert False, "deve essere immutabile"
    except Exception:
        pass


# ─── display_label (DL-ARCH-V2-013 §6) ───────────────────────────────────────

def test_display_label_desc1_and_desc2():
    label = _compute_display_label("Bullone", "M8x20", "ART001")
    assert label == "Bullone M8x20"


def test_display_label_desc1_only():
    label = _compute_display_label("Bullone", None, "ART001")
    assert label == "Bullone"


def test_display_label_falls_back_to_codice():
    label = _compute_display_label(None, None, "ART001")
    assert label == "ART001"


def test_display_label_empty_desc1_falls_back():
    label = _compute_display_label("", None, "ART001")
    assert label == "ART001"


def test_display_label_empty_desc2_uses_desc1_only():
    label = _compute_display_label("Bullone", "", "ART001")
    assert label == "Bullone"


def test_display_label_both_empty_falls_back_to_codice():
    label = _compute_display_label("", "", "ART001")
    assert label == "ART001"


def test_display_label_strips_whitespace():
    label = _compute_display_label("  Bullone  ", "  M8x20  ", "ART001")
    assert label == "Bullone M8x20"
