# TASK-V2-105 - Planning primary driver classification

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
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Introdurre una classificazione primaria univoca del candidate `by_article` per evitare che i casi
misti compaiano sia nella scheda `customer` sia nella scheda `stock`.

## Scope

- introdurre nel Core un campo esplicito:
  - `primary_driver`
- valori ammessi:
  - `customer`
  - `stock`
- applicare la regola di precedenza:
  - `customer_shortage_qty > 0` -> `customer`
  - altrimenti, `stock_replenishment_qty > 0` -> `stock`
- riallineare la UI `Planning Candidates` per usare `primary_driver` nei filtri/tab
- mantenere visibili entrambe le componenti quantitative nei casi misti

## Out of Scope

- nuovi horizon
- nuovi warning
- sdoppiamento del modulo planning

## Constraints

- il candidate resta unico
- i casi misti devono comparire una sola volta
- i casi misti devono stare nella scheda `customer`

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude su Core/UI `Planning Candidates`.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Introdotta classificazione primaria univoca `primary_driver` e riallineata la UI.

- Core by_article:
  - `primary_driver = customer` se `customer_shortage_qty > 0`
  - altrimenti `primary_driver = stock` se `stock_replenishment_qty > 0`
- Ramo by_customer_order_line classificato `primary_driver = customer`.
- Read model/API estesi con campo `primary_driver`.
- UI `Planning Candidates` aggiornata: filtri `Solo fabbisogno cliente / Solo scorta` basati su `primary_driver` (non più su soglie quantitative), evitando doppia presenza dei casi misti.
- Aggiunti test mirati su precedenza e classificazione.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
