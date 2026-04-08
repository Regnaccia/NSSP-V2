# TASK-V2-034 - Performance produzioni con default active

## Status
Todo

## Date
2026-04-08

## Scope

Ridurre il costo di caricamento della surface `produzioni` evitando il caricamento iniziale dell'intero storico e introducendo un contratto di query piu controllato.

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`
- `docs/task/TASK-V2-032-sync-on-demand-produzioni.md`
- `docs/task/TASK-V2-033-forza-completata-produzioni.md`

## Goal

Portare la surface `produzioni` a un comportamento piu sostenibile su dataset grandi, trattando lo storico come consultazione esplicita e non come parte del caricamento standard.

## Context

Nel comportamento attuale la vista `produzioni` risulta lenta, con alta probabilita perche il dataset storico e molto ampio.

Il primo correttivo scelto e:

- non mostrare le produzioni storiche di default

La surface deve aprirsi sulle sole produzioni attive, lasciando lo storico disponibile solo tramite filtro esplicito e query backend controllate.

## In Scope

- default della lista `produzioni` su `bucket=active`
- filtro esplicito `bucket` con almeno:
  - `active`
  - `historical`
  - `all`
- filtro `bucket` applicato lato backend/Core
- paginazione backend della lista `produzioni`
- aggiornamento UI per consumare la lista paginata
- caricamento del dettaglio solo per la produzione selezionata

## Out of Scope

- virtualizzazione avanzata frontend
- ricerca full-text avanzata
- scheduler automatico
- modifica della logica di `stato_produzione`
- modifica del flag `forza_completata`

## Constraints

- la UI non deve caricare tutto lo storico in apertura
- il filtro `bucket` non deve essere solo client-side
- la paginazione deve essere backend-driven
- la surface deve restare coerente con la spec UIX `produzioni`

## Acceptance Criteria

- la surface `produzioni` apre di default con sole produzioni `active`
- l'utente puo selezionare esplicitamente:
  - `active`
  - `historical`
  - `all`
- il backend supporta il filtro `bucket`
- il backend supporta paginazione della lista
- la UI consuma la lista paginata senza regressioni funzionali
- il dettaglio continua a caricarsi solo sulla riga selezionata
- `npm run build` passa senza errori

## Deliverables

- estensione query/backend per lista `produzioni`
- contratto API con filtro `bucket` e paginazione
- aggiornamento UI della surface `produzioni`
- eventuali test backend/frontend coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- estensioni del contratto query/API
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti
