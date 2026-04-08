"""
Test di integrazione per il Core slice `produzioni` (TASK-V2-030, TASK-V2-034, TASK-V2-035).

Verificano:
- bucket corretto (active / historical)
- stato_produzione computato dalle quantita
- precedenza di forza_completata sull'override
- aggiornamento del flag forza_completata
- aggregazione da entrambi i mirror
- filtro bucket e paginazione (TASK-V2-034)
- filtro stato_produzione e ricerca testuale (TASK-V2-035)
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.produzioni.queries import list_produzioni, set_forza_completata
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica
from nssp_v2.core.produzioni.models import CoreProduzioneOverride

from datetime import datetime, timezone


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime(2026, 4, 8, 12, 0, 0, tzinfo=timezone.utc)


def _attiva(id_dettaglio: int, qtor=Decimal("100"), qtev=Decimal("0"), **kwargs) -> SyncProduzioneAttiva:
    return SyncProduzioneAttiva(
        id_dettaglio=id_dettaglio,
        cliente_ragione_sociale=kwargs.get("cliente", "ACME SRL"),
        codice_articolo=kwargs.get("codice_articolo", "ART001"),
        descrizione_articolo=kwargs.get("descrizione_articolo", "Bullone"),
        numero_documento=kwargs.get("numero_documento", "DOC01"),
        numero_riga_documento=kwargs.get("numero_riga_documento", 1),
        quantita_ordinata=qtor,
        quantita_prodotta=qtev,
        attivo=True,
        synced_at=_NOW,
    )


def _storica(id_dettaglio: int, qtor=Decimal("100"), qtev=Decimal("100"), **kwargs) -> SyncProduzioneStorica:
    return SyncProduzioneStorica(
        id_dettaglio=id_dettaglio,
        cliente_ragione_sociale=kwargs.get("cliente", "BETA SPA"),
        codice_articolo=kwargs.get("codice_articolo", "ART002"),
        descrizione_articolo=kwargs.get("descrizione_articolo", "Dado"),
        numero_documento=kwargs.get("numero_documento", "DOC02"),
        numero_riga_documento=kwargs.get("numero_riga_documento", 1),
        quantita_ordinata=qtor,
        quantita_prodotta=qtev,
        attivo=True,
        synced_at=_NOW,
    )


# ─── Helper: items da lista ───────────────────────────────────────────────────

def _items(session, **kwargs):
    """Scorciatoia: restituisce items della pagina con i parametri dati."""
    return list_produzioni(session, **kwargs).items


# ─── Bucket ───────────────────────────────────────────────────────────────────

def test_bucket_active(session):
    session.add(_attiva(1001))
    session.flush()

    result = list_produzioni(session, bucket="active")
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].bucket == "active"
    assert result.items[0].id_dettaglio == 1001


def test_bucket_historical(session):
    session.add(_storica(2001))
    session.flush()

    result = list_produzioni(session, bucket="historical")
    assert result.total == 1
    assert result.items[0].bucket == "historical"
    assert result.items[0].id_dettaglio == 2001


def test_bucket_all_entrambi_presenti(session):
    session.add(_attiva(1001))
    session.add(_storica(2001))
    session.flush()

    result = list_produzioni(session, bucket="all")
    assert result.total == 2
    buckets = {i.bucket for i in result.items}
    assert buckets == {"active", "historical"}


def test_ordine_attive_prima_storiche_in_all(session):
    session.add(_attiva(1001))
    session.add(_attiva(1002))
    session.add(_storica(2001))
    session.flush()

    items = _items(session, bucket="all")
    assert items[0].bucket == "active"
    assert items[1].bucket == "active"
    assert items[2].bucket == "historical"


def test_default_bucket_e_active(session):
    """Senza specificare bucket, il default e 'active' (TASK-V2-034)."""
    session.add(_attiva(1001))
    session.add(_storica(2001))
    session.flush()

    result = list_produzioni(session)
    assert result.total == 1
    assert result.items[0].bucket == "active"


def test_bucket_active_esclude_storiche(session):
    session.add(_attiva(1001))
    session.add(_storica(2001))
    session.flush()

    result = list_produzioni(session, bucket="active")
    assert result.total == 1
    assert all(i.bucket == "active" for i in result.items)


def test_bucket_historical_esclude_attive(session):
    session.add(_attiva(1001))
    session.add(_storica(2001))
    session.flush()

    result = list_produzioni(session, bucket="historical")
    assert result.total == 1
    assert all(i.bucket == "historical" for i in result.items)


def test_bucket_non_valido_raises(session):
    with pytest.raises(ValueError, match="Bucket non valido"):
        list_produzioni(session, bucket="unknown")


# ─── Stato produzione (regola standard) ───────────────────────────────────────

def test_stato_attiva_quando_qtev_minore(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("50")))
    session.flush()

    item = _items(session, bucket="active")[0]
    assert item.stato_produzione == "attiva"


def test_stato_completata_quando_qtev_uguale(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("100")))
    session.flush()

    item = _items(session, bucket="active")[0]
    assert item.stato_produzione == "completata"


def test_stato_completata_quando_qtev_maggiore(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("120")))
    session.flush()

    item = _items(session, bucket="active")[0]
    assert item.stato_produzione == "completata"


def test_stato_attiva_quando_quantita_none(session):
    obj = _attiva(1001, qtor=None, qtev=None)
    session.add(obj)
    session.flush()

    item = _items(session, bucket="active")[0]
    assert item.stato_produzione == "attiva"


def test_stato_storica_completata_per_default(session):
    session.add(_storica(2001, qtor=Decimal("100"), qtev=Decimal("100")))
    session.flush()

    item = _items(session, bucket="historical")[0]
    assert item.stato_produzione == "completata"


# ─── Override forza_completata ────────────────────────────────────────────────

def test_forza_completata_default_false(session):
    session.add(_attiva(1001))
    session.flush()

    item = _items(session, bucket="active")[0]
    assert item.forza_completata is False


def test_forza_completata_override_attiva(session):
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.flush()

    updated = set_forza_completata(session, 1001, "active", True)
    assert updated.forza_completata is True
    assert updated.stato_produzione == "completata"


def test_forza_completata_precedenza_su_quantita(session):
    """Con forza_completata=True, stato=completata anche se qtev < qtor."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    items = _items(session, bucket="active")
    assert items[0].stato_produzione == "completata"


