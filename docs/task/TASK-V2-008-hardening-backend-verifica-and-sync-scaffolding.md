# TASK-V2-008 - Hardening verifica backend e sync scaffolding

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
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/task/TASK-V2-007-bootstrap-sync-clienti.md`

## Goal

Rendere la verifica backend riproducibile in ambiente pulito e riallineare lo scaffolding sync in modo che le strutture comuni del layer `sync` non siano possedute dalla sola unit `clienti`.

## Context

La review di stato del progetto ha evidenziato due problemi concreti prima del primo caso applicativo reale:

- la verifica backend non e deterministica, perche i test dipendono dall'ambiente locale e dalla config caricata a import-time
- il primo scaffolding sync `clienti` contiene strutture comuni del layer `sync` in un package troppo specifico dell'entita

Nel dettaglio:

- `Settings()` viene istanziato a import-time e puo rompere la raccolta test quando il file `.env` o l'ambiente locale non e coerente
- `sync_run_log` e `sync_entity_state` sono oggi modellati dentro `sync/clienti`, ma sono concetti comuni del layer `sync` e non ownership esclusiva della singola entita

Prima di procedere con il primo caso applicativo sync reale, questi gap devono essere chiusi.

## Scope

### In Scope

- hardening della configurazione backend per evitare errori di raccolta test dovuti a ambiente locale sporco
- chiarimento e implementazione del bootstrap config/test in modo riproducibile
- eventuale introduzione di fixture, helper o convenzioni test che isolino il backend dal `.env` locale
- riallineamento dello scaffolding sync:
  - spostare strutture comuni del layer `sync` fuori dal package `clienti`
  - mantenere `clienti` come prima sync unit, ma senza possedere risorse globali
- aggiornamento di import, migrazioni, test e script necessari
- aggiornamento documentazione minima se i comandi di verifica cambiano

### Out of Scope

- nuova entita sync oltre `clienti`
- integrazione Easy reale online
- scheduler reale
- orchestrazione multi-entita completa
- surface UI dati-dipendente
- modellazione Core dei clienti

## Constraints

- rispettare `DL-ARCH-V2-002` sulla verifica riproducibile
- rispettare `DL-ARCH-V2-007`, `008`, `009` sul layer `sync`
- nessuna scrittura verso Easy e permessa in nessun caso
- le strutture comuni `sync` non devono creare dipendenze da una singola entita
- i test devono poter essere eseguiti da `V2/backend` senza dipendere dal repo root o da `V1`

## Acceptance Criteria

- i test backend raccolgono ed eseguono da `V2/backend` in ambiente pulito senza fallire per parsing config o `.env` locale incoerente
- esiste una convenzione chiara e documentata per la config di test backend
- `sync_run_log` e `sync_entity_state` non vivono piu nel package `sync/clienti`
- la sync unit `clienti` continua a funzionare dopo il riallineamento dello scaffolding
- `TASK-V2-007` non e piu bloccato da questi due problemi strutturali

## Deliverables

- hardening config/test backend
- eventuali fixture o helper per ambiente test
- refactor dello scaffolding sync condiviso
- aggiornamenti a modelli, import, migrazioni e test coinvolti
- aggiornamenti documentali minimi:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md` se necessario
  - eventuale nota in `docs/task/TASK-V2-007-bootstrap-sync-clienti.md`

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Database:

```bash
docker compose -f infra/docker/docker-compose.db.yml up -d
cd backend
cp .env.example .env
alembic upgrade head
```

Se il task introduce fixture o override env per i test, devono essere documentati esplicitamente.

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con una verifica esplicita che copra:

- raccolta test senza errori di config
- test unit backend eseguibili nel workdir corretto
- test sync `clienti` ancora funzionanti dopo il refactor shared

Devono essere riportati:

- comandi esatti
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- trattare la config di test come un contratto tecnico del progetto, non come side effect del `.env`
- evitare che moduli importati dai test istanzino config fragile senza controllo
- spostare le strutture comuni sync in un modulo shared del layer `sync`
- mantenere il refactor stretto: correggere ownership e verification, senza introdurre nuova business logic

