"""
Test del Core slice `planning_candidates` V2 (TASK-V2-062, TASK-V2-068, TASK-V2-071, DL-ARCH-V2-025, DL-ARCH-V2-027).

Copertura:
- logica pura by_article (is_planning_candidate_v1, future_availability_v1, required_qty_minimum_v1)
- logica pura by_customer_order_line (is_planning_candidate_by_order_line, line_future_coverage_v2, required_qty_minimum_by_order_line)
- perimetro articoli: solo codici presenti e attivi in sync_articoli
- candidato by_article generato solo se future_availability_qty < 0
- candidato by_customer_order_line generato solo se line_future_coverage_qty < 0
- branching corretto: articoli by_article vs by_customer_order_line
- incoming_supply_qty aggregata correttamente per by_article
- linked_incoming_supply_qty collegata per riga ordine per by_customer_order_line
- forza_completata esclude la produzione dalla supply in entrambe le modalita (TASK-V2-068)
- ordinamento finale: required_qty_minimum decrescente (merge dei due rami)
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
    PlanningContextOrderLine,
    future_availability_v1,
    is_planning_candidate_v1,
    is_planning_candidate_by_order_line,
    line_future_coverage_v2,
    required_qty_minimum_v1,
    required_qty_minimum_by_order_line,
)
from nssp_v2.core.planning_candidates.queries import list_planning_candidates_v1

# Importati per registrare tutti i modelli in Base.metadata prima di create_all
from nssp_v2.core.articoli.models import ArticoloFamiglia, CoreArticoloConfig
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


def _avail(session, article_code, availability_qty, inventory_qty=None,
           set_aside_qty=Decimal("0"), committed_qty=None):
    """Inserisce una riga CoreAvailability in modo semanticamente consistente.

    Convenzione default (DL-ARCH-V2-028 §1):
    - Se inventory_qty non e specificato e committed_qty non e specificato:
      - la domanda aperta (committed) e la causa della disponibilita negativa
        → committed_qty = max(-availability_qty, 0), inventory_qty = 0
      - questo rappresenta il caso reale: stock=0, domanda=N, availability=-N
    - Per testare anomalie inventariali (giacenza fisica negativa senza domanda):
      specificare esplicitamente inventory_qty negativo e committed_qty=0
    """
    if inventory_qty is None and committed_qty is None:
        # Scenario default: disponibilita negativa = domanda che eccede lo stock
        committed_qty = max(-availability_qty, Decimal("0"))
        inventory_qty = Decimal("0")
    elif inventory_qty is None:
        inventory_qty = Decimal("0")
    elif committed_qty is None:
        committed_qty = Decimal("0")

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
    return order_ref or f"ORD{nr:04d}", nr


def _produzione_collegata(
    session,
    codice_articolo,
    quantita_ordinata,
    riferimento_numero_ordine_cliente,
    riferimento_riga_ordine_cliente,
    quantita_prodotta=None,
    attivo=True,
    forza_completata=False,
):
    """Produzione collegata a una riga ordine cliente (per test by_customer_order_line)."""
    id_det = _next_id()
    session.add(SyncProduzioneAttiva(
        id_dettaglio=id_det,
        codice_articolo=codice_articolo,
        quantita_ordinata=quantita_ordinata,
        quantita_prodotta=quantita_prodotta,
        riferimento_numero_ordine_cliente=riferimento_numero_ordine_cliente,
        riferimento_riga_ordine_cliente=Decimal(str(riferimento_riga_ordine_cliente)),
        attivo=attivo,
        synced_at=_NOW,
    ))
    if forza_completata:
        session.add(CoreProduzioneOverride(
            id_dettaglio=id_det,
            bucket="active",
            forza_completata=True,
        ))
    session.flush()
    return id_det


def _art_col(session, codice_articolo, attivo=True):
    """Crea articolo con planning_mode=by_customer_order_line via override diretto."""
    session.add(SyncArticolo(
        codice_articolo=codice_articolo,
        attivo=attivo,
        synced_at=_NOW,
    ))
    session.add(CoreArticoloConfig(
        codice_articolo=codice_articolo,
        famiglia_code=None,
        updated_at=_NOW,
        override_considera_in_produzione=True,
        override_aggrega_codice_in_produzione=False,  # → by_customer_order_line
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


# ─── Test forza_completata (TASK-V2-068) ──────────────────────────────────────

class TestForzaCompletata:
    """Verifica che le produzioni con forza_completata=True vengano escluse dalla supply.

    Copre il limite V1 superato in TASK-V2-068:
    precedentemente forza_completata non impattava incoming_supply_qty.
    """

    def _produzione_con_override(
        self,
        session,
        codice_articolo: str,
        quantita_ordinata,
        quantita_prodotta=None,
        forza_completata: bool = False,
    ) -> int:
        """Crea una produzione attiva con eventuale override forza_completata."""
        id_det = _next_id()
        session.add(SyncProduzioneAttiva(
            id_dettaglio=id_det,
            codice_articolo=codice_articolo,
            quantita_ordinata=quantita_ordinata,
            quantita_prodotta=quantita_prodotta,
            attivo=True,
            synced_at=_NOW,
        ))
        if forza_completata:
            session.add(CoreProduzioneOverride(
                id_dettaglio=id_det,
                bucket="active",
                forza_completata=True,
            ))
        session.flush()
        return id_det

    def test_forza_completata_esclusa_da_supply(self, session):
        """Produzione attiva ma con forza_completata=True: non contribuisce a incoming_supply."""
        _avail(session, "ART001", Decimal("-10"))
        _art(session, "ART001")
        # produzione con quantita rimanente = 8, ma forzata completata
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("10"),
            quantita_prodotta=Decimal("2"),
            forza_completata=True,
        )
        # incoming deve essere 0, non 8

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("0")
        assert result[0].future_availability_qty == Decimal("-10")

    def test_forza_completata_false_inclusa_nella_supply(self, session):
        """Override con forza_completata=False: la produzione contribuisce normalmente."""
        _avail(session, "ART001", Decimal("-10"))
        _art(session, "ART001")
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("6"),
            quantita_prodotta=Decimal("1"),
            forza_completata=False,
        )
        # incoming = 6 - 1 = 5 -> future = -10 + 5 = -5

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("5")
        assert result[0].future_availability_qty == Decimal("-5")

    def test_senza_override_inclusa_nella_supply(self, session):
        """Produzione senza override (None in core_produzione_override): inclusa normalmente."""
        _avail(session, "ART001", Decimal("-8"))
        _art(session, "ART001")
        # nessun override -> left join restituisce NULL -> inclusa
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("5"),
            quantita_prodotta=Decimal("2"),
            forza_completata=False,  # record override non creato, solo non lo impostiamo
        )
        # incoming = 3 -> future = -8 + 3 = -5

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("3")

    def test_mix_forza_completata_e_attiva(self, session):
        """Due produzioni: una con forza_completata=True, una senza. Solo la seconda contribuisce."""
        _avail(session, "ART001", Decimal("-15"))
        _art(session, "ART001")
        # produzione 1: forza_completata=True, remaining = 7 -> esclusa
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("10"),
            quantita_prodotta=Decimal("3"),
            forza_completata=True,
        )
        # produzione 2: nessun override, remaining = 4 -> inclusa
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("6"),
            quantita_prodotta=Decimal("2"),
            forza_completata=False,
        )
        # incoming = 4 (solo la seconda) -> future = -15 + 4 = -11

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("4")
        assert result[0].future_availability_qty == Decimal("-11")

    def test_forza_completata_scopre_candidate_nascosto(self, session):
        """
        Scenario critico: con forza_completata non considerata, l'articolo sembrerebbe coperto.
        Con il fix (TASK-V2-068), la produzione forzata e esclusa e l'articolo diventa candidate.
        """
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        # supply che coprirerebbe la criticita, ma e forzata completata
        self._produzione_con_override(
            session, "ART001",
            quantita_ordinata=Decimal("8"),
            quantita_prodotta=Decimal("0"),
            forza_completata=True,
        )
        # Senza fix: incoming = 8 -> future = -5 + 8 = +3 -> non candidate (errato)
        # Con fix: incoming = 0 -> future = -5 + 0 = -5 -> candidate (corretto)

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].incoming_supply_qty == Decimal("0")
        assert result[0].future_availability_qty == Decimal("-5")
        assert result[0].required_qty_minimum == Decimal("5")


# ─── Test logica pura by_customer_order_line (TASK-V2-071) ───────────────────

class TestLogicaPuraOrderLine:
    """Logica pura del ramo by_customer_order_line."""

    def test_coverage_positiva_se_supply_copre(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("5"),
            linked_incoming_supply_qty=Decimal("8"),
        )
        assert line_future_coverage_v2(ctx) == Decimal("3")

    def test_coverage_negativa_se_supply_insufficiente(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("10"),
            linked_incoming_supply_qty=Decimal("3"),
        )
        assert line_future_coverage_v2(ctx) == Decimal("-7")

    def test_coverage_zero_se_supply_uguale_demand(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("5"),
            linked_incoming_supply_qty=Decimal("5"),
        )
        assert line_future_coverage_v2(ctx) == Decimal("0")

    def test_is_candidate_quando_negativa(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("10"),
            linked_incoming_supply_qty=Decimal("3"),
        )
        assert is_planning_candidate_by_order_line(ctx) is True

    def test_non_candidate_se_coperta(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("5"),
            linked_incoming_supply_qty=Decimal("8"),
        )
        assert is_planning_candidate_by_order_line(ctx) is False

    def test_non_candidate_se_zero(self):
        ctx = PlanningContextOrderLine(
            article_code="ART",
            order_reference="ORD001",
            line_reference=1,
            line_open_demand_qty=Decimal("5"),
            linked_incoming_supply_qty=Decimal("5"),
        )
        assert is_planning_candidate_by_order_line(ctx) is False

    def test_required_qty_minimum_quando_negativa(self):
        assert required_qty_minimum_by_order_line(Decimal("-7")) == Decimal("7")

    def test_required_qty_minimum_zero_se_positiva(self):
        assert required_qty_minimum_by_order_line(Decimal("3")) == Decimal("0")

    def test_required_qty_minimum_zero_se_zero(self):
        assert required_qty_minimum_by_order_line(Decimal("0")) == Decimal("0")


# ─── Test branching by_customer_order_line (TASK-V2-071) ─────────────────────

class TestByCustomerOrderLine:
    """Verifica il ramo by_customer_order_line della query principale.

    Un articolo con planning_mode=by_customer_order_line non usa core_availability.
    La candidatura e per riga ordine: candidate se linked_supply < line_demand.
    """

    def test_riga_non_coperta_da_supply_e_candidate(self, session):
        """Riga ordine con demand > 0 e nessuna produzione collegata: candidate."""
        _art_col(session, "ART001")
        order_ref, line_ref = _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        c = result[0]
        assert c.article_code == "ART001"
        assert c.planning_mode == "by_customer_order_line"
        assert c.order_reference == order_ref
        assert c.line_reference == line_ref
        assert c.line_open_demand_qty == Decimal("10")
        assert c.linked_incoming_supply_qty == Decimal("0")
        assert c.line_future_coverage_qty == Decimal("-10")
        assert c.required_qty_minimum == Decimal("10")
        assert c.availability_qty is None
        assert c.future_availability_qty is None

    def test_riga_coperta_da_supply_collegata_non_e_candidate(self, session):
        """Riga ordine con produzione collegata che copre tutta la domanda: non candidate."""
        _art_col(session, "ART001")
        order_ref, line_ref = _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))
        _produzione_collegata(
            session, "ART001",
            quantita_ordinata=Decimal("10"),
            riferimento_numero_ordine_cliente=order_ref,
            riferimento_riga_ordine_cliente=line_ref,
        )

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_riga_parzialmente_coperta_e_candidate(self, session):
        """Riga con supply parziale: required = abs(line_future_coverage_qty)."""
        _art_col(session, "ART001")
        order_ref, line_ref = _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))
        _produzione_collegata(
            session, "ART001",
            quantita_ordinata=Decimal("4"),
            riferimento_numero_ordine_cliente=order_ref,
            riferimento_riga_ordine_cliente=line_ref,
        )

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        c = result[0]
        assert c.linked_incoming_supply_qty == Decimal("4")
        assert c.line_future_coverage_qty == Decimal("-6")
        assert c.required_qty_minimum == Decimal("6")

    def test_riga_demand_zero_non_genera_candidate(self, session):
        """Riga completamente evasa (demand = 0): non candidate."""
        _art_col(session, "ART001")
        _riga_ordine(session, "ART001",
                     ordered_qty=Decimal("10"),
                     fulfilled_qty=Decimal("10"))

        result = list_planning_candidates_v1(session)
        assert result == []

    def test_forza_completata_esclusa_da_linked_supply(self, session):
        """Produzione collegata con forza_completata=True non contribuisce alla supply."""
        _art_col(session, "ART001")
        order_ref, line_ref = _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))
        _produzione_collegata(
            session, "ART001",
            quantita_ordinata=Decimal("10"),
            riferimento_numero_ordine_cliente=order_ref,
            riferimento_riga_ordine_cliente=line_ref,
            forza_completata=True,
        )

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].linked_incoming_supply_qty == Decimal("0")
        assert result[0].required_qty_minimum == Decimal("10")

    def test_supply_non_collegata_non_conta(self, session):
        """Produzione per lo stesso articolo senza riferimento ordine: non conta."""
        _art_col(session, "ART001")
        order_ref, line_ref = _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))
        session.add(SyncProduzioneAttiva(
            id_dettaglio=_next_id(),
            codice_articolo="ART001",
            quantita_ordinata=Decimal("20"),
            attivo=True,
            synced_at=_NOW,
        ))
        session.flush()

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].linked_incoming_supply_qty == Decimal("0")

    def test_articolo_col_senza_core_availability_genera_candidate(self, session):
        """Articolo by_customer_order_line non usa core_availability."""
        _art_col(session, "ART001")
        _riga_ordine(session, "ART001", ordered_qty=Decimal("5"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].planning_mode == "by_customer_order_line"

    def test_branching_mix_by_article_e_by_customer_order_line(self, session):
        """Mix: ART001 by_article (None), ART002 by_customer_order_line."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")

        _art_col(session, "ART002")
        _riga_ordine(session, "ART002", ordered_qty=Decimal("8"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 2

        by_art = next(c for c in result if c.article_code == "ART001")
        by_col = next(c for c in result if c.article_code == "ART002")

        assert by_art.planning_mode is None
        assert by_art.future_availability_qty == Decimal("-5")
        assert by_art.order_reference is None

        assert by_col.planning_mode == "by_customer_order_line"
        assert by_col.line_open_demand_qty == Decimal("8")
        assert by_col.availability_qty is None

    def test_articolo_by_article_non_genera_candidati_per_riga(self, session):
        """Articolo by_article con riga ordine: genera UN candidato by_article, non uno per riga."""
        _avail(session, "ART001", Decimal("-5"))
        _art(session, "ART001")
        _riga_ordine(session, "ART001", ordered_qty=Decimal("10"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 1
        assert result[0].planning_mode is None
        assert result[0].order_reference is None
        assert result[0].customer_open_demand_qty == Decimal("10")

    def test_piu_righe_stesso_articolo_col_generano_candidati_separati(self, session):
        """Due righe ordine per stesso articolo by_customer_order_line: due candidati."""
        _art_col(session, "ART001")
        ref1, lr1 = _riga_ordine(session, "ART001", ordered_qty=Decimal("5"))
        ref2, lr2 = _riga_ordine(session, "ART001", ordered_qty=Decimal("8"))

        result = list_planning_candidates_v1(session)
        assert len(result) == 2
        assert all(c.article_code == "ART001" for c in result)
        assert all(c.planning_mode == "by_customer_order_line" for c in result)
        line_refs = {c.line_reference for c in result}
        assert len(line_refs) == 2
