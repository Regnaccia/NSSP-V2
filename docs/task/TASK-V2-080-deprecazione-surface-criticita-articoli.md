# TASK-V2-080 - Deprecazione surface criticita articoli

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/roadmap/STATUS.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/AI_HANDOFF_CURRENT_STATE.md`

## Goal

Deprecare formalmente la surface `criticita articoli` senza rimuoverla dal sistema,
per riflettere che il focus operativo si e spostato su:

- `Planning Candidates`
- futuro modulo `Warnings`

## Context

`Criticita articoli` e stata utile come primo slice di logica operativa, ma oggi:

- `Planning Candidates` copre una semantica piu ricca e piu vicina al bisogno produttivo
- `Warnings` prendera in carico le anomalie

La surface `criticita` non va cancellata subito, ma non deve piu essere trattata come
stream primario di evoluzione.

## Scope

- marcare la surface `criticita articoli` come `deprecated`
- aggiornare label/testi UI dove opportuno
- aggiornare overview/docs per chiarire il nuovo posizionamento
- ridurre la centralita della surface nella shell produzione se necessario
- mantenere la surface tecnicamente disponibile

## Refresh Behavior

- invariato
- la surface, finche esiste, continua a riusare il refresh semantico backend gia esistente

## Out of Scope

- rimozione della surface
- rimozione del codice backend/frontend associato
- migrazione automatica degli utenti
- modulo `Warnings`
- modifiche a `Planning Candidates`

## Constraints

- la deprecazione deve essere esplicita ma non distruttiva
- la surface deve restare raggiungibile nel breve periodo
- la documentazione deve chiarire che `criticita articoli` e una vista legacy / transitional

## Acceptance Criteria

- `criticita articoli` e chiaramente marcata come deprecated / legacy
- la docs riflette che non e piu la surface operativa primaria
- `Planning Candidates` e il nuovo stream primario per il fabbisogno operativo
- nessuna rimozione tecnica viene fatta in questo task

## Verification Level

- `Mirata`

Verifiche minime:

- build frontend
- smoke UI sulla navigazione shell produzione
- verifica documentale della deprecazione

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

