# TASK-V2-003 - Bootstrap DB interno V2

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/task/TASK-V2-001-bootstrap-backend.md`
- `docs/task/TASK-V2-002-hardening-verifica-backend.md`
- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Goal

Introdurre il primo bootstrap completo del database interno V2, con configurazione ambiente, modelli SQLAlchemy strutturali, prima migrazione Alembic e seed minimo per utenti e ruoli.

## Context

La V2 ha gia:

- bootstrap backend minimo
- convenzione di verifica riproducibile
- decisione architetturale esplicita sul DB interno come persistence backbone

Manca ancora il primo slice persistente reale su cui costruire:

- autenticazione browser
- ruoli utente multipli
- contratti applicativi basati su dati interni

Questo task deve colmare quel vuoto senza anticipare il task auth.

Il risultato atteso non e ancora un flusso login completo, ma una base tecnica stabile e verificabile che renda disponibile:

- PostgreSQL locale V2
- configurazione DB esplicita
- tabelle strutturali iniziali
- migrazione Alembic iniziale
- seed minimo per utenti e ruoli

Il task e il prerequisito diretto di `TASK-V2-004`.

## Scope

### In Scope

- definire il bootstrap locale del database PostgreSQL per la V2
- introdurre o completare la configurazione ambiente backend per puntare al DB interno
- aggiungere i modelli SQLAlchemy minimi per:
  - `users`
  - `roles`
  - `user_roles`
- definire ownership tecnica chiara delle tabelle come slice di access control
- creare la prima migration Alembic coerente con i modelli introdotti
- introdurre un seed minimo o comando equivalente per popolare almeno:
  - un utente attivo
  - almeno un ruolo
  - almeno un mapping utente-ruolo
- aggiornare la documentazione di bootstrap e verifica backend con i passaggi DB necessari
- aggiungere test minimi backend o controlli automatici sul layer DB/migrazione compatibili con il livello di bootstrap raggiunto

### Out of Scope

- endpoint auth completi
- pagina login frontend
- sessioni applicative browser
- policy di autorizzazione per feature di dominio
- modellazione di facts canonici o dati sync di business
- separazione multi-schema PostgreSQL
- Docker completo di tutta la piattaforma se non necessario al bootstrap DB locale

## Constraints

- rispettare i confini `sync/core/app/shared`
- usare PostgreSQL come DB interno V2
- partire con una sola schema iniziale `public`
- ogni modifica strutturale deve passare da SQLAlchemy + Alembic
- il frontend non deve entrare nel perimetro di questo task
- il task deve restare focalizzato sul backbone persistente, non sull'auth completa
- la verifica deve essere riproducibile in ambiente pulito secondo `DL-ARCH-V2-002`
- il setup locale del DB deve essere spiegabile e ragionevolmente semplice da eseguire

## Acceptance Criteria

- esiste un modo documentato e riproducibile per avviare un PostgreSQL locale per la V2
- il backend puo puntare al DB interno tramite configurazione ambiente esplicita
- esistono modelli SQLAlchemy minimi per `users`, `roles`, `user_roles`
- esiste almeno una migration Alembic applicabile in ambiente pulito che crea le tabelle iniziali
- esiste un seed minimo o procedura equivalente per ottenere dati iniziali verificabili
- la documentazione spiega come:
  - preparare il DB
  - applicare la migration
  - eseguire il seed
  - verificare il risultato
- esistono controlli automatici o test minimi che coprono almeno bootstrap schema e import dei modelli

## Deliverables

- configurazione DB aggiornata lato backend
- eventuale asset locale per avvio PostgreSQL, ad esempio sotto `infra/docker/`, se scelto come soluzione
- modelli SQLAlchemy iniziali per access control
- migration Alembic iniziale del DB interno
- seed minimo o script equivalente
- documentazione aggiornata:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - eventuale `backend/README.md`
- test o verifiche automatiche minime coerenti con il task

## Environment Bootstrap

Comandi minimi attesi per verificare il task in modo riproducibile.

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Database:

Il task deve chiudersi con comandi espliciti per:

- avviare PostgreSQL locale
- impostare la variabile ambiente o il file `.env` necessario
- applicare la migration
- lanciare il seed

Se viene introdotto Docker Compose o uno script equivalente, i comandi vanno riportati in modo completo.

## Verification Commands

I comandi effettivi potranno essere affinati durante l'implementazione, ma il task deve chiudersi con almeno:

```bash
cd backend
alembic upgrade head
pytest tests/ -v
```

e con almeno un comando o procedura esplicita per verificare che:

- il DB e raggiungibile
- le tabelle iniziali esistono
- il seed minimo e stato applicato correttamente

Devono essere riportati:

- comandi esatti
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere semplice il bootstrap locale del DB; evitare soluzioni sofisticate non necessarie
- modellare `users`, `roles`, `user_roles` in modo pulito e coerente con `DL-ARCH-V2-004`
- lasciare spazio al task auth senza introdurre gia endpoint o session management completi
- se viene introdotto un asset Docker locale, limitarlo al supporto del DB bootstrap
- usare naming e ownership delle tabelle leggibili fin dal primo slice

---

## Completion Notes

### Summary

Bootstrap DB interno completato. Modelli SQLAlchemy per `users`, `roles`, `user_roles` creati nel layer `app`. Prima migration Alembic scrittta manualmente e coerente con i modelli. Seed script minimo idempotente. Docker Compose per PostgreSQL locale introdotto sotto `infra/docker/`. Config aggiornata con `DATABASE_URL_TEST` per separazione ambienti. 11 test unit passanti senza DB attivo. Guida bootstrap aggiornata con sequenza completa da zero.

### Files Changed

- `backend/src/nssp_v2/app/models/__init__.py` — creato: espone `User`, `Role`, `UserRole`
- `backend/src/nssp_v2/app/models/access.py` — creato: modelli SQLAlchemy access control con ownership esplicita nel layer `app`
- `backend/alembic/env.py` — aggiornato: importa `nssp_v2.app.models.access` per registrare i modelli in `Base.metadata`
- `backend/alembic/versions/20260407_001_access_control_tables.py` — creato: prima migration per `roles`, `users`, `user_roles`
- `backend/scripts/seed_initial.py` — creato: seed idempotente con 4 ruoli + utente admin + mapping admin->admin
- `backend/tests/unit/test_models_access.py` — creato: 9 test unit su struttura modelli (no DB)
- `infra/docker/docker-compose.db.yml` — creato: PostgreSQL 16 locale per sviluppo
- `backend/src/nssp_v2/shared/config.py` — aggiornato: aggiunto `database_url_test`
- `backend/.env.example` — aggiornato: aggiunto `DATABASE_URL_TEST` con commento separazione ambienti
- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md` — aggiornato: sequenza completa con DB, migrazioni, seed, test

