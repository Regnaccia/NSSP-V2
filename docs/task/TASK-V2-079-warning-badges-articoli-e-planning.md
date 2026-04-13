# TASK-V2-079 - Warning badges in articoli and planning

## Status

Deferred

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

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`

## Goal

Integrare il consumo dei warning nelle prime surface operative gia esistenti,
senza duplicare la logica del modulo `Warnings`.

## Context

Una volta disponibili:

- Core `Warnings`
- configurazione di visibilita
- surface `Warnings`

ha senso aggiungere indicatori sintetici nelle viste operative piu rilevanti:

- `articoli`
- `Planning Candidates`

## Scope

- introdurre badge o indicatori warning nel dettaglio `articoli`
- introdurre badge o indicatori warning nella vista `Planning Candidates`
- leggere i warning dal modulo canonico `Warnings`
- rispettare la visibilita configurata

## Out of Scope

- generazione warning locale nelle surface
- workflow warning avanzato
- nuove tipologie warning oltre quelle gia presenti nel modulo

## Constraints

- `Planning Candidates` non deve trattare `NEGATIVE_STOCK` come `reason` del candidate
- le surface devono solo consumare warning gia generati
- nessuna duplicazione di logica warning nei moduli operativi

## Acceptance Criteria

- `articoli` mostra indicatori warning coerenti con il modulo `Warnings`
- `Planning Candidates` mostra indicatori warning coerenti con il modulo `Warnings`
- la reason del candidate resta separata dal warning

## Verification Level

- `Mirata`

Verifiche minime:

- build frontend
- smoke UI su `articoli`
- smoke UI su `Planning Candidates`
- verifica che `NEGATIVE_STOCK` compaia come warning e non come reason del candidate

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`
