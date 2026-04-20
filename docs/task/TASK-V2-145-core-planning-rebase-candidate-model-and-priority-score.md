# TASK-V2-145 - Core planning rebase: candidate model semplice + baseline `priority_score`

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-041.md`
- `docs/decisions/ARCH/DL-ARCH-V2-042.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/roadmap/REBASE_V2_BACKLOG_2026-04-15.md`

## Goal

Aprire il primo slice di rebase Core di `Planning Candidates` per convergere verso:

- classificazione planning piu semplice
- separazione esplicita tra bisogno, rilascio e priorita
- baseline iniziale di `priority_score` come layer distinto

## Context

Il modello attuale planning usa ancora `customer_horizon_days` dentro il calcolo della componente cliente.

Il rebase ha ora fissato in modo netto che:

- Core planning semplice e stabile
- priorita temporale trattata in un layer separato
- rimozione diretta di `customer_horizon_days` dal calcolo Core

## Scope

- rimuovere `customer_horizon_days` dal calcolo Core nel ramo `by_article`
- progettare il delta minimo per allineare la classificazione planning al target rebase
- introdurre nel read model un primo `priority_score` placeholder spiegabile
- definire i primi input del punteggio in forma semplice e difendibile
- mantenere separati:
  - `primary_driver`
  - `reason_code`
  - `required_qty_total`
  - `release_status`
  - `priority_score`

## Out of Scope

- algoritmo finale di priorita multi-fattore
- allocazione automatica stock a ordini
- priorita ordine da ERP
- setup produttivi
- tempi di ciclo o schedulazione macchina
- pannello proposal della colonna destra

## Constraints

- il task deve rimuovere `customer_horizon_days` dal calcolo Core
- `priority_score` non deve sostituire `reason_code` o `release_status`
- il punteggio iniziale deve restare spiegabile
- i test reali gia materializzati su `12x8x25` devono essere riletti contro la nuova semantica target

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` Possibile
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` Si
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 08 - Quantita esplicite con semantica distinta`

## Refresh / Sync Behavior

- riusare il refresh semantico backend esistente
- non introdurre nuovi mirror

## Acceptance Criteria

- `customer_horizon_days` non influenza piu `customer_shortage_qty`
- il read model planning espone un primo `priority_score`
- `priority_score` resta separato da:
  - `primary_driver`
  - `reason_code`
  - `release_status`
- i test planning vengono riallineati al nuovo contratto
- spec e roadmap risultano coerenti col comportamento realmente implementato

## Deliverables

- delta Core planning sul read model `by_article`
- eventuale delta API
- test mirati
- riallineamento documentale del contratto planning

## Verification Level

- `Mirata`

## Implementation Log

### Core

- `customer_horizon_days` rimosso dal calcolo di `customer_shortage_qty` nel ramo `by_article`
- `customer_shortage_qty` riallineato a `max(-future_availability_qty, 0)`
- mantenuto il solo uso di `customer_horizon_days` per:
  - `is_within_customer_horizon`
  - supporto UI / priority
- introdotto `priority_score` nel read model `PlanningCandidateItem`
- introdotta baseline V1 di scoring nel Core planning

### Test

- aggiunti test dedicati in:
  - `backend/tests/core/test_core_planning_candidates.py`
- riallineata la suite storica:
  - `backend/tests/core/test_core_planning_candidates_stock_horizon.py`

### Note

- il task chiude il rebase Core sul significato di `customer_horizon`
- eventuali usi residui del filtro restano solo lato UI / ranking, non nella semantica del bisogno

## Implementation Log

### 2026-04-17

**Backend — `core/planning_candidates/read_models.py`**

- Aggiunto `priority_score: float | None = None` a `PlanningCandidateItem` (sezione campi comuni, dopo `computed_at`).
- Il campo e separato da `primary_driver`, `reason_code`, `release_status` (DL-ARCH-V2-042 §1).

**Backend — `core/planning_candidates/queries.py`**

- **Rimosso `_availability_with_capped_commitments`**: la funzione che applicava `customer_horizon_days` come capping degli impegni nella componente cliente non esiste piu.
- **Rimosso il blocco `customer_horizon_avail`** in `_list_by_article_candidates`: le circa 15 righe che calcolavano `customer_lookahead_date` / `customer_horizon_avail` sono state sostituite con una sola riga: `shortage = customer_shortage_qty_v1(fav)`.
- `customer_horizon_days` resta passato alla funzione ma viene usato solo per `_is_within_customer_horizon` (flag UI/presentazione) e per il capping dello stock horizon (component scorta, invariato).
- **Aggiunto `_compute_priority_score_v1`**: helper con formula a 4 componenti spiegabili (max 100 pt): proximity (0–40), shortage severity (0–40), release feasibility (0–15), warning (0–5).
- **`list_planning_candidates_v1`**: il `priority_score` e iniettato nel passo finale insieme ai warning, in modo che `has_active_warnings` sia definitivo al momento del calcolo.

**Frontend — `types/api.ts`**

- Aggiunto `priority_score: number | null` a `PlanningCandidateItem` (sezione campi comuni).

**Test — `tests/core/test_core_planning_candidates.py`**

- Aggiunta classe `TestRebaseCustomerHorizon` (3 test):
  - `test_shortage_basata_su_fav_completo`: verifica che `customer_shortage_qty` usi `fav` completo indipendentemente da `horizon_days`.
  - `test_shortage_invariata_al_variare_di_horizon_days`: invarianza con `horizon_days=5` vs `horizon_days=365`.
  - `test_candidato_con_riga_oltre_horizon_ma_fav_negativo`: caso chiave — riga ordine a 120gg con `horizon=30gg` produce un candidate post-rebase (pre-rebase non lo produceva).
- Aggiunta classe `TestPriorityScore` (5 test): presenza, separazione semantica, monotonicita, by_customer_order_line, non-negativita.

**Totale test**: 73 → 81 (tutti green).

**Impatto semantico**: gli articoli con ordini cliente oltre il vecchio `customer_horizon_days` ma con `fav < 0` (committed_qty nel CoreAvailability gia comprendeva quegli ordini) sono ora candidati con `primary_driver=customer`. Comportamento piu corretto e coerente con la classificazione `Cliente / Cliente+Magazzino / Magazzino`.
