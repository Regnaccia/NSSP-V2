# TASK-V2-071 - Core Planning Candidates V2 branching

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md`
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`
- `docs/task/TASK-V2-062-core-planning-candidates-v1.md`
- `docs/task/TASK-V2-069-allineamento-nomenclatura-planning-mode.md`

## Goal

Evolvere il Core `Planning Candidates` dalla V1 aggregata unica al branching reale tra:

- `planning_mode = by_article`
- `planning_mode = by_customer_order_line`

## Context

La V1 attuale di `Planning Candidates` lavora sempre aggregata per articolo.

Con `DL-ARCH-V2-027` questa semantica non e piu sufficiente:

- alcuni articoli restano correttamente pianificati `by_article`
- altri devono essere pianificati `by_customer_order_line`

La scelta non deve essere hardcoded.
Deve essere guidata da:

- `effective_aggrega_codice_in_produzione`
- e dal vocabolario esplicito `planning_mode` introdotto da `TASK-V2-069`

## Scope

- introdurre nel Core `Planning Candidates` il branching reale tra le due modalita
- mantenere il comportamento esistente per:
  - `planning_mode = by_article`
- introdurre il nuovo comportamento per:
  - `planning_mode = by_customer_order_line`
- esporre nel risultato il campo esplicito:
  - `planning_mode`
- supportare nel ramo `by_customer_order_line`:
  - identita per riga ordine cliente
  - domanda per riga:
    - `max(ordered_qty - set_aside_qty - fulfilled_qty, 0)`
  - `availability_qty = 0`
  - match tra candidate e produzioni tramite:
    - `numero_ordine_cliente`
    - `riga_ordine_cliente`
    - `riferimento_numero_ordine_cliente`
    - `riferimento_riga_ordine_cliente`
  - esclusione delle produzioni completate, anche via override `forza_completata`
- mantenere shape e logica stabili e difendibili per entrambe le modalita

## Out of Scope

- cambiare la UI `Planning Candidates`
- introdurre scoring / ranking
- introdurre planning horizon o ETA
- introdurre stock-driven candidates
- ridefinire il modello di planning policy oltre il branching gia deciso
- introdurre policy di aggregazione ulteriori oltre:
  - `by_article`
  - `by_customer_order_line`

## Constraints

- il ramo `by_article` deve restare retrocompatibile con la V1
- il ramo `by_customer_order_line` non deve usare in modo ambiguo la metrica articolo-level `future_availability_qty`
- nel ramo per-riga usare una metrica esplicita tipo:
  - `line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty`
- i candidate devono rendere sempre chiaro quale modalita li ha prodotti
- evitare hardcode UI-side: il branching deve vivere nel Core

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Questo task non introduce un nuovo refresh:

- continua a riusare il refresh semantico della surface `produzione`
- non cambia la chain di riallineamento dati

## Acceptance Criteria

- il Core `Planning Candidates` produce candidate sia `by_article` sia `by_customer_order_line` in base a `planning_mode`
- il ramo `by_article` mantiene il comportamento V1 esistente
- il ramo `by_customer_order_line` usa identita, domanda e supply collegate alla singola riga ordine
- le produzioni completate non contribuiscono alla supply planning in nessuno dei due rami
- il contratto espone `planning_mode` in modo esplicito
- la completion note dichiara chiaramente:
  - shape del read model finale
  - metriche usate nei due rami
  - eventuali limiti residui

## Verification Level

- `Mirata`

Verifiche minime richieste:

- test backend/Core mirati sui due rami:
  - `by_article`
  - `by_customer_order_line`
- casi di test espliciti su:
  - riga ordine coperta da produzioni collegate
  - riga ordine non coperta
  - esclusione di produzioni completate via override

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

Il riallineamento di roadmap, overview e guide trasversali viene fatto dopo da Codex.

## Contracts / Flows Changed

### Read model `PlanningCandidateItem` — shape finale

