# TASK-V2-102 - UI Planning Candidates driver filters and horizon

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

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/task/TASK-V2-100-core-customer-horizon-planning-candidates.md`
- `docs/task/TASK-V2-101-core-stock-horizon-cap-on-commitments.md`

## Goal

Separare operativamente nella UI `Planning Candidates` i driver `fabbisogno cliente` e `scorta`,
introducendo filtri espliciti e un filtro customer horizon.

## Scope

- aggiungere filtro o tab:
  - `Tutti`
  - `Solo fabbisogno cliente`
  - `Solo scorta`
- basare i filtri su:
  - `customer_shortage_qty > 0`
  - `stock_replenishment_qty > 0`
- aggiungere filtro:
  - `solo entro customer horizon`
- mantenere una sola vista/modulo `Planning Candidates`

## Out of Scope

- nuovo modulo separato planning stock
- nuovi refresh dedicati
- changing domain logic lato frontend

## Constraints

- il filtro e solo di presentazione
- il Core resta unico
- nessuna duplicazione di righe lato UI

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

Aggiunti filtri driver e horizon nella UI Planning Candidates. Orizzonte customer configurabile in UI con default 30 giorni.

**`core/planning_candidates/read_models.py`**:
- Aggiunto `nearest_delivery_date: date | None = None` — data_consegna più vicina tra le righe ordine dell'articolo.

**`core/planning_candidates/queries.py`**:
- `_list_by_article_candidates` riceve `horizon_days: int` e lo usa per:
  - `_is_within_customer_horizon(...)` — rimpiazza `_DEFAULT_CUSTOMER_HORIZON_DAYS`.
  - Cap impegni scorta: `lookahead_date = today + timedelta(days=horizon_days)` — rimpiazza `effective_stock_months * 30`. Il cap si applica ora quando `target_qty is not None` (stock policy configurata), indipendentemente da `effective_stock_months`.
- `list_planning_candidates_v1(session, horizon_days: int = 30)` — default 30, retrocompatibile.
- Popolato `nearest_delivery_date` da `nearest_deliveries.get(avail.article_code)`.

**`app/api/produzione.py`**:
- Aggiunto `horizon_days: int = Query(default=30, ge=1)` all'endpoint `GET /planning-candidates`.
- Passato a `list_planning_candidates_v1(session, horizon_days=horizon_days)`.

**`frontend/src/types/api.ts`**:
- Aggiunti 5 campi a `PlanningCandidateItem`:
  - `customer_shortage_qty: string | null`
  - `stock_replenishment_qty: string | null`
  - `required_qty_total: string | null`
  - `is_within_customer_horizon: boolean | null`
  - `nearest_delivery_date: string | null`

**`frontend/src/pages/surfaces/PlanningCandidatesPage.tsx`**:
- Aggiunto tipo locale `DriverFilter = 'tutti' | 'fabbisogno' | 'scorta'`.
- Aggiunto componente `DriverFilterBar`: tab segmentata Tutti / Solo fabbisogno cliente / Solo scorta + checkbox "Entro" + input numerico giorni (default 30) + label "giorni". Input disabilitato se checkbox inattiva.
- Aggiunti stati `driverFilter`, `soloEntroHorizon`, `horizonDays` (default 30).
- `loadCandidates` passa `params: { horizon_days }` all'API.
- `useEffect` su `horizonDays` ri-fetcha con debounce 600ms: il server ricalcola `is_within_customer_horizon` e `stock_replenishment_qty` con il nuovo orizzonte.
- `filtered` usa `is_within_customer_horizon === true` (server-side, coerente con `stock_replenishment_qty`).
- `npx tsc --noEmit` e `pytest tests/core/test_core_planning_candidates_*.py` passano senza errori.

## Completed At

2026-04-13

## Completed By

Claude Code
