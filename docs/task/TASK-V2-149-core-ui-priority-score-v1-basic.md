# TASK-V2-149 - Core/UI `priority_score_v1_basic`

## Status
Completed

## Date
2026-04-19

## Owner
Codex

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-042.md`
- `docs/decisions/ARCH/DL-ARCH-V2-043.md`
- `docs/decisions/ARCH/DL-ARCH-V2-044.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`

## Goal

Materializzare la prima V1 stabile e spiegabile del punteggio planning:

- `priority_score_v1_basic`

con:

- formula documentata
- `stock_pressure` ratio-based
- esposizione minima coerente in Core/API/UI

## Scope

- congelare la formula V1 nel Core
- rendere esplicita la policy attiva:
  - `priority_score_v1_basic`
- riallineare `priority_score` al contratto:
  - `time_urgency`
  - `customer_pressure`
  - `stock_pressure`
  - `release_penalty`
  - `warning_penalty`
- usare `stock_effective_qty / target_stock_qty` per `stock_pressure`
- esporre in UI almeno:
  - valore score
  - presenza esplicita nella colonna sinistra
  - sorting coerente per priorita

## Out of Scope

- admin config di policy score
- score per articolo o famiglia
- allocazione stock a ordini
- priorita ERP
- setup produttivi
- earliest start / completion
- formula finale multi-modulo

## Constraints

- lo score non puo cambiare:
  - `primary_driver`
  - `reason_code`
  - `reason_text`
  - `release_status`
- `stock_pressure` deve essere ratio-based
- il tempo deve restare layer di priorita, non di bisogno
- la V1 deve restare spiegabile e testabile

## Acceptance Criteria

- `priority_score` implementa il contratto di `DL-ARCH-V2-044`
- `stock_pressure` non usa piu una pura scala assoluta di quantita
- `priority_score` resta clampato in `0..100`
- i candidate cliente urgenti restano prioritizzati sopra casi stock comparabili
- la UI planning mostra `priority_score` nella colonna sinistra
- la UI planning puo ordinare per `priority_score desc`
- test mirati coprono:
  - urgenza temporale
  - pressione cliente
  - pressione stock ratio-based
  - penalita release
  - penalita warning

## Deliverables

- delta Core planning score
- eventuale enrichment API minimo
- delta UI planning per visualizzazione / sorting
- test dedicati
- riallineamento docs

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-19

Implementazione completa. 45 test passati.

**Core** (`core/planning_candidates/queries.py`):
- `_compute_priority_score_v1` sostituita con `_compute_priority_score_v1_basic` — firma estesa, formula addittiva per contratto DL-ARCH-V2-044.
- Componenti: `time_urgency` (step-function a fasce), `customer_pressure` (base+tier capped 40), `stock_pressure` (ratio `stock_effective/target_stock`, 6 fasce), `release_penalty` (sottratto), `warning_penalty` (sottratto per conteggio).
- Ritorna `(score, band)` — clamp `0..100`.
- Injection point aggiornato: passa `customer_shortage_qty`, `stock_replenishment_qty`, `stock_effective_qty`, `target_stock_qty`, `active_warnings_count`; inietta anche `priority_band` nel `model_copy`.

**Read model** (`core/planning_candidates/read_models.py`):
- Aggiunto `priority_band: Literal["low", "medium", "high", "critical"] | None = None`.
- Aggiunto `target_stock_qty: Decimal | None = None` (necessario per ratio stock_pressure).
- Candidate `by_article` ora popola `target_stock_qty=target_qty` nella costruzione.

**Frontend** (`types/api.ts`):
- Aggiunto `priority_band: 'low' | 'medium' | 'high' | 'critical' | null`.
- Aggiunto `target_stock_qty: string | null`.

**Frontend** (`pages/surfaces/PlanningWorkspacePage.tsx`):
- `SortBy` type esteso: aggiunto `'priority_score'`.
- `SORT_OPTIONS`: aggiunto `{ value: 'priority_score', label: 'Priorità' }` come prima opzione.
- Sort logic: `priority_score` descending con secondary sort per codice.
- Default sort cambiato da `'data_consegna'` a `'priority_score'`.
- Aggiunto componente `PriorityBandBadge` con colori semantici (critical=red, high=orange, medium=yellow, low=gray).
- Badge `priority_band` mostrato in riga 5 di `CandidateCard`, con tooltip score.

**Test** (`tests/core/test_core_priority_score_v1_basic.py`):
- 45 test puri (no DB) divisi in 7 classi: `TestTimeUrgency`, `TestCustomerPressure`, `TestStockPressure`, `TestReleasePenalty`, `TestWarningPenalty`, `TestClamp`, `TestPriorityBand`, `TestGuardrail`.
- Copertura completa di tutti i branch e fasce delle 5 componenti.