def test_forza_completata_reset_a_false(session):
    """Reimpostare forza_completata=False ripristina la regola standard."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    set_forza_completata(session, 1001, "active", False)
    items = _items(session, bucket="active")
    assert items[0].stato_produzione == "attiva"
    assert items[0].forza_completata is False


def test_forza_completata_su_storica(session):
    session.add(_storica(2001, qtor=Decimal("100"), qtev=Decimal("50")))
    session.flush()

    updated = set_forza_completata(session, 2001, "historical", True)
    assert updated.bucket == "historical"
    assert updated.stato_produzione == "completata"


def test_forza_completata_record_inesistente_raises(session):
    with pytest.raises(ValueError, match="non trovata"):
        set_forza_completata(session, 9999, "active", True)


def test_forza_completata_bucket_non_valido_raises(session):
    with pytest.raises(ValueError, match="Bucket non valido"):
        set_forza_completata(session, 1001, "wrong", True)


def test_forza_completata_non_confonde_bucket(session):
    """Override su 'active' non altera la stessa id_dettaglio in 'historical'."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.add(_storica(1001, qtor=Decimal("100"), qtev=Decimal("0")))
    session.flush()

    set_forza_completata(session, 1001, "active", True)
    items_a = _items(session, bucket="active")
    items_s = _items(session, bucket="historical")

    assert items_a[0].forza_completata is True
    assert items_a[0].stato_produzione == "completata"
    assert items_s[0].forza_completata is False
    assert items_s[0].stato_produzione == "attiva"


