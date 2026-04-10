"""
Test del Core slice `planning_candidates` V1 (TASK-V2-062, DL-ARCH-V2-025).

Copertura:
- logica pura (is_planning_candidate_v1, future_availability_v1, required_qty_minimum_v1)
- perimetro articoli: solo codici presenti e attivi in sync_articoli (coerente con criticita)
- candidato generato solo se future_availability_qty < 0
- incoming_supply_qty aggregata correttamente da sync_produzioni_attive
- customer_open_demand_qty aggregata correttamente da sync_righe_ordine_cliente
- articolo coperto dalla supply (future_availability >= 0) non e candidate
- articolo critico ma coperto da supply non e candidate (test chiave: future != criticita)
- ordinamento crescente per future_availability_qty
- required_qty_minimum = abs(future_availability_qty)
- tabella vuota -> lista vuota
- mismatch casing tra canonical e raw (UPPER join)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nssp_v2.shared.db import Base
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.core.planning_candidates.logic import (
    PlanningContext,
    future_availability_v1,
    is_planning_candidate_v1,
    required_qty_minimum_v1,
)
from nssp_v2.core.planning_candidates.queries import list_planning_candidates_v1

# Importati per registrare tutti i modelli in Base.metadata prima di create_all
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig  # noqa: F401
from nssp_v2.core.commitments.models import CoreCommitment  # noqa: F401
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside  # noqa: F401
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition  # noqa: F401
from nssp_v2.core.produzioni.models import CoreProduzioneOverride  # noqa: F401
from nssp_v2.sync.articoli.models import SyncArticolo  # noqa: F401
from nssp_v2.sync.mag_reale.models import SyncMagReale  # noqa: F401
from nssp_v2.sync.produzioni_attive.models import SyncProduzioneAttiva  # noqa: F401
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente  # noqa: F401
from nssp_v2.sync.produzioni_storiche.models import SyncProduzioneStorica  # noqa: F401


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


_NOW = datetime.now(timezone.utc)


# ─── Helper ───────────────────────────────────────────────────────────────────

_id_dettaglio_counter = 0
_riga_counter = 0


def _next_id() -> int:
    global _id_dettaglio_counter
    _id_dettaglio_counter += 1
    return _id_dettaglio_counter


def _next_riga() -> int:
    global _riga_counter
    _riga_counter += 1
    return _riga_counter


def _avail(session, article_code, availability_qty, inventory_qty=Decimal("0"),
           set_aside_qty=Decimal("0"), committed_qty=Decimal("0")):
    session.add(CoreAvailability(
        article_code=article_code,
        inventory_qty=inventory_qty,
        customer_set_aside_qty=set_aside_qty,
        committed_qty=committed_qty,
        availability_qty=availability_qty,
        computed_at=_NOW,
    ))
    session.flush()


def _art(session, codice_articolo, attivo=True):
    session.add(SyncArticolo(
        codice_articolo=codice_articolo,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _produzione(session, codice_articolo, quantita_ordinata, quantita_prodotta=None, attivo=True):
    session.add(SyncProduzioneAttiva(
        id_dettaglio=_next_id(),
        codice_articolo=codice_articolo,
        quantita_ordinata=quantita_ordinata,
        quantita_prodotta=quantita_prodotta,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.flush()


def _riga_ordine(session, article_code, ordered_qty, set_aside_qty=None, fulfilled_qty=None,
                 order_ref=None, continues_previous_line=None):
    nr = _next_riga()
    session.add(SyncRigaOrdineCliente(
        order_reference=order_ref or f"ORD{nr:04d}",
        line_reference=nr,
        article_code=article_code,
        ordered_qty=ordered_qty,
        set_aside_qty=set_aside_qty,
        fulfilled_qty=fulfilled_qty,
        continues_previous_line=continues_previous_line,
        synced_at=_NOW,
    ))
    session.flush()


# ─── Test logica pura ─────────────────────────────────────────────────────────

class TestLogicaPura:

    def test_future_availability_somma_incoming(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("-5"),
            incoming_supply_qty=Decimal("3"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert future_availability_v1(ctx) == Decimal("-2")

    def test_future_availability_none_se_availability_none(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=None,
            incoming_supply_qty=Decimal("10"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert future_availability_v1(ctx) is None

    def test_future_availability_coperto_da_supply(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("-5"),
            incoming_supply_qty=Decimal("10"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert future_availability_v1(ctx) == Decimal("5")

    def test_is_candidate_future_negativa(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("-5"),
            incoming_supply_qty=Decimal("2"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert is_planning_candidate_v1(ctx) is True

    def test_is_candidate_false_se_coperto_da_supply(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("-5"),
            incoming_supply_qty=Decimal("10"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert is_planning_candidate_v1(ctx) is False

    def test_is_candidate_false_se_future_zero(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("-5"),
            incoming_supply_qty=Decimal("5"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert is_planning_candidate_v1(ctx) is False

    def test_is_candidate_false_se_availability_none(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=None,
            incoming_supply_qty=Decimal("0"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert is_planning_candidate_v1(ctx) is False

    def test_is_candidate_false_se_availability_positiva_con_supply(self):
        ctx = PlanningContext(
            article_code="ART",
            availability_qty=Decimal("10"),
            incoming_supply_qty=Decimal("5"),
            customer_open_demand_qty=Decimal("0"),
        )
        assert is_planning_candidate_v1(ctx) is False

    def test_required_qty_quando_negativa(self):
        assert required_qty_minimum_v1(Decimal("-7")) == Decimal("7")

    def test_required_qty_zero_quando_positiva(self):
        assert required_qty_minimum_v1(Decimal("3")) == Decimal("0")

    def test_required_qty_zero_quando_zero(self):
        assert required_qty_minimum_v1(Decimal("0")) == Decimal("0")

    def test_required_qty_zero_quando_none(self):
        assert required_qty_minimum_v1(None) == Decimal("0")


# ─── Test perimetro articoli ───────────────────────────────────────────────────

class TestPerimetroArticoli:

    def test_orfano_assente_da_sync_articoli_escluso(self, session):
        """Codice con availability negativa ma assente da sync_articoli: escluso."""
        _avail(session, "ART001", Decimal("-5"))
        # nessun _art: ART001 non e in sync_articoli

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_orfano_non_attivo_escluso(self, session):
        """Codice con availability negativa ma attivo=False in sync_articoli: escluso."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001", attivo=False)

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_articolo_attivo_senza_supply_e_candidate(self, session):
        """Articolo attivo con availability negativa e nessuna supply: e candidate."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].article_code == "ART001"

    def test_tabella_vuota_restituisce_lista_vuota(self, session):
        result = list_planning_candidates_v1(session)
        assert result == []


# ─── Test logica candidate: future_availability ───────────────────────────────

class TestLogicaCandidate:

    def test_articolo_critico_coperto_da_supply_non_e_candidate(self, session):
        """
        Caso chiave: l'articolo e critico (availability < 0) ma la supply lo copre.
        Deve NON essere candidate (future_availability >= 0).
        Dimostra la differenza tra criticita e planning candidates.
        """
        _avail(session, "ART001", Decimal("-3"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("10"), quantita_prodotta=Decimal("5"))
        # incoming = 10 - 5 = 5 -> future = -3 + 5 = +2 -> non candidate

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_articolo_critico_parzialmente_coperto_e_candidate(self, session):
        """Availability -10, incoming 3 -> future -7 -> candidate."""
        _avail(session, "ART001", Decimal("-10"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("5"), quantita_prodotta=Decimal("2"))
        # incoming = 5 - 2 = 3 -> future = -10 + 3 = -7

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        c = result[0]
        assert c.article_code == "ART001"
        assert c.availability_qty == Decimal("-10")
        assert c.incoming_supply_qty == Decimal("3")
        assert c.future_availability_qty == Decimal("-7")
        assert c.required_qty_minimum == Decimal("7")

    def test_articolo_positivo_con_supply_non_e_candidate(self, session):
        """Articolo con availability positiva: mai candidate."""
        _avail(session, "ART001", Decimal("5"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("10"))

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_supply_zero_quando_produzione_non_attiva(self, session):
        """Produzione con attivo=False non contribuisce a incoming_supply."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("10"), attivo=False)
        # incoming = 0 -> future = -5 -> candidate

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("0")

    def test_supply_zero_quando_produzione_completata_per_quantita(self, session):
        """Produzione con quantita_prodotta >= quantita_ordinata: remaining = 0."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("10"), quantita_prodotta=Decimal("10"))
        # remaining = max(10-10, 0) = 0 -> incoming = 0 -> future = -5 -> candidate

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("0")
        assert result[0].future_availability_qty == Decimal("-5")


# ─── Test aggregazione incoming_supply ───────────────────────────────────────

class TestIncomingSupply:

    def test_supply_aggregata_da_piu_produzioni(self, session):
        """Piu produzioni per lo stesso articolo: incoming = somma dei remaining."""
        _avail(session, "ART001", Decimal("-20"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("8"), quantita_prodotta=Decimal("3"))
        _produzione(session, "ART001", quantita_ordinata=Decimal("6"), quantita_prodotta=None)
        # incoming = (8-3) + (6-0) = 5 + 6 = 11 -> future = -20 + 11 = -9

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("11")
        assert result[0].future_availability_qty == Decimal("-9")

    def test_supply_senza_quantita_prodotta(self, session):
        """Produzione con quantita_prodotta=None: remaining = quantita_ordinata."""
        _avail(session, "ART001", Decimal("-10"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("4"), quantita_prodotta=None)
        # incoming = 4 -> future = -10 + 4 = -6

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("4")

    def test_supply_non_negativa_se_sovra_prodotta(self, session):
        """Produzione con quantita_prodotta > quantita_ordinata: remaining clampato a 0."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("5"), quantita_prodotta=Decimal("8"))
        # remaining = max(5-8, 0) = 0 -> incoming = 0 -> future = -5

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("0")


