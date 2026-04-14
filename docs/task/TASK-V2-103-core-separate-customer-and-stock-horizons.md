# TASK-V2-103 - Core separate customer and stock horizons

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
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`

## Goal

Riallineare il Core `Planning Candidates` alla distinzione corretta tra:

- `customer horizon`
- `stock horizon`

evitando che la stessa leva governi sia il flag customer sia il cap della componente scorta.

## Scope

- separare nel Core i due concetti di horizon
- fare in modo che:
  - `is_within_customer_horizon` usi solo il `customer horizon`
  - `stock_replenishment_qty` usi solo il `stock horizon`
- eliminare l'accoppiamento improprio introdotto tra `horizon_days` e cap della componente scorta
- riallineare helper, query e test Core collegati
- aggiornare eventuali commenti/read model interni rimasti ambigui

## Out of Scope

- nuovi filtri UI
- nuovi warning
- nuovi task admin

## Constraints

- il candidate Core resta unico
- il `customer horizon` non deve eliminare i candidate fuori orizzonte
- la componente scorta non deve dipendere da una leva di presentazione UI customer

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude sui test `planning_candidates`.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Riallineata la logica Core separando definitivamente `customer horizon` e `stock horizon`.

- `list_planning_candidates_v1` ora riceve `customer_horizon_days` (solo per `is_within_customer_horizon`).
- Nel ramo `by_article` il capping stock usa solo `effective_stock_months` (look-ahead `months * 30`), mai il parametro customer horizon.
- `stock_replenishment_qty` usa sempre `stock_horizon_availability_qty` calcolata con il capping stock dedicato.
- Aggiunto test mirato che verifica che cambiare `customer_horizon_days` non altera `stock_replenishment_qty`.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
