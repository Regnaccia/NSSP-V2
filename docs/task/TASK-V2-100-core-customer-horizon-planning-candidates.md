# TASK-V2-100 - Core customer horizon in Planning Candidates

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

## Goal

Introdurre nel Core `Planning Candidates` un primo orizzonte temporale customer-driven semplice,
basato su `data_consegna`, senza eliminare i candidate fuori orizzonte.

## Scope

- introdurre configurazione minima `customer_horizon_days`
- calcolare nel Core il flag:
  - `is_within_customer_horizon`
- applicare la logica nel ramo customer-driven in modo read-model / projection oriented
- mantenere i candidate fuori orizzonte visibili nel Core, senza scartarli

## Out of Scope

- filtro UI
- lead time
- tempi ciclo
- scheduling

## Constraints

- la regola V1 e basata solo su `data_consegna`
- nessun candidate deve essere perso solo perche fuori orizzonte

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

Introdotto `is_within_customer_horizon` flag nel ramo `by_article` dei Planning Candidates.

**`planning_candidates/read_models.py`**:
- Aggiunto `is_within_customer_horizon: bool | None = None` nel blocco by_article.
- Semantica: `True` = delivery entro orizzonte, `False` = delivery oltre, `None` = nessuna data_consegna valorizzata o candidate by_customer_order_line.

**`planning_candidates/queries.py`**:
- Aggiunto `_DEFAULT_CUSTOMER_HORIZON_DAYS = 30` (configurazione minima V1 — costante di modulo, senza tabella DB).
- Aggiunto `_compute_nearest_delivery_by_article`: aggrega `min(expected_delivery_date)` per articolo da `sync_righe_ordine_cliente` (non descrittive, con delivery date valorizzata).
- Aggiunto `_is_within_customer_horizon`: helper puro `nearest <= today + horizon_days`.
- In `_list_by_article_candidates`: chiama `_compute_nearest_delivery_by_article` una volta per tutti gli articoli, calcola `within_horizon` per ogni candidate e lo attacca al `PlanningCandidateItem`.
- Candidate fuori orizzonte non vengono eliminati: il flag e `False`, la riga resta visibile nel Core.

**Test** (15 nuovi in `test_core_planning_candidates_horizon.py`):
- 7 test helper puri (`_is_within_customer_horizon`, `_DEFAULT_CUSTOMER_HORIZON_DAYS`)
- 8 test integrazione `list_planning_candidates_v1`:
  - True / False / None per delivery date assente
  - boundary (oggi + 30 → True, incluso)
  - nearest delivery usata quando ci sono piu righe con date diverse
  - candidato fuori orizzonte non scartato (flag False, candidate presente)
  - by_customer_order_line: flag sempre None

## Completed At

2026-04-13

## Completed By

Claude Code