**Campi comuni** (presenti in entrambe le modalità):
- `article_code`, `display_label`, `famiglia_code`, `famiglia_label`
- `effective_considera_in_produzione`, `effective_aggrega_codice_in_produzione`, `planning_mode`
- `required_qty_minimum`, `computed_at`

**Campi by_article** (None per by_customer_order_line):
- `availability_qty`, `customer_open_demand_qty`, `incoming_supply_qty`, `future_availability_qty`

**Campi by_customer_order_line** (None per by_article):
- `order_reference`, `line_reference`
- `line_open_demand_qty`, `linked_incoming_supply_qty`, `line_future_coverage_qty`

### Nuove funzioni/tipi Core

**`logic.py`**:
- `PlanningContextOrderLine`: dataclass contesto by_customer_order_line
- `line_future_coverage_v2(ctx)`: `linked_supply - line_demand`
- `is_planning_candidate_by_order_line(ctx)`: candidatura se `line_future_coverage < 0`
- `required_qty_minimum_by_order_line(coverage)`: scopertura minima

**`queries.py`** — ristrutturazione completa:
- `_load_articoli_info`: query preliminare per determinare `planning_mode` per ogni articolo
- `_load_forza_completata_ids`: set di id_dettaglio esclusi
- `_compute_incoming_supply_by_article`: supply aggregata per by_article
- `_compute_linked_supply_by_line`: supply per (order_reference, line_reference)
- `_list_by_article_candidates`: ramo by_article (V1 retrocompatibile)
- `_list_by_customer_order_line_candidates`: ramo by_customer_order_line
- `list_planning_candidates_v1`: entry point con branching + merge + sort

### Metriche per modalità

**by_article**: `future_availability_qty = availability_qty + incoming_supply_qty < 0`
**by_customer_order_line**: `line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty < 0`

### Limiti residui

- `by_customer_order_line` è time-agnostic: nessun ETA, nessuna finestra temporale
- le produzioni storiche non sono consultate (solo attive con riferimento ordine)
- supply non collegata (senza riferimento ordine) non conta nel ramo by_customer_order_line

### UI

La UI (`PlanningCandidatesPage`) non è stata modificata strutturalmente. Aggiornato solo `types/api.ts` per rendere i campi by_article `string | null` (erano `string`). Un fix minimale su `parseFloat(item.future_availability_qty ?? '0')` per gestire il null nel sort.

## Documentation Impact

Nessun impatto documentale trasversale — l'interfaccia API esposta (`GET /api/produzione/planning-candidates`) mantiene lo stesso URL e restituisce ancora una lista di `PlanningCandidateItem`. I nuovi campi sono additive (opzionali con default None).

## Completion Notes

TASK-V2-071 completato. 648 test backend passati (+19 nuovi). Build frontend pulita.

Il Core `Planning Candidates` ora biforca realmente su `planning_mode`:
- articoli `by_article` (o senza policy) → logica V1 su `core_availability`
- articoli `by_customer_order_line` → logica V2 per riga ordine, senza `core_availability`

Le produzioni completate (`forza_completata=True`) sono escluse dalla supply in entrambe le modalità. Il vocabolario `planning_mode` è esposto esplicitamente in ogni candidate.

## Verification Notes

**Test logica pura by_customer_order_line** (`TestLogicaPuraOrderLine`): 9 test su `line_future_coverage_v2`, `is_planning_candidate_by_order_line`, `required_qty_minimum_by_order_line`.

**Test integrazione branching** (`TestByCustomerOrderLine`): 10 test su:
- riga non coperta → candidate
- riga coperta → non candidate
- riga parzialmente coperta → required_qty_minimum corretto
- demand zero → non candidate
- forza_completata esclusa da linked_supply
- supply non collegata ignorata
- assenza core_availability non blocca il ramo by_customer_order_line
- mix by_article + by_customer_order_line nella stessa query
- articolo by_article non genera candidati per riga
- più righe stesso articolo by_customer_order_line → candidati separati

Suite completa: **648 passed**, 0 failed.

## Completed At

2026-04-10

## Completed By

Claude Code
