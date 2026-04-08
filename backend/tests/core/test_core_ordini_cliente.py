"""
Test di integrazione per il Core slice `ordini_cliente` (TASK-V2-041, DL-ARCH-V2-018).

Verificano:
- formula open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
- valori None trattati come 0 nella formula
- open_qty mai negativo
- set_aside_qty riduce il disponibile aperto
- aggregazione description_lines da righe continues_previous_line=True
- riga principale senza continuation ha description_lines vuota
- piu righe di continuazione accumulate nell'ordine corretto
- le righe di continuazione non compaiono come item autonomi
- regola is_main_destination: customer_destination_progressive vuoto -> True
- mirror vuoto -> lista vuota
- get_order_line: None se non trovata, None se la riga e una continuation
- get_order_lines_by_order: filtrato per ordine, rispetta le continuation
- list_customer_order_lines: ordine corretto (order_reference, line_reference)
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from nssp_v2.core.ordini_cliente.queries import (
    list_customer_order_lines,
    get_order_lines_by_order,
    get_order_line,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_DATE = datetime(2026, 3, 10)
_DELIVERY = datetime(2026, 4, 15)


def _insert(session, order_ref, line_ref, **kwargs):
    """Helper: inserisce direttamente un record in sync_righe_ordine_cliente."""
    from datetime import datetime, timezone
    defaults = dict(
        order_date=_DATE,
        expected_delivery_date=_DELIVERY,
        customer_code="CLI001",
        destination_code="DEST01",
        customer_destination_progressive=None,
        customer_order_reference="REF-001",
        article_code="ART001",
        article_description_segment="Articolo principale",
        article_measure="150x50",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("20.00000"),
        set_aside_qty=Decimal("10.00000"),
        net_unit_price=Decimal("5.50000"),
        continues_previous_line=False,
        synced_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    obj = SyncRigaOrdineCliente(
        order_reference=order_ref,
        line_reference=line_ref,
        **defaults,
    )
    session.add(obj)
    session.flush()
    return obj


# ─── open_qty formula ─────────────────────────────────────────────────────────

def test_open_qty_formula_base(session):
    """open_qty = ordered - set_aside - fulfilled."""
    _insert(session, "ORD001", 1,
            ordered_qty=Decimal("100.00000"),
            fulfilled_qty=Decimal("20.00000"),
            set_aside_qty=Decimal("10.00000"))

    items = list_customer_order_lines(session)
    assert len(items) == 1
    assert items[0].open_qty == Decimal("70.00000")  # 100 - 10 - 20


def test_open_qty_none_trattati_come_zero(session):
    """Valori None in ordered/set_aside/fulfilled trattati come 0."""
    _insert(session, "ORD001", 1,
            ordered_qty=Decimal("50.00000"),
            fulfilled_qty=None,
            set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert items[0].open_qty == Decimal("50.00000")


def test_open_qty_mai_negativo(session):
    """open_qty non puo essere negativo: max con 0."""
    _insert(session, "ORD001", 1,
            ordered_qty=Decimal("10.00000"),
            fulfilled_qty=Decimal("8.00000"),
            set_aside_qty=Decimal("5.00000"))
    # 10 - 5 - 8 = -3 -> 0

    items = list_customer_order_lines(session)
    assert items[0].open_qty == Decimal("0")


def test_open_qty_set_aside_riduce_il_disponibile(session):
    """set_aside_qty (quantita inscatolata) riduce open_qty come fulfilled_qty."""
    _insert(session, "ORD001", 1,
            ordered_qty=Decimal("100.00000"),
            fulfilled_qty=Decimal("0.00000"),
            set_aside_qty=Decimal("30.00000"))

    items = list_customer_order_lines(session)
    assert items[0].open_qty == Decimal("70.00000")


def test_open_qty_tutto_evaso(session):
    """Se fulfilled_qty copre tutto l'ordinato, open_qty e 0."""
    _insert(session, "ORD001", 1,
            ordered_qty=Decimal("50.00000"),
            fulfilled_qty=Decimal("50.00000"),
            set_aside_qty=Decimal("0.00000"))

    items = list_customer_order_lines(session)
    assert items[0].open_qty == Decimal("0")