---

## Completion Notes

### Summary

Due interventi ortogonali eseguiti:

**1. Config hardening:** `Settings()` ora è istanziato tramite `@lru_cache get_settings()` in `config.py`. `db.py` ora inizializza l'engine in modo lazy via `get_engine()` — importare `db.py` (per `Base` o i modelli) non crea più un engine PostgreSQL a import-time. Aggiunto `tests/conftest.py` che imposta env vars test-safe via `os.environ.setdefault()` prima che qualsiasi modulo applicativo venga importato, rendendo la raccolta test indipendente dal file `.env` locale.

**2. Sync scaffolding refactor:** `SyncRunLog` e `SyncEntityState` spostati da `sync/clienti/models.py` a `sync/models.py` (layer condiviso). `sync/clienti/models.py` li re-esporta per backward compat. Import aggiornati in `unit.py` e nei test (`test_clienti_run.py`, `test_sync_clienti_contract.py`). Nessuna modifica alla migrazione (i nomi tabella restano identici).

Verifica: `pytest tests -q` → **55 passed in 3.81s**, zero errori.

### Files Changed

**Config hardening:**
- `backend/src/nssp_v2/shared/config.py` — aggiornato: aggiunto `get_settings()` con `@lru_cache`, `settings` diventa alias di `get_settings()`
- `backend/src/nssp_v2/shared/db.py` — aggiornato: engine lazy via `get_engine()`, `SessionLocal` diventa funzione che crea `Session(get_engine())`
- `backend/tests/conftest.py` — creato: env vars test-safe via `os.environ.setdefault()`

**Sync scaffolding refactor:**
- `backend/src/nssp_v2/sync/models.py` — creato: `SyncRunLog`, `SyncEntityState` (ownership layer sync, non specifica di `clienti`)
- `backend/src/nssp_v2/sync/clienti/models.py` — aggiornato: rimossi `SyncRunLog` e `SyncEntityState`, re-esportati da `sync.models`
- `backend/src/nssp_v2/sync/clienti/unit.py` — aggiornato: import `SyncRunLog`, `SyncEntityState` da `sync.models`
- `backend/tests/sync/test_clienti_run.py` — aggiornato: import canonici da `sync.models`
- `backend/tests/unit/test_sync_clienti_contract.py` — aggiornato: import canonici da `sync.models` per i 4 test sui modelli condivisi

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | venv `.venv` locale backend | 55 passed in 3.81s |

### Assumptions

- Il re-export di `SyncRunLog` e `SyncEntityState` da `sync/clienti/models.py` garantisce backward compat per eventuali import esistenti non aggiornati
- `os.environ.setdefault()` in conftest.py è sufficiente: pydantic-settings assegna priorità alle env vars sul file `.env`, quindi i test non dipendono da un `.env` locale anche se presente
- `get_settings()` con `lru_cache` è già abbastanza robusto: in test, un futuro `get_settings.cache_clear()` consentirebbe di forzare ri-creazione con env vars modificate

### Known Limits

- `settings = get_settings()` in `config.py` è ancora una chiamata module-level: se `config.py` venisse importato prima che `conftest.py` si esegua (scenario anomalo), il singleton userebbe l'ambiente pre-conftest. Nella pratica pytest questo non accade
- La lazy engine non previene connessioni se il codice applicativo viene importato direttamente fuori da pytest (es. `python -c "import nssp_v2.app.main"`)

### Follow-ups

- Task successivo naturale: sync `destinazioni` (introduce dependency declaration non vuota su `clienti`) oppure primo caso applicativo surface logistica
- Se in futuro serve override totale dei settings nei test di integrazione, aggiungere una fixture pytest che chiami `get_settings.cache_clear()` + imposti env vars + li resetti in teardown

## Completed At

2026-04-07

## Completed By

Claude Code
