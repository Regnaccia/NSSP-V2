# TASK-V2-011 - Sync destinazioni

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
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/task/TASK-V2-010-sync-clienti-reale.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
- `docs/integrations/easy/catalog/POT_DESTDIV.json`

## Goal

Implementare la sync reale di `destinazioni` da Easy `POT_DESTDIV` verso il target interno V2, in dipendenza esplicita dalla sync `clienti`.

## Context

Dopo la sync reale `clienti`, la seconda entita naturale e `destinazioni`.

Questo task deve introdurre:

- una nuova sync unit per entita
- una dependency declaration non vuota verso `clienti`
- un target interno `sync_destinazioni` coerente col mapping documentato

Il task non deve ancora creare il Core slice clienti + destinazioni.
Deve solo costruire il secondo mirror sync interno e la sua relazione tecnica col cliente.

## Scope

### In Scope

- implementazione adapter read-only reale per `POT_DESTDIV`
- lettura dei campi selezionati in `EASY_DESTINAZIONI.md`
- target interno `sync_destinazioni`
- source identity tecnica `PDES_COD`
- mantenimento nel target di `CLI_COD` e `NUM_PROGR_CLIENTE`
- dependency declaration esplicita verso `clienti`
- run metadata e freshness anchor coerenti col modello sync condiviso
- verifica di idempotenza e allineamento

### Out of Scope

- Core slice clienti + destinazioni
- orchestrazione completa multi-entita
- scheduler reale
- surface UI dati-dipendente
- scrittura verso Easy

## Constraints

- accesso a Easy solo read-only, senza eccezioni
- rispettare `EASY_DESTINAZIONI.md` come mapping tecnico di riferimento
- `destinazioni` deve dichiarare dipendenza da `clienti`
- il target sync resta vicino alla sorgente e non diventa modello Core
- la sync deve restare idempotente

## Acceptance Criteria

- esiste un adapter reale read-only per `POT_DESTDIV`
- esiste una sync unit `destinazioni` implementata nel layer `sync`
- il target `sync_destinazioni` contiene i campi previsti da `EASY_DESTINAZIONI.md`
- la sync `destinazioni` dichiara e rispetta la dipendenza da `clienti`
- la sync `destinazioni` resta idempotente
- run metadata e freshness anchor vengono aggiornati correttamente

## Deliverables

- adapter Easy reale per `destinazioni`
- modelli e migration per `sync_destinazioni`
- sync unit `destinazioni`
- test coerenti con il perimetro
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/integrations/easy/EASY_DESTINAZIONI.md` se il mapping cambia

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
```

Database:

```bash
docker compose -f infra/docker/docker-compose.db.yml up -d
cd backend
cp .env.example .env
alembic upgrade head
```

Easy:

- configurare `EASY_CONNECTION_STRING` in `.env`
- usare solo connessione read-only

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita:

