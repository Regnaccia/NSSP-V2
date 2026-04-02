# TASK-V2-001 — Bootstrap backend minimo V2

## Status
Completed

## Date
2026-04-02

## Owner
Claude Code

## Context

La repository V2 ha già una struttura documentale e architetturale valida:

- il `charter` definisce separazione forte tra `sync`, `core` e `app`
- il DL-ARCH-V2-001 fissa i confini repository e le regole di dipendenza
- il `README.md` descrive una struttura backend con `backend/src/nssp_v2/app`, `core`, `shared`, `sync`

Al momento però il backend non è ancora bootstrapato come progetto Python/FastAPI realmente eseguibile.

Prima di sviluppare facts, aggregate, rebuild o casi d’uso operativi, serve una base tecnica minima, pulita e coerente con i confini V2.

Questo task serve anche come test iniziale del workflow “task → Claude Code → implementazione”.

## Objective

Creare il bootstrap minimo del backend V2 in modo che il progetto sia:

- installabile come progetto Python
- avviabile con FastAPI
- con package structure coerente con `app/core/shared/sync`
- predisposto a PostgreSQL + Alembic
- pronto per i task successivi senza introdurre logica di dominio prematura

## Scope

### In scope

Creare o completare i seguenti elementi minimi:

- `backend/pyproject.toml`
- `backend/alembic.ini`
- struttura package Python sotto `backend/src/nssp_v2/`
- file `__init__.py` necessari
- `backend/src/nssp_v2/app/main.py`
- `backend/src/nssp_v2/app/api/` come base minima
- `backend/src/nssp_v2/shared/config.py`
- `backend/src/nssp_v2/shared/db.py`
- setup Alembic minimo funzionante
- cartelle test backend:
  - `backend/tests/unit/`
  - `backend/tests/integration/`
  - `backend/tests/contracts/`
  - `backend/tests/sync/`
- endpoint HTTP minimo:
  - `GET /health`
- endpoint HTTP minimo opzionale:
  - `GET /ready`
- file `.env.example` minimi lato backend

### Out of scope

Non implementare in questo task:

- logica EasyJob
- sync reale verso sorgenti esterne
- facts canonici
- computed facts
- aggregate
- workflow applicativi
- autenticazione
- modelli di dominio business
- policy operative
- projection frontend
- docker avanzato

## Architectural constraints

Rispettare rigorosamente i confini V2:

- `sync` non contiene logica operativa
- `core` non dipende da HTTP/FastAPI
- `app` non reimplementa logica di dominio
- `shared` contiene solo supporto tecnico

Dipendenze ammesse:

- `app -> core`
- `app -> shared`
- `core -> shared`
- `sync -> shared`

Dipendenze non ammesse:

- `core -> app`
- `core -> sync`
- `sync -> app`

## Expected directory target

backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   └── versions/
├── src/
│   └── nssp_v2/
│       ├── __init__.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── api/
│       │       ├── __init__.py
│       │       └── health.py
│       ├── core/
│       │   └── __init__.py
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── db.py
│       └── sync/
│           └── __init__.py
└── tests/
    ├── unit/
    ├── integration/
    ├── contracts/
    └── sync/

## Functional requirements

### FR1 — Python project bootstrap
Il backend deve essere configurato come progetto Python tramite `pyproject.toml`.

### FR2 — FastAPI app bootstrap
Deve esistere una FastAPI app avviabile.

### FR3 — Health endpoint
Deve esistere `GET /health` che restituisce:

{
  "status": "ok"
}

### FR4 — Config centralizzata
Configurazione runtime in `shared/config.py`.

### FR5 — DB bootstrap
Base SQLAlchemy per PostgreSQL.

### FR6 — Alembic bootstrap
Alembic configurato correttamente.

### FR7 — Test bootstrap
Almeno un test per `/health`.

## Non-functional requirements

- codice minimale e leggibile
- nessuna logica business
- naming coerente con `nssp_v2`
- import puliti
- base estendibile
- nessun shortcut architetturale

## Implementation notes

- usare FastAPI
- usare SQLAlchemy
- config via environment variables
- usare `.env.example`
- evitare file inutili
- mantenere `core/` e `sync/` minimali ma presenti

## Acceptance criteria

Il task è completato se:

1. backend installabile
2. app FastAPI avviabile
3. `/health` funzionante
4. struttura coerente con DL-ARCH-V2-001
5. config centralizzata presente
6. Alembic inizializzato
7. almeno un test funzionante
8. nessuna logica di dominio introdotta
9. il repo è pronto per i task successivi

## Deliverables

Claude Code deve produrre:

- file creati/modificati nel backend
- summary finale con:
  - cosa è stato creato
  - eventuali scelte tecniche
  - eventuali limiti volontari
  - suggerimenti per step successivo

## References

- README.md
- docs/charter/V2_CHARTER.md
- docs/decisions/ARCH/DL-ARCH-V2-001.md
- CONTRIBUTING.md

---

## Completion Notes

- summary: Bootstrap backend minimo completato. Progetto Python installabile, FastAPI avviabile, config centralizzata, DB bootstrap SQLAlchemy 2.0, Alembic configurato, 2 test unit passanti.
- files_changed:
  - `backend/pyproject.toml` — project config, dipendenze, pytest config
  - `backend/.env.example` — variabili d'ambiente con default documentati
  - `backend/alembic.ini` — configurazione Alembic (URL override in env.py)
  - `backend/alembic/env.py` — env Alembic, URL da shared/config, target Base.metadata
  - `backend/alembic/script.py.mako` — template migrazioni standard
  - `backend/src/nssp_v2/shared/config.py` — Settings via pydantic-settings, .env support
  - `backend/src/nssp_v2/shared/db.py` — engine, SessionLocal, Base, get_session()
  - `backend/src/nssp_v2/app/main.py` — FastAPI app con router health
  - `backend/src/nssp_v2/app/api/health.py` — GET /health, GET /ready
  - `__init__.py` per shared, core, sync, app, app/api, tests e sotto-cartelle test
  - `backend/tests/unit/test_health.py` — 2 test su /health e /ready
- verification: `pytest tests/unit/test_health.py -v` → 2 passed in 1.28s
- followups:
  - Scrivere DL-ARCH-V2-002 su contratto persistenza core (Base, modelli, convenzioni) prima di TASK-V2-002
  - TASK-V2-002 naturale: prime tabelle source facts (articoli, ordini, righe_ordine) con modelli SQLAlchemy e prima migrazione Alembic

## Completed At

2026-04-02

## Completed By

Claude Code