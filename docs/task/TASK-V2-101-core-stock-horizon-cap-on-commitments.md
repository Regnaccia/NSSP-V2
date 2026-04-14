# TASK-V2-101 - Core stock horizon cap on commitments

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
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`

## Goal

Introdurre un `stock horizon` nella componente stock-driven del ramo `by_article`, limitando gli
impegni cliente considerati al look-ahead coerente con `effective_stock_months`.

## Scope

- introdurre il concetto di:
  - `stock_horizon_availability_qty`
- limitare `capped_commitments_qty` agli impegni entro il look-ahead stock
- usare `stock_horizon_availability_qty` nel calcolo di:
  - `stock_replenishment_qty`
- mantenere invariata la logica customer-driven:
  - `customer_shortage_qty`

## Out of Scope

- filtro UI
- ETA produzioni
- lead time
- scheduling

## Constraints

- il cap temporale vale solo per la componente scorta
- il look-ahead V1 e:
  - `effective_stock_months`
- il candidate Core resta unico per articolo

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

```powershell
python -m pytest tests/ -v
```

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Introdotto `stock_horizon_availability_qty` nella componente stock-driven del ramo `by_article`.

**`planning_candidates/logic.py`**:
- Aggiunto `stock_horizon_availability_qty_v1(stock_effective, customer_set_aside_qty, capped_commitments_qty, incoming_supply_qty) -> Decimal`.
  Formula: `stock_eff - set_aside - capped_committed + incoming`.

**`planning_candidates/queries.py`**:
- Aggiunto `effective_stock_months: Decimal | None` a `_ArticoloInfo`; risolto in `_load_articoli_info` con regola override > famiglia (identica a `stock_policy/queries.py`).
- Aggiunto `_load_open_commitments_by_article_with_dates`: carica da `sync_righe_ordine_cliente` la lista `(open_qty, delivery_date)` per ogni articolo.
- Aggiunto `_capped_commitments_from_lines(line_data, lookahead_date) -> Decimal`: somma gli impegni con `delivery_date <= lookahead_date`. Righe senza data incluse (conservativo).
- In `_list_by_article_candidates`:
  - Se `art.effective_stock_months is not None`: `lookahead_date = today + round(months*30) days`, calcola `capped_committed` e `stock_horizon_avail = stock_horizon_availability_qty_v1(...)`, passa `stock_horizon_avail` a `stock_replenishment_qty_v1`.
  - Se `effective_stock_months is None`: fallback a `avail_eff` (no capping, target=None comunque).
- `customer_shortage_qty` invariata: usa ancora `fav` (full commitments).

**Test** (14 nuovi in `test_core_planning_candidates_stock_horizon.py`):
- 3 test `stock_horizon_availability_qty_v1` (puro)
- 6 test `_capped_commitments_from_lines` (tutto/niente/misto/None/boundary/lista vuota)
- 5 test integrazione:
  - ordini lontani esclusi → replenishment ridotta
  - customer_shortage invariata (usa fav completo)
  - ordini senza data inclusi nel capping (conservativo)
  - nessun ordine → capped=0 → stock_horizon_avail = stock_eff
  - effective_stock_months=None → no capping, replenishment=None

## Completed At

2026-04-13

## Completed By

Claude Code
