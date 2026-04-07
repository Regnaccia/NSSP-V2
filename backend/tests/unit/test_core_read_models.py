"""
Test unit per i read model del Core slice `clienti + destinazioni`.

Non richiedono DB attivo.
Verificano struttura, computed field display_label, separazione dati Easy / interni,
flag is_primary (DL-ARCH-V2-012).
"""

from nssp_v2.core.clienti_destinazioni.read_models import (
    ClienteItem,
    DestinazioneDetail,
    DestinazioneItem,
)
from nssp_v2.core.clienti_destinazioni.queries import (
    _compute_display_label,
    _compute_primary_display_label,
    _primary_codice,
    _is_primary_codice,
    _codice_cli_from_primary,
)


# ─── ClienteItem ─────────────────────────────────────────────────────────────

def test_cliente_item_required_fields():
    item = ClienteItem(codice_cli="C001", ragione_sociale="Acme Srl")
    assert item.codice_cli == "C001"
    assert item.ragione_sociale == "Acme Srl"


def test_cliente_item_is_frozen():
    item = ClienteItem(codice_cli="C001", ragione_sociale="Acme Srl")
    try:
        item.codice_cli = "C002"
        assert False, "deve essere immutabile"
    except Exception:
        pass


# ─── DestinazioneItem ─────────────────────────────────────────────────────────

def test_destinazione_item_required_fields():
    item = DestinazioneItem(
        codice_destinazione="D001",
        codice_cli="C001",
        numero_progressivo_cliente="001",
        indirizzo="Via Roma 1",
        citta="Milano",
        provincia="MI",
        nickname_destinazione="Sede Milano",
        display_label="Sede Milano",
        is_primary=False,
    )
    assert item.codice_destinazione == "D001"
    assert item.display_label == "Sede Milano"
    assert item.is_primary is False


def test_destinazione_item_optional_fields_can_be_none():
    item = DestinazioneItem(
        codice_destinazione="D001",
        codice_cli=None,
        numero_progressivo_cliente=None,
        indirizzo=None,
        citta=None,
        provincia=None,
        nickname_destinazione=None,
        display_label="D001",
        is_primary=False,
    )
    assert item.codice_cli is None
    assert item.nickname_destinazione is None


def test_destinazione_item_is_primary_true():
    item = DestinazioneItem(
        codice_destinazione="MAIN:C001",
        codice_cli="C001",
        numero_progressivo_cliente=None,
        indirizzo=None,
        citta=None,
        provincia=None,
        nickname_destinazione=None,
        display_label="Acme Srl",
        is_primary=True,
    )
    assert item.is_primary is True
    assert item.codice_destinazione == "MAIN:C001"


# ─── DestinazioneDetail ───────────────────────────────────────────────────────

def test_destinazione_detail_has_ragione_sociale_cliente():
    detail = DestinazioneDetail(
        codice_destinazione="D001",
        codice_cli="C001",
        numero_progressivo_cliente="001",
        indirizzo="Via Roma 1",
        citta="Milano",
        provincia="MI",
        nazione_codice="IT",
        telefono_1="02 123456",
        ragione_sociale_cliente="Acme Srl",
        nickname_destinazione=None,
        display_label="Via Roma 1",
        is_primary=False,
    )
    assert detail.ragione_sociale_cliente == "Acme Srl"
    assert detail.nazione_codice == "IT"
    assert detail.telefono_1 == "02 123456"
    assert detail.is_primary is False


def test_destinazione_detail_ragione_sociale_cliente_nullable():
    detail = DestinazioneDetail(
        codice_destinazione="D001",
        codice_cli=None,
        numero_progressivo_cliente=None,
        indirizzo=None,
        citta=None,
        provincia=None,
        nazione_codice=None,
        telefono_1=None,
        ragione_sociale_cliente=None,
        nickname_destinazione=None,
        display_label="D001",
        is_primary=False,
    )
    assert detail.ragione_sociale_cliente is None


# ─── Identita della destinazione principale (DL-ARCH-V2-012 §4) ──────────────

def test_primary_codice_format():
    assert _primary_codice("C001") == "MAIN:C001"


def test_is_primary_codice_true():
    assert _is_primary_codice("MAIN:C001") is True


def test_is_primary_codice_false_for_aggiuntiva():
    assert _is_primary_codice("D001") is False
    assert _is_primary_codice("POT001") is False


def test_codice_cli_from_primary():
    assert _codice_cli_from_primary("MAIN:C001") == "C001"
    assert _codice_cli_from_primary("MAIN:ABC-123") == "ABC-123"


# ─── display_label aggiuntive: separazione Easy / interno ─────────────────────

def test_display_label_uses_nickname_first():
    label = _compute_display_label("Sede Milano", "Via Roma 1", "D001")
    assert label == "Sede Milano"


def test_display_label_falls_back_to_indirizzo():
    label = _compute_display_label(None, "Via Roma 1", "D001")
    assert label == "Via Roma 1"


def test_display_label_falls_back_to_codice():
    label = _compute_display_label(None, None, "D001")
    assert label == "D001"


def test_display_label_empty_nickname_falls_back():
    label = _compute_display_label("", "Via Roma 1", "D001")
    assert label == "Via Roma 1"


def test_display_label_empty_indirizzo_falls_back():
    label = _compute_display_label(None, "", "D001")
    assert label == "D001"


# ─── display_label principale (DL-ARCH-V2-012 §3) ────────────────────────────

def test_primary_display_label_uses_nickname_first():
    label = _compute_primary_display_label("HQ", "Acme Srl", "C001")
    assert label == "HQ"


def test_primary_display_label_falls_back_to_ragione_sociale():
    label = _compute_primary_display_label(None, "Acme Srl", "C001")
    assert label == "Acme Srl"


def test_primary_display_label_falls_back_to_codice_cli():
    label = _compute_primary_display_label(None, "", "C001")
    assert label == "C001"


# ─── Separazione dati Easy vs interni (contratto strutturale) ────────────────

def test_destinazione_item_easy_fields_are_read_only_by_origin():
    item = DestinazioneItem(
        codice_destinazione="D001",
        codice_cli="C001",
        numero_progressivo_cliente="001",
        indirizzo="Via Roma 1",
        citta="Milano",
        provincia="MI",
        nickname_destinazione=None,
        display_label="Via Roma 1",
        is_primary=False,
    )
    try:
        item.indirizzo = "Via Nuova 2"
        assert False, "DestinazioneItem deve essere frozen"
    except Exception:
        pass


def test_destinazione_detail_easy_fields_vs_internal():
    detail = DestinazioneDetail(
        codice_destinazione="D001",
        codice_cli="C001",
        numero_progressivo_cliente=None,
        indirizzo="Via Roma 1",
        citta="Milano",
        provincia="MI",
        nazione_codice="IT",
        telefono_1=None,
        ragione_sociale_cliente="Acme Srl",
        nickname_destinazione="HUB Nord",
        display_label="HUB Nord",
        is_primary=False,
    )
    assert detail.nickname_destinazione == "HUB Nord"
    assert detail.indirizzo == "Via Roma 1"
    assert detail.display_label == "HUB Nord"