# ─── Filtra inattivi ──────────────────────────────────────────────────────────

def test_inattivi_esclusi_dalla_lista(session):
    obj = _attiva(1001)
    obj.attivo = False
    session.add(obj)
    obj2 = _storica(2001)
    obj2.attivo = False
    session.add(obj2)
    session.flush()

    assert list_produzioni(session, bucket="active").total == 0
    assert list_produzioni(session, bucket="historical").total == 0
    assert list_produzioni(session, bucket="all").total == 0


# ─── Paginazione (TASK-V2-034) ────────────────────────────────────────────────

def test_paginazione_limit(session):
    for i in range(1, 6):
        session.add(_attiva(1000 + i))
    session.flush()

    result = list_produzioni(session, bucket="active", limit=3, offset=0)
    assert result.total == 5
    assert len(result.items) == 3
    assert result.limit == 3
    assert result.offset == 0


def test_paginazione_offset(session):
    for i in range(1, 6):
        session.add(_attiva(1000 + i))
    session.flush()

    result = list_produzioni(session, bucket="active", limit=3, offset=3)
    assert result.total == 5
    assert len(result.items) == 2  # solo 2 rimasti


def test_paginazione_offset_oltre_totale(session):
    session.add(_attiva(1001))
    session.flush()

    result = list_produzioni(session, bucket="active", limit=10, offset=999)
    assert result.total == 1
    assert len(result.items) == 0


def test_paginazione_all_attraversa_buckets(session):
    """Con bucket='all' e offset oltre le attive, si passano alle storiche."""
    for i in range(1, 4):
        session.add(_attiva(1000 + i))
    for i in range(1, 4):
        session.add(_storica(2000 + i))
    session.flush()

    # Prendi solo le ultime 2 attive e le prime 2 storiche (offset=1, limit=4)
    result = list_produzioni(session, bucket="all", limit=4, offset=1)
    assert result.total == 6
    assert len(result.items) == 4
    # Le prime 2 sono attive (offset=1 su 3 attive → 2 attive rimanenti)
    assert result.items[0].bucket == "active"
    assert result.items[1].bucket == "active"
    # Le successive 2 sono storiche
    assert result.items[2].bucket == "historical"
    assert result.items[3].bucket == "historical"


def test_paginazione_all_solo_storiche(session):
    """Con offset >= count_attive, si saltano tutte le attive e si leggono le storiche."""
    for i in range(1, 3):
        session.add(_attiva(1000 + i))
    for i in range(1, 4):
        session.add(_storica(2000 + i))
    session.flush()

    result = list_produzioni(session, bucket="all", limit=10, offset=2)
    assert result.total == 5
    assert all(i.bucket == "historical" for i in result.items)
    assert len(result.items) == 3


def test_limit_clampato_a_max(session):
    session.add(_attiva(1001))
    session.flush()

    # limit > MAX_LIMIT (200) viene clampato
    result = list_produzioni(session, bucket="active", limit=9999)
    assert result.limit == 200


# ─── Filtro stato e ricerca (TASK-V2-035) ────────────────────────────────────

def test_filtro_stato_attiva(session):
    """stato=attiva restituisce solo le produzioni non completate."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("50")))   # attiva
    session.add(_attiva(1002, qtor=Decimal("100"), qtev=Decimal("100")))  # completata
    session.flush()

    items = _items(session, bucket="active", stato="attiva")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1001
    assert items[0].stato_produzione == "attiva"


def test_filtro_stato_completata(session):
    """stato=completata restituisce solo le produzioni completate per quantita."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("50")))   # attiva
    session.add(_attiva(1002, qtor=Decimal("100"), qtev=Decimal("100")))  # completata
    session.flush()

    items = _items(session, bucket="active", stato="completata")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1002
    assert items[0].stato_produzione == "completata"


