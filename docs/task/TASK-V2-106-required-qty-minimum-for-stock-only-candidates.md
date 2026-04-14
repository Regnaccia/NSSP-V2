# TASK-V2-106 - Required qty minimum for stock-only candidates

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

Rendere `required_qty_minimum` coerente anche per i candidate `stock-only`, valorizzandolo con la
scopertura minima di scorta rispetto al `target_stock_qty`.

## Scope

- riallineare il Core `Planning Candidates by_article`
- fare in modo che:
  - `required_qty_minimum = customer_shortage_qty` per `primary_driver = customer`
  - `required_qty_minimum = stock_replenishment_qty` per `primary_driver = stock`
- coprire esplicitamente il caso `stock-only`
- riallineare eventuali test e commenti collegati

## Out of Scope

- nuovi filtri UI
- nuovi warning
- nuovi horizon

## Constraints

- il candidate resta unico
- `required_qty_total` continua a rappresentare la somma complessiva delle componenti
- `required_qty_minimum` rappresenta la minima quantita coerente con il driver primario

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

Riallineato `required_qty_minimum` al driver primario nel ramo `by_article`.

- Aggiunta risoluzione esplicita `primary_driver`.
- Calcolo `required_qty_minimum` aggiornato:
  - `customer` -> `customer_shortage_qty`
  - `stock` -> `stock_replenishment_qty`
- Coperto il caso `stock-only`: `required_qty_minimum` ora valorizzato correttamente con la scopertura scorta.
- Aggiunti test dedicati su `required_qty_minimum_by_primary_driver_v1` e verifiche d’integrazione sui candidati stock-driven.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