def test_open_qty_ordered_none(session):
    """Se ordered_qty e None, open_qty e 0 (nessuna domanda)."""
    _insert(session, "ORD001", 1,
            ordered_qty=None,
            fulfilled_qty=None,
            set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert items[0].open_qty == Decimal("0")


# ─── description_lines ────────────────────────────────────────────────────────

def test_riga_senza_continuation_ha_description_lines_vuota(session):
    """Una riga principale senza righe di continuazione ha description_lines=[]."""
    _insert(session, "ORD001", 1, continues_previous_line=False)

    items = list_customer_order_lines(session)
    assert len(items) == 1
    assert items[0].description_lines == []


def test_riga_continuation_aggregata_in_description_lines(session):
    """Una riga COLL_RIGA_PREC=True diventa description_lines della riga principale."""
    _insert(session, "ORD001", 1, continues_previous_line=False,
            article_description_segment="Riga principale")
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_description_segment="Continuazione 1",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert len(items) == 1
    assert items[0].description_lines == ["Continuazione 1"]


def test_piu_righe_continuation_accumulate_in_ordine(session):
    """Piu righe di continuazione consecutive si accumulano in description_lines."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_description_segment="Continua A",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)
    _insert(session, "ORD001", 3, continues_previous_line=True,
            article_description_segment="Continua B",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert len(items) == 1
    assert items[0].description_lines == ["Continua A", "Continua B"]


def test_righe_continuation_non_compaiono_come_item_autonomi(session):
    """Le righe continues_previous_line=True non generano CustomerOrderLineItem propri."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)
    _insert(session, "ORD001", 3, continues_previous_line=True,
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert len(items) == 1  # solo la riga principale


def test_continuation_con_description_segment_none_non_aggiunta(session):
    """Una riga di continuazione con article_description_segment=None non aggiunge nulla."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_description_segment=None,
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = list_customer_order_lines(session)
    assert items[0].description_lines == []


def test_description_lines_non_attraversano_ordini_diversi(session):
    """Le righe di continuazione non attraversano la frontiera tra ordini diversi."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD002", 1, continues_previous_line=True,
            article_description_segment="Descrizione ORD002",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = list_customer_order_lines(session)
    # ORD001/1 non ha description_lines da ORD002
    ord001_item = next(i for i in items if i.order_reference == "ORD001")
    assert ord001_item.description_lines == []


# ─── is_main_destination ──────────────────────────────────────────────────────

def test_is_main_destination_quando_progressivo_vuoto(session):
    """customer_destination_progressive None -> is_main_destination=True."""
    _insert(session, "ORD001", 1, customer_destination_progressive=None)

    items = list_customer_order_lines(session)
    assert items[0].is_main_destination is True


def test_is_main_destination_false_quando_progressivo_valorizzato(session):
    """customer_destination_progressive valorizzato -> is_main_destination=False."""
    _insert(session, "ORD001", 1, customer_destination_progressive="002")

    items = list_customer_order_lines(session)
    assert items[0].is_main_destination is False


# ─── mirror vuoto ─────────────────────────────────────────────────────────────

def test_mirror_vuoto_lista_vuota(session):
    items = list_customer_order_lines(session)
    assert items == []


# ─── get_order_lines_by_order ─────────────────────────────────────────────────

def test_get_order_lines_by_order_filtro_per_ordine(session):
    """Restituisce solo le righe dell'ordine richiesto."""
    _insert(session, "ORD001", 1, article_code="ART001")
    _insert(session, "ORD001", 2, article_code="ART002")
    _insert(session, "ORD002", 1, article_code="ART003")

    items = get_order_lines_by_order(session, "ORD001")
    assert len(items) == 2
    assert all(i.order_reference == "ORD001" for i in items)


def test_get_order_lines_by_order_ordine_inesistente(session):
    items = get_order_lines_by_order(session, "ORDXXX")
    assert items == []


def test_get_order_lines_by_order_include_description_lines(session):
    """Le description_lines vengono costruite correttamente dentro get_order_lines_by_order."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_description_segment="Continua",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    items = get_order_lines_by_order(session, "ORD001")
    assert len(items) == 1
    assert items[0].description_lines == ["Continua"]


# ─── get_order_line ───────────────────────────────────────────────────────────

def test_get_order_line_trovata(session):
    _insert(session, "ORD001", 1, article_code="ART001")

    item = get_order_line(session, "ORD001", 1)
    assert item is not None
    assert item.order_reference == "ORD001"
    assert item.line_reference == 1
    assert item.article_code == "ART001"


def test_get_order_line_non_trovata(session):
    item = get_order_line(session, "ORDXXX", 1)
    assert item is None


def test_get_order_line_continuation_restituisce_none(session):
    """get_order_line su una riga COLL_RIGA_PREC=True restituisce None."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    item = get_order_line(session, "ORD001", 2)
    assert item is None


def test_get_order_line_include_description_lines(session):
    """get_order_line costruisce le description_lines dalle righe successive."""
    _insert(session, "ORD001", 1, continues_previous_line=False)
    _insert(session, "ORD001", 2, continues_previous_line=True,
            article_description_segment="Nota aggiuntiva",
            article_code=None, ordered_qty=None, fulfilled_qty=None, set_aside_qty=None)

    item = get_order_line(session, "ORD001", 1)
    assert item is not None
    assert item.description_lines == ["Nota aggiuntiva"]


# ─── ordinamento e completezza ────────────────────────────────────────────────

def test_list_ordinato_per_ordine_e_progressivo(session):
    """list_customer_order_lines rispetta l'ordine (order_reference, line_reference)."""
    _insert(session, "ORD002", 1, article_code="ART_B")
    _insert(session, "ORD001", 2, article_code="ART_C")
    _insert(session, "ORD001", 1, article_code="ART_A")

    items = list_customer_order_lines(session)
    keys = [(i.order_reference, i.line_reference) for i in items]
    assert keys == [("ORD001", 1), ("ORD001", 2), ("ORD002", 1)]