# ─── Test aggregazione customer_open_demand ───────────────────────────────────

class TestCustomerDemand:

    def test_demand_aggregata_da_piu_righe(self, session):
        """Piu righe ordine per lo stesso articolo: demand = somma open_qty."""
        _avail(session, "ART001", Decimal("-30"))
        _art(session, "ART001")
        _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))
        _riga_ordine(session, "ART001", ordered_qty=Decimal("15"), fulfilled_qty=Decimal("5"))
        # demand = 10 + (15-5) = 10 + 10 = 20

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].customer_open_demand_qty == Decimal("20")

    def test_demand_con_set_aside(self, session):
        """open_qty = ordered - set_aside - fulfilled."""
        _avail(session, "ART001", Decimal("-20"))
        _art(session, "ART001")
        _riga_ordine(session, "ART001",
                     ordered_qty=Decimal("20"),
                     set_aside_qty=Decimal("5"),
                     fulfilled_qty=Decimal("3"))
        # demand = max(20 - 5 - 3, 0) = 12

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].customer_open_demand_qty == Decimal("12")

    def test_demand_zero_se_fully_fulfilled(self, session):
        """Riga completamente evasa: open_qty = 0, demand = 0."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        _riga_ordine(session, "ART001",
                     ordered_qty=Decimal("10"),
                     fulfilled_qty=Decimal("10"))
        # demand = max(10-0-10, 0) = 0

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].customer_open_demand_qty == Decimal("0")

    def test_demand_zero_se_nessuna_riga(self, session):
        """Nessuna riga ordine per l'articolo: demand = 0, ma candidate se future < 0."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        # nessuna riga ordine

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].customer_open_demand_qty == Decimal("0")


