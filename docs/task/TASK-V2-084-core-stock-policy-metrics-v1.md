# TASK-V2-084 - Core stock policy metrics V1

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

Introdurre il primo computed slice Core della stock policy V1 con metriche articolo-specifiche.

## Context

Dopo il modello configurativo serve un building block Core separato che calcoli:

- `monthly_stock_base_qty`
- `capacity_calculated_qty`
- `capacity_effective_qty`
- `target_stock_qty`
- `trigger_stock_qty`

senza ancora cambiare `Planning Candidates`.

## Scope

- introdurre un computed fact o read model dedicato alle stock metrics
- includere:
  - `article_code`
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`
  - `algorithm_key`
  - `computed_at`
- implementare il pattern di logica sostituibile per il calcolo della base mensile
- usare:
  - `effective_stock_months`
  - `effective_stock_trigger_months`
  - `capacity_override_qty`

## Out of Scope

- integrazione in `Planning Candidates`
- UI dedicata
- scelta finale di algoritmi avanzati o multipli

## Constraints

- non introdurre stock policy nel ramo `by_customer_order_line`
- non creare duplicazione con `availability` o altri fact esistenti
- il calcolo della base mensile deve restare sostituibile

## Acceptance Criteria

- esiste un building block Core dedicato alle stock metrics V1
- `target_stock_qty` e `trigger_stock_qty` sono calcolati secondo `DL-ARCH-V2-030`
- la logica di `monthly_stock_base_qty` e isolata e sostituibile

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base ai test backend introdotti.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

