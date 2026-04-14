# TASK-V2-085 - Planning Candidates stock-driven V1

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`

## Goal

Integrare la stock policy V1 nel ramo `Planning Candidates by_article` evitando doppio conteggio
tra shortage cliente e replenishment di scorta.

## Context

Una volta disponibili:

- configurazione stock policy
- configurazione logiche stock
- Core stock metrics

il planning puo estendersi da customer-driven puro a candidate unificati cliente + scorta
nel solo ramo `by_article`.

## Scope

- estendere `Planning Candidates by_article` con:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `required_qty_total`
- riusare `future_availability_qty`
- applicare:
  - `customer_shortage_qty = max(-future_availability_qty, 0)`
  - `stock_replenishment_qty = max(target_stock_qty - max(future_availability_qty, 0), 0)`
- mantenere un solo candidate per articolo
- chiarire reason / breakdown nel read model e nella UI planning

## Refresh / Sync Behavior

- La vista riusa un refresh semantico backend gia esistente
- `Planning Candidates` continua a riusare `refresh_articoli()`
- il task puo estendere i fact consumati dalla vista, ma non deve introdurre un nuovo refresh semantico separato

## Out of Scope

- stock policy nel ramo `by_customer_order_line`
- `Production Proposals`
- scoring
- badge warning

## Constraints

- nessun doppio candidate cliente + scorta sullo stesso articolo
- nessun doppio conteggio nella quantita totale
- il ramo `by_customer_order_line` resta invariato

## Acceptance Criteria

- `Planning Candidates by_article` integra la stock policy V1
- cliente e scorta sono rappresentati come breakdown di un solo candidate
- il ramo `by_customer_order_line` non usa stock policy

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```
python -m pytest tests/core/test_core_planning_candidates_stock.py tests/core/test_core_planning_candidates.py tests/core/test_core_stock_policy_logic.py tests/core/test_core_stock_policy_metrics.py -v
# 177 passed
```

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Nuove funzioni pure in `core/planning_candidates/logic.py`:**
- `is_planning_candidate_with_stock_v1(fav, trigger)`: estende la candidatura — True se `fav < 0` (shortage) OPPURE `fav < trigger` (scorta sotto soglia)
- `customer_shortage_qty_v1(fav)`: `max(-fav, 0)` — zero se cliente coperto
- `stock_replenishment_qty_v1(target, fav)`: `max(target - max(fav, 0), 0)` — il clamp `max(fav,0)` previene doppio conteggio; `None` se no stock policy
- `required_qty_total_v1(shortage, replenishment)`: somma shortage + replenishment (0 se replenishment=None)

**Nuovi campi in `PlanningCandidateItem` (`read_models.py`):**
- `customer_shortage_qty: Decimal | None = None`
- `stock_replenishment_qty: Decimal | None = None`
- `required_qty_total: Decimal | None = None`
- Nuovi reason codes documentati: `future_availability_negative`, `stock_below_trigger`, `line_demand_uncovered`

**Aggiornamento `queries.py` (`_list_by_article_candidates`):**
- Carica `list_stock_metrics_v1(session)` → dict `{article_code: StockMetricsItem}`
- Per ogni articolo usa `is_planning_candidate_with_stock_v1(fav, trigger_qty)` invece di `is_planning_candidate_v1`
- Popola il breakdown `customer_shortage_qty`, `stock_replenishment_qty`, `required_qty_total`
- Articoli senza stock policy: breakdown = None, candidatura identica a V1 puro
- `reason_code`: `"future_availability_negative"` se `fav < 0`, `"stock_below_trigger"` altrimenti

**Nuovo test file `tests/core/test_core_planning_candidates_stock.py`** (28 test):
- Classi pure: `TestIsCandidate`, `TestCustomerShortage`, `TestStockReplenishment`, `TestRequiredTotal`
- Integrazione: shortage cliente con/senza stock policy, trigger candidate, no doppio conteggio, campi None senza policy, by_customer_order_line invariato

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`
