# TASK-V2-112 - UI Planning Candidates warnings column

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
- `docs/task/TASK-V2-111-core-planning-candidates-article-warnings-enrichment.md`

## Goal

Rendere immediatamente visibili nella tabella `Planning Candidates` gli warning articolo che
impattano la lettura o la configurazione del candidate.

## Context

Gli warning articolo piu rilevanti per il planning oggi, come `INVALID_STOCK_CAPACITY`, esistono
gia nel modulo `Warnings` ma non sono visibili direttamente nella tabella planning.

Serve una colonna sintetica dedicata.

## Scope

- introdurre una colonna `Warnings` nella tabella `Planning Candidates`
- mostrare badge warning sintetici a partire dagli warning attivi dell'articolo
- gestire almeno il primo tipo:
  - `INVALID_STOCK_CAPACITY`
- mantenere il rendering estendibile a warning futuri

## Out of Scope

- modal di configurazione articolo
- generazione warning
- nuovi warning types

## Constraints

- la UI deve consumare solo il contratto planning arricchito
- nessuna logica warning duplicata lato frontend
- la colonna deve rimanere leggibile anche in presenza di zero warning

## Pattern Checklist

- `Richiede mapping o chiarimento sorgente esterna?` -> `No`
- `Introduce o modifica mirror sync_*?` -> `No`
- `Introduce o modifica computed fact / read model / effective_* nel core?` -> `No`
- `Introduce configurazione interna governata da admin?` -> `No`
- `Introduce configurazione che deve essere visibile in articoli?` -> `No`
- `Introduce override articolo o default famiglia?` -> `No`
- `Richiede warnings dedicati o impatta warning esistenti?` -> `Si`
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` -> `No`
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` -> `Si`
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` -> `No`
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` -> `No`

## Pattern References

- `Pattern 15 - Governance in admin, consumo nelle surface operative`
- `Pattern 16 - Core unico, segmentazione solo in UI`

## Refresh / Sync Behavior

La vista riusa un refresh semantico backend gia esistente.

Non viene introdotto alcun nuovo refresh dedicato.

## Acceptance Criteria

- la tabella `Planning Candidates` mostra una colonna `Warnings`
- gli warning attivi dell'articolo sono visibili tramite badge sintetici
- `INVALID_STOCK_CAPACITY` e chiaramente riconoscibile
- assenza warning = cella neutra / vuota senza rumore visivo inutile

## Deliverables

- tabella `Planning Candidates` aggiornata
- rendering badge warning mirato
- verifiche UI mirate

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire in modo mirato da Claude sulla UI `Planning Candidates`.

## Implementation Notes

- tenere i badge warning distinti dai badge motivi (`Cliente` / `Scorta`)

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

- Aggiunta colonna `Warnings` nella tabella `Planning Candidates`.
- Implementato rendering badge warning da `active_warnings` (contratto planning arricchito).
- Mapping esplicito per `INVALID_STOCK_CAPACITY` con badge dedicato (`Capacity`).
- Fallback estendibile per warning futuri: badge con `code` e tooltip su `message`.
- Cella senza warning resa neutra con placeholder non invasivo (`—`).

## Completed At

2026-04-14

## Completed By

Codex (GPT-5)