# ─── Test ordinamento e campi ─────────────────────────────────────────────────

class TestOrdinamentoECampi:

    def test_ordinamento_crescente_per_future_availability(self, session):
        """Candidate ordinati per future_availability_qty crescente (peggiori sopra)."""
        _avail(session, "ART001", Decimal("-2"))
        _art(session, "ART001")
        _avail(session, "ART002", Decimal("-10"))
        _art(session, "ART002")
        _avail(session, "ART003", Decimal("-5"))
        _art(session, "ART003")

        result = list_planning_candidates_v1(session)
        assert len(result) == 3
        assert result[0].article_code == "ART002"  # -10
        assert result[1].article_code == "ART003"  # -5
        assert result[2].article_code == "ART001"  # -2

    def test_campi_read_model_corretti(self, session):
        """Verifica tutti i campi del read model per un candidate."""
        _avail(session, "ART001", Decimal("-7"),
               inventory_qty=Decimal("3"),
               set_aside_qty=Decimal("2"),
               committed_qty=Decimal("8"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("4"), quantita_prodotta=Decimal("1"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        c = result[0]

        assert c.article_code == "ART001"
        assert c.availability_qty == Decimal("-7")
        assert c.incoming_supply_qty == Decimal("3")   # 4-1
        assert c.future_availability_qty == Decimal("-4")  # -7+3
        assert c.required_qty_minimum == Decimal("4")
        assert c.computed_at == _NOW.replace(tzinfo=None)

    def test_required_qty_minimum_e_abs_future(self, session):
        """required_qty_minimum = abs(future_availability_qty)."""
        _avail(session, "ART001", Decimal("-15"))
        _art(session, "ART001")
        _produzione(session, "ART001", quantita_ordinata=Decimal("8"))
        # future = -15 + 8 = -7 -> required = 7

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].required_qty_minimum == Decimal("7")


# ─── Test mismatch casing (cross-source join) ─────────────────────────────────

class TestCasingMismatch:

    def test_canonical_upper_con_sync_lowercase(self, session):
        """
        CoreAvailability usa canonical UPPER ('8X7X160').
        SyncArticolo puo avere raw lowercase ('8x7x160').
        Il UPPER join deve trovare la corrispondenza.
        """
        _avail(session, "8X7X160", Decimal("-5"))
        _art(session, "8x7x160")  # raw lowercase

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].article_code == "8X7X160"

    def test_produzione_codice_lowercase_aggregata_correttamente(self, session):
        """
        Produzione con codice_articolo raw lowercase: incoming aggregato sotto canonical UPPER.
        """
        _avail(session, "8X7X160", Decimal("-10"))
        _art(session, "8x7x160")
        _produzione(session, "8x7x160", quantita_ordinata=Decimal("4"))
        # incoming per "8X7X160" deve trovare la produzione con codice raw "8x7x160"

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("4")
        assert result[0].future_availability_qty == Decimal("-6")

    def test_riga_ordine_codice_lowercase_aggregata_correttamente(self, session):
        """
        Riga ordine con article_code raw lowercase: demand aggregata sotto canonical UPPER.
        """
        _avail(session, "8X7X160", Decimal("-10"))
        _art(session, "8x7x160")
        _riga_ordine(session, "8x7x160", ordered_qty=Decimal("5"))
        # demand per "8X7X160" deve trovare la riga con codice raw "8x7x160"

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].customer_open_demand_qty == Decimal("5")
