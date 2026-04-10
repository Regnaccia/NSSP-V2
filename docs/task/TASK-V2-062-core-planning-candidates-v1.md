# TASK-V2-062 - Core Planning Candidates V1

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`
- `docs/task/TASK-V2-049-core-availability.md`
- `docs/task/TASK-V2-054-refresh-semantici-backend.md`

## Goal

Introdurre il primo slice Core di `Planning Candidates` V1 come projection customer-driven aggregata per articolo, basata su `future_availability_qty`.

## Context

La V2 ha gia chiuso il modello quantitativo canonico:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

Dispone inoltre di:

- `customer_order_lines`
- `produzioni attive`
- refresh semantici backend
- una prima vista operativa `criticita articoli`

Con `DL-ARCH-V2-025` il progetto fissa la V1 di `Planning Candidates` come una projection distinta da `criticita`:

- solo `customer-driven`
- aggregata per `article`
- basata su:
  - `availability_qty`
  - `incoming_supply_qty`
  - `future_availability_qty = availability_qty + incoming_supply_qty`

Il primo passo attuativo corretto non e ancora la UI.

Serve prima una base Core pulita e verificabile, che renda disponibile:

- la logica V1
- il read model / projection del modulo
- la regola di generazione dei candidate

## Scope

### In Scope

- introdurre il primo slice Core `planning_candidates`
- introdurre la logica V1 customer-driven aggregata per articolo
- aggregare per articolo:
  - `customer_open_demand_qty`
  - `incoming_supply_qty`
- usare `availability_qty` come input canonico gia esistente
- calcolare:
  - `future_availability_qty = availability_qty + incoming_supply_qty`
  - `required_qty_minimum` quando la disponibilita futura resta negativa
- generare candidate solo quando:
  - `future_availability_qty < 0`
- introdurre un read model / projection o query dedicata per elencare i candidate V1
- campi minimi consigliati nel read model:
  - `article_code`
  - `availability_qty`
  - `customer_open_demand_qty`
  - `incoming_supply_qty`
  - `future_availability_qty`
  - `required_qty_minimum`
  - `computed_at`

### Out of Scope

- UI `Planning Candidates`
- route o navigazione frontend dedicate
- scoring / ranking
- planning horizon
- `incoming_within_horizon_qty`
- stock-driven candidates
- policy di aggregazione `aggregable / non_aggregable`
- candidate per riga ordine
- suggerimenti di quantita produttiva finale
- scheduler o allocazione risorse

## Constraints

- la logica V1 deve vivere come funzione di dominio separata, coerente con `DL-ARCH-V2-023`
- il task non deve ridefinire i fact canonici gia esistenti
- `availability_qty` deve mantenere il naming e il significato corrente
- `incoming_supply_qty` V1 deve essere semplice e time-agnostic
- il modulo deve restare aggregato per articolo
- non introdurre ora stati come `monitor`
- non introdurre hardcode di policy future su famiglie o articolo

## Refresh / Sync Behavior

La vista UI non e in scope in questo task.

Quindi:

- `La vista non ha refresh on demand`
- il task introduce solo logica Core e projection/read model
- eventuali refresh semantici dedicati verranno valutati nei task successivi del modulo

## Acceptance Criteria

- esiste una prima logica V1 di `planning candidates` coerente con `DL-ARCH-V2-025`
- il sistema espone un read model / query Core dei candidate aggregati per articolo
- `future_availability_qty` e calcolata come `availability_qty + incoming_supply_qty`
- un candidate esiste solo se `future_availability_qty < 0`
- `required_qty_minimum` e valorizzata solo per articoli ancora scoperti
- il task non introduce ancora UI, scoring o policy stock-driven

## Deliverables

- logica Core `Planning Candidates` V1
- read model / projection / query Core dedicata
- test mirati sul modulo
- aggiornamento del solo task con completion notes ricche

## Verification Level

`Mirata`

Questo task introduce un nuovo slice Core e una nuova logica di dominio, ma non chiude ancora la milestone UI del modulo.

Quindi:

- test backend mirati sul nuovo slice
- niente full suite obbligatoria
- nessuna build frontend obbligatoria in questo task, salvo tocchi collaterali non previsti

## Environment Bootstrap

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

Sono ammessi sottoinsiemi piu mirati se il task aggiunge test dedicati al nuovo slice e non modifica contratti app ampi.

## Implementation Notes

Direzione raccomandata:

- modellare il modulo come slice Core separato, simile a `criticita`
- privilegiare chiarezza semantica e spiegabilita del read model
- mantenere il perimetro V1 strettissimo
- non anticipare ora l'interfaccia finale della vista planning

Una possibile traiettoria pulita e:

- `logic.py`
- `read_models.py`
- `queries.py`

con naming coerente al modulo.

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Slice Core introdotto

Nuovo modulo `nssp_v2.core.planning_candidates` con la struttura canonica del Core
(coerente con `criticita`):

```
core/planning_candidates/
  __init__.py       — esporta le API pubbliche del modulo
  logic.py          — logica pura V1 (PlanningContext, funzioni intercambiabili)
  read_models.py    — PlanningCandidateItem (frozen Pydantic)
  queries.py        — list_planning_candidates_v1() + aggregati ausiliari
