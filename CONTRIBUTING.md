# Contributing To NSSP V2

Questo repository ospita la V2 come prodotto e base architetturale autonoma.

Prima di aprire modifiche:

- leggi [README.md](README.md)
- leggi [docs/charter/V2_CHARTER.md](docs/charter/V2_CHARTER.md)
- verifica i decision log attivi in [docs/decisions/](docs/decisions/)

## Regole di base

- non introdurre logica di business in `frontend/`
- non duplicare regole di dominio tra `sync/`, `core/` e `app/`
- `sync/` integra sorgenti esterne e scrive solo dati di sync o metadata di run
- `core/` contiene fatti canonici, computed facts, aggregate, stati, policy e orchestrazione
- `app/` espone API e workflow senza reimplementare la logica di dominio
- ogni decisione architetturale non banale deve lasciare traccia in `docs/decisions/`

## Workflow consigliato

1. Allinea la modifica a un task o a una decisione esistente.
2. Se la modifica cambia confini, responsabilita o regole, aggiorna o aggiungi un decision log.
3. Mantieni i commit piccoli e coerenti.
4. Apri una PR con contesto, impatto e rischi residui.

## Convenzioni pratiche

- backend Python sotto `backend/src/nssp_v2/`
- test backend organizzati per scopo in `backend/tests/`
- documentazione generale in `docs/`
- roadmap confermata in `docs/roadmap/FUTURE.md`
- idee aperte o non confermate in `docs/roadmap/POSSIBLE.md`

## Checklist minima prima della PR

- il cambiamento e descritto chiaramente
- i file toccati rispettano i confini `sync/core/app/shared`
- la documentazione e aggiornata se il comportamento cambia
- i test rilevanti sono stati eseguiti oppure e dichiarato cosa manca

## Casi che richiedono un decision log

- introduzione di un nuovo boundary applicativo
- spostamento di logica tra layer
- nuove regole di rebuild, stato o policy
- nuove convenzioni strutturali di repository o documentazione