def test_filtro_stato_completata_con_override(session):
    """forza_completata=True deve essere inclusa nel filtro stato=completata."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))  # attiva normale
    session.add(_attiva(1002, qtor=Decimal("100"), qtev=Decimal("10")))  # diventa completata per override
    session.flush()
    set_forza_completata(session, 1002, "active", True)

    items = _items(session, bucket="active", stato="completata")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1002


def test_filtro_stato_attiva_esclude_override_completata(session):
    """Con stato=attiva, le produzioni con forza_completata=True sono escluse."""
    session.add(_attiva(1001, qtor=Decimal("100"), qtev=Decimal("10")))
    session.add(_attiva(1002, qtor=Decimal("100"), qtev=Decimal("10")))
    session.flush()
    set_forza_completata(session, 1002, "active", True)

    items = _items(session, bucket="active", stato="attiva")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1001


def test_filtro_stato_storica(session):
    """Il filtro stato funziona anche su bucket=historical."""
    session.add(_storica(2001, qtor=Decimal("100"), qtev=Decimal("50")))   # attiva
    session.add(_storica(2002, qtor=Decimal("100"), qtev=Decimal("100")))  # completata
    session.flush()

    attive = _items(session, bucket="historical", stato="attiva")
    assert len(attive) == 1
    assert attive[0].id_dettaglio == 2001

    complete = _items(session, bucket="historical", stato="completata")
    assert len(complete) == 1
    assert complete[0].id_dettaglio == 2002


def test_filtro_stato_non_valido_raises(session):
    with pytest.raises(ValueError, match="Stato non valido"):
        list_produzioni(session, stato="unknown")


def test_ricerca_q_codice_articolo(session):
    session.add(_attiva(1001, codice_articolo="ART001"))
    session.add(_attiva(1002, codice_articolo="ART999"))
    session.flush()

    items = _items(session, bucket="active", q="ART001")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1001


def test_ricerca_q_numero_documento(session):
    session.add(_attiva(1001, numero_documento="DOC001"))
    session.add(_attiva(1002, numero_documento="DOC999"))
    session.flush()

    items = _items(session, bucket="active", q="DOC999")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1002


def test_ricerca_q_nessun_match(session):
    session.add(_attiva(1001, codice_articolo="ART001"))
    session.flush()

    items = _items(session, bucket="active", q="ZZZNOMATCH")
    assert len(items) == 0


def test_ricerca_q_case_insensitive(session):
    session.add(_attiva(1001, codice_articolo="ART001"))
    session.flush()

    items = _items(session, bucket="active", q="art001")
    assert len(items) == 1


def test_ricerca_q_parziale(session):
    """La ricerca e parziale (contiene, non esatta)."""
    session.add(_attiva(1001, codice_articolo="ART001"))
    session.add(_attiva(1002, codice_articolo="ART002"))
    session.flush()

    items = _items(session, bucket="active", q="ART")
    assert len(items) == 2


def test_ricerca_e_stato_combinati(session):
    """q e stato si combinano: solo le produzioni che soddisfano entrambi i filtri."""
    session.add(_attiva(1001, codice_articolo="ART001", qtor=Decimal("100"), qtev=Decimal("100")))  # completata, match
    session.add(_attiva(1002, codice_articolo="ART001", qtor=Decimal("100"), qtev=Decimal("10")))   # attiva, match
    session.add(_attiva(1003, codice_articolo="ART999", qtor=Decimal("100"), qtev=Decimal("100")))  # completata, no match
    session.flush()

    items = _items(session, bucket="active", stato="completata", q="ART001")
    assert len(items) == 1
    assert items[0].id_dettaglio == 1001


def test_ricerca_q_stringa_vuota_ignorata(session):
    """Una stringa q vuota o solo spazi non filtra nulla."""
    session.add(_attiva(1001))
    session.add(_attiva(1002))
    session.flush()

    items_empty = _items(session, bucket="active", q="")
    items_spaces = _items(session, bucket="active", q="   ")
    assert len(items_empty) == 2
    assert len(items_spaces) == 2
