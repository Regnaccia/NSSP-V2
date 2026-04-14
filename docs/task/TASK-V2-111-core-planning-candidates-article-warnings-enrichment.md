# TASK-V2-111 - Core Planning Candidates article warnings enrichment

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date
2026-04-14

## Owner
Claude Code

## Source Documents

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/guides/PLANNING_AND_STOCK_RULES.md`

## Goal

Arricchire `Planning Candidates` con gli warning attivi dell'articolo, filtrati correttamente per
area utente, senza duplicare la logica del modulo `Warnings`.

## Context

Lo stock-driven ha introdotto warning articolo importanti, in particolare:

- `INVALID_STOCK_CAPACITY`

Oggi per vedere il warning l'operatore deve uscire dal planning e andare nella surface dedicata
`Warnings`. Serve invece una lettura immediata nel contesto del candidate.

## Scope

- estendere il read model/API `Planning Candidates` con una forma minima degli warning attivi
  collegati all'articolo
- consumare warning canonici gia generati dal modulo `Warnings`
- filtrare i warning esposti in planning in base a:
  - `visible_to_areas`
  - area corrente dell'utente
- esporre almeno:
  - `active_warnings`
  - oppure `active_warning_codes`
- coprire il primo caso operativo:
  - `INVALID_STOCK_CAPACITY`

## Out of Scope

- rendering UI dei badge warning
- modal di configurazione articolo
- nuovi tipi warning non ancora generati dal modulo `Warnings`

## Constraints

- `Planning Candidates` non deve ricalcolare warning
- il modulo `Warnings` resta l'unica sorgente di verita
- il contratto deve restare estendibile a warning futuri

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `Si`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `Si`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `No`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Pattern References

- `Pattern 2 - Mirror esterno + arricchimento interno`
- `Pattern 15 - Governance in admin, consumo nelle surface operative`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- ogni candidate puo esporre warning attivi dell'articolo
- gli warning provengono dal modulo `Warnings`
- la lista warning in planning rispetta `visible_to_areas`
- `INVALID_STOCK_CAPACITY` e disponibile nel contratto planning quando attivo

## Deliverables

- read model/API `Planning Candidates` estesi
- enrichment Core/API dei warning articolo
- test mirati Core/API

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude su Core/API `Planning Candidates` e `Warnings`.

## Implementation Notes

- il contratto warning planning puo restare minimale, per esempio:
  - `code`
  - `severity`
  - `message`

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Esteso il read model/API `Planning Candidates` con:
  - `active_warning_codes`
  - `active_warnings` (shape minima: `code`, `severity`, `message`)
- Enrichment Core implementato senza ricalcolo warning:
  - consumo warning canonici da modulo `Warnings` (`list_warnings_v1`)
  - filtro per area utente via `filter_warnings_by_areas`
  - mapping per articolo applicato ai candidate finali
- Endpoint `/api/produzione/planning-candidates` aggiornato per passare al Core:
  - `user_areas` derivate dai ruoli utente
  - `is_admin`
- Coperto caso operativo `INVALID_STOCK_CAPACITY` con test mirati:
  - warning incluso quando area utente compatibile
  - warning escluso quando area utente non visibile

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