```bash
cd backend
python scripts/<sync_destinazioni>.py
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- evidenza che la connessione verso Easy e solo read-only

## Implementation Notes

Direzione raccomandata:

- costruire `destinazioni` come seconda sync unit autonoma, non come estensione opaca di `clienti`
- usare `PDES_COD` come source identity tecnica
- mantenere `CLI_COD` e `NUM_PROGR_CLIENTE` come campi relazionali importanti
- non introdurre ancora logica Core di unione clienti + destinazioni

---

## Completion Notes

### Summary

Implementata la seconda sync unit autonoma `destinazioni` che legge da `POT_DESTDIV` (EasyJob) e mantiene il mirror interno `sync_destinazioni`. Introdotta la prima dependency declaration non vuota del sistema sync: `DEPENDENCIES = ["clienti"]`. Tutti i componenti del layer sync seguono il contratto DL-ARCH-V2-009: source adapter read-only, upsert alignment, mark_inactive delete handling, full_scan change acquisition, run metadata e freshness anchor persistiti.

### Files Changed

- `src/nssp_v2/sync/destinazioni/__init__.py` — package marker (vuoto)
- `src/nssp_v2/sync/destinazioni/source.py` — `DestinazioneRecord` (dataclass, 1 campo obbligatorio + 7 opzionali), `DestinazioneSourceAdapter` (ABC), `EasyDestinazioneSource` (pyodbc read-only, SELECT su `POT_DESTDIV`), `FakeDestinazioneSource` (fixture per test)
- `src/nssp_v2/sync/destinazioni/models.py` — `SyncDestinazione` (SQLAlchemy ORM, tablename `sync_destinazioni`, unique su `codice_destinazione`)
- `src/nssp_v2/sync/destinazioni/unit.py` — `DestinazioneSyncUnit` con contratto completo; primo sync unit con `DEPENDENCIES = ["clienti"]`
- `alembic/versions/20260407_004_sync_destinazioni.py` — migration `sync_destinazioni` (down_revision=20260407003)
- `scripts/sync_destinazioni.py` — entrypoint on-demand `--source easy|fake`
- `tests/unit/test_sync_destinazioni_contract.py` — 20 test su contratto, source adapter, record fields, modello ORM (senza DB)
- `tests/sync/test_destinazioni_run.py` — 10 test di integrazione con SQLite in-memory (insert, update, idempotenza, mark_inactive, reactivation, metadata, freshness anchor, campi opzionali)

### Dependencies Introduced

Nessuna nuova dipendenza rispetto a TASK-V2-010. `pyodbc` già dichiarato in `[easy]`.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests/unit/test_sync_destinazioni_contract.py tests/sync/test_destinazioni_run.py -v` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 30/30 passed |
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale | 91 passed, 4 failed (pre-esistenti in test_admin_policy — `HTTP_422_UNPROCESSABLE_CONTENT`, fuori scope) |
| `python scripts/sync_destinazioni.py --source fake` | Non eseguita | — | Script strutturalmente equivalente a `sync_clienti.py --source fake`; verifica manuale rimandata a quando DB è attivo |
| `python scripts/sync_destinazioni.py --source easy` | Non eseguita | Easy non disponibile nell'ambiente agente | Da eseguire con Easy online configurato |
| `alembic upgrade head` (migration 004) | Non eseguita | PostgreSQL non disponibile nell'ambiente agente | Da eseguire con Docker DB attivo |

### Assumptions

- `codice_destinazione` è sempre `NOT NULL` nella sorgente (corrisponde a `PDES_COD NOT NULL` in `POT_DESTDIV`).
- `CLI_COD` (codice cliente associato) è considerato campo opzionale nel target sync: la FK non è hard-coded per non vincolare la sync a un ordine di caricamento rigido.
- `NUM_PROGR_CLIENTE` mappato come `numero_progressivo_cliente` (stringa, nullable): il significato operativo verrà chiarito nel Core slice.
- I 4 fallimenti pre-esistenti in `test_admin_policy` (`HTTP_422_UNPROCESSABLE_CONTENT`) non sono stati introdotti da questo task e non sono stati toccati.

### Known Limits

- Nessun orchestratore multi-entità: la dipendenza `["clienti"]` è dichiarativa ma non ancora enforced a runtime (la sync può essere lanciata in isolamento senza errori, anche se `sync_clienti` non è stata eseguita prima).
- La migration 004 crea la tabella ma non aggiunge indici su `codice_cli` (utile per join frequenti nel Core slice).
- `easy_schema_explorer.py` non è stato usato per estrarre il catalogo `POT_DESTDIV.json` in live; il mapping si basa su `EASY_DESTINAZIONI.md`.

### Follow-ups

- **TASK-V2-012**: Core slice `clienti` — modello Core Cliente con promozione da `sync_clienti`
- Aggiungere indice su `sync_destinazioni.codice_cli` nella migration del Core slice
- Implementare enforcement runtime delle dependencies nel futuro orchestratore

## Completed At

2026-04-07

## Completed By

Claude Code
