# TASK-V2-085 - Planning Candidates stock-driven V1

## Status

Todo

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

Da definire da Claude in base ai test backend/frontend introdotti.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