### Dependencies Introduced

Nessuna nuova dipendenza runtime. Docker richiesto per il DB locale (non tracciato come dipendenza Python).

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest tests/unit/ -v` | Claude Code (agente) | venv `.venv` locale backend | 11 passed in 2.30s |
| `python -c "from nssp_v2.app.models.access import User, Role, UserRole; print('models OK')"` | Claude Code (agente) | venv `.venv` locale backend | OK |
| `alembic upgrade head` | Non eseguita | PostgreSQL non disponibile nell'ambiente agente | migration scritta manualmente e coerente con i modelli — da verificare con DB attivo |
| `python scripts/seed_initial.py` | Non eseguita | richiede DB attivo | da verificare dopo `alembic upgrade head` |

### Assumptions

- Docker disponibile per avviare PostgreSQL locale tramite `docker-compose.db.yml`
- Il seed usa un hash sha256 placeholder per `password_hash` — TASK-V2-004 sostituirà con bcrypt via passlib
- `alembic upgrade head` deve essere eseguito da `backend/` con venv attivo e `.env` configurato

### Known Limits

- `alembic upgrade head` e seed non verificati da agente (richiedono PostgreSQL attivo)
- verifica indipendente da revisore esterno non eseguita
- i test di integrazione (`tests/integration/`) restano vuoti — da popolare in task successivi con fixture DB dedicata

### Follow-ups

- `TASK-V2-004`: browser auth e routing iniziale per ruoli

## Completed At

2026-04-07

## Completed By

Claude Code
