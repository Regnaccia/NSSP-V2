# TASK-V2-104 - UI planning customer horizon filter semantic fix

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
- `docs/task/TASK-V2-103-core-separate-customer-and-stock-horizons.md`

## Goal

Riallineare la UI/API `Planning Candidates` affinche il filtro utente su `customer horizon`
governi solo la presentazione customer-driven e non alteri la semantica della componente scorta.

## Scope

- aggiornare la vista `Planning Candidates`
- aggiornare l'eventuale wiring API collegato al filtro `customer horizon`
- fare in modo che il controllo UI dell'orizzonte:
  - agisca solo sul filtro customer
  - non cambi il cap stock-driven
- riallineare testi/tooltip se necessario

## Out of Scope

- nuovi moduli planning
- nuovi warning
- nuove configurazioni admin

## Constraints

- i filtri `Tutti / Solo fabbisogno / Solo scorta` restano invariati
- il filtro `customer horizon` resta un filtro di presentazione
- nessuna duplicazione di righe o di candidate

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude su UI/API `Planning Candidates`.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Riallineata la semantica UI/API del filtro horizon customer.

- Endpoint `GET /produzione/planning-candidates` documentato come filtro customer-only (`horizon_days` non governa più la componente stock).
- Wiring backend aggiornato: `horizon_days` viene passato a `customer_horizon_days`.
- UI `Planning Candidates` mantiene il controllo utente dell'orizzonte come filtro di presentazione customer (`is_within_customer_horizon`) senza impatti su cap stock.

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