```

### Logica V1 (DL-ARCH-V2-025)

**`PlanningContext`** — dataclass frozen, contesto stabile passato alle funzioni:

```python
@dataclass(frozen=True)
class PlanningContext:
    article_code: str
    availability_qty: Decimal | None
    incoming_supply_qty: Decimal       # supply aggregata da produzioni attive
    customer_open_demand_qty: Decimal  # domanda cliente aperta aggregata
```

**Funzioni intercambiabili (DL-ARCH-V2-023):**

- `future_availability_v1(ctx)` → `availability_qty + incoming_supply_qty` (o None)
- `required_qty_minimum_v1(fav)` → `abs(fav)` se negativa, altrimenti `0`
- `is_planning_candidate_v1(ctx)` → `future_availability_qty < 0`

### Read model

**`PlanningCandidateItem`** — campi minimi V1:

| Campo | Significato |
|---|---|
| `article_code` | codice canonico |
| `availability_qty` | quota libera attuale |
| `customer_open_demand_qty` | domanda cliente aperta aggregata |
| `incoming_supply_qty` | supply da produzioni attive (rimanente) |
| `future_availability_qty` | `availability + incoming` |
| `required_qty_minimum` | `abs(future_availability)` quando candidate |
| `computed_at` | timestamp del computed fact availability |

### Query: aggregazione supply e demand

**`_compute_incoming_supply(session)`** — aggrega `incoming_supply_qty` per article_code
canonico da `sync_produzioni_attive` (attivo=True):

```python
remaining = max(quantita_ordinata - COALESCE(quantita_prodotta, 0), 0)
```

Il codice_articolo raw viene normalizzato a UPPER in Python per allineamento al canonical.
V1 tradeoff esplicito: `forza_completata` (override Core) non è considerato — la
produzione resta "incoming" se `attivo=True`, anche se marcata completata via override.
Una produzione con `quantita_prodotta >= quantita_ordinata` contribuisce `remaining = 0`,
il che è corretto senza richiedere il filtro esplicito di stato completata.

**`_compute_customer_demand(session)`** — aggrega `customer_open_demand_qty` per article_code
canonico da `sync_righe_ordine_cliente`:

```python
open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```

Esclude righe `continues_previous_line=True` (descrizioni, non domanda autonoma).

**`list_planning_candidates_v1(session)`** — perimetro articoli identico a `criticita`:
INNER JOIN con `sync_articoli` (attivo=True) via `func.upper()` per tollerare mismatch
di casing (coerente con TASK-V2-059 e TASK-V2-060).

Ordinamento: `future_availability_qty` crescente (i più scoperti sopra).

### Distinzione rispetto a `criticita`

| Aspetto | criticita | planning_candidates |
|---|---|---|
| Regola | `availability_qty < 0` | `future_availability_qty < 0` |
| Domanda | è scoperto adesso? | serve ancora nuova produzione? |
| Supply attiva | non considerata | inclusa in `incoming_supply_qty` |
| Articolo coperto da supply | appare in criticita | **non** appare in planning |

Questo è il caso di test chiave `test_articolo_critico_coperto_da_supply_non_e_candidate`:
un articolo con `availability=-3` e `incoming=5` è critico ma **non** è planning candidate
(`future = +2`).

### Tradeoff V1 espliciti

- `incoming_supply_qty` è time-agnostic: nessun ETA, nessun horizon
- `forza_completata` non considerato nella query planning (V1)
- nessun scoring o ranking
- nessuna policy per famiglia
- nessun candidate per riga ordine

### Test di regressione

`tests/core/test_core_planning_candidates.py` — 34 test in 6 classi:

- `TestLogicaPura` (11): funzioni pure su `PlanningContext`
- `TestPerimetroArticoli` (4): orfani esclusi, attivo=False escluso, baseline
- `TestLogicaCandidate` (5): candidate vs non-candidate, supply attiva vs non attiva
- `TestIncomingSupply` (3): aggregazione da più produzioni, remaining clampato a 0
- `TestCustomerDemand` (4): aggregazione da più righe, set_aside, fulfilled, zero
- `TestOrdinamentoECampi` (3): ordinamento crescente, campi read model, required_qty
- `TestCasingMismatch` (3): UPPER join per sync_articoli, produzioni, righe ordine

### Verifica

```
python -m pytest tests/core tests/app -q
332 passed in 5.38s
```

## Completed At

2026-04-10

## Completed By

Claude Code
