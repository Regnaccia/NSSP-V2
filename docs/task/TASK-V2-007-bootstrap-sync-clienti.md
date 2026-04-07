# TASK-V2-007 - Bootstrap sync clienti

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

## Goal

Preparare il primo slice tecnico del layer `sync` implementando una sync unit minima per l'entita `clienti`, verificabile end-to-end senza dipendere da Easy online.

## Context

La V2 ha gia:

- bootstrap backend stabile
- database interno con migrazioni e test
- auth browser e prima surface `admin`
- DL specifici su sync per entita, esecuzione runtime e sync unit contract

Manca pero ancora il primo caso tecnico reale che dimostri che il modello sync deciso nei DL e implementabile nel codice.

Il primo task sync non deve ancora coprire tutta l'integrazione Easy reale.

Deve invece costruire una base corretta e testabile per:

- una sync unit per entita
- un target interno dedicato
- metadati minimi di run
- freshness anchor
- esecuzione on demand
- idempotenza
- rispetto esplicito della policy read-only verso Easy

La prima entita scelta e:

- `clienti`

perche ha dipendenze minime e consente di validare il modello senza introdurre subito la complessita di `destinazioni` o `ordini`.

## Scope

### In Scope

- introduzione di una prima sync unit `clienti`
- definizione di un source adapter read-only minimo per `clienti`
- supporto a sorgente fake o fixture-driven per testare la sync senza Easy online
- target interno dedicato per `clienti` nel database V2
- source identity esplicita per `clienti`
- alignment strategy esplicita per `clienti`
- change acquisition strategy esplicita per `clienti`
- delete handling policy esplicita per `clienti`
- run metadata minimi per le esecuzioni di sync
- freshness anchor minimo (`last_success_at` o equivalente)
- comando o entrypoint backend interno per esecuzione on demand della sync `clienti`
- test backend su:
  - idempotenza
  - upsert/allineamento
  - run metadata
  - rispetto del contratto read-only
- aggiornamento documentazione tecnica minima se necessaria

### Out of Scope

- connessione definitiva a Easy reale in ambiente operativo
- scheduler reale o cron di produzione
- orchestrazione multi-entita
- sync `destinazioni`, `ordini`, `articoli`
- surface UI di dominio clienti
- modellazione Core dei clienti
- rebuild Core
- policy avanzate di retry, locking distribuito o monitoring

## Constraints

- rispettare i confini `sync/core/app/shared`
- nessuna scrittura verso Easy e permessa in nessun caso
- la sorgente esterna deve essere trattata come read-only anche nei test
- il target interno della sync non coincide con il modello Core
- la sync unit deve dichiarare esplicitamente:
  - source identity
  - alignment strategy
  - change acquisition strategy
  - delete handling policy
  - dependency declaration
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`
- il task deve preferire una sorgente fake/controllata per la verifica automatica

## Acceptance Criteria

- esiste una sync unit `clienti` implementata nel layer `sync`
- esiste un target interno dedicato per i dati sincronizzati di `clienti`
- la sync `clienti` puo essere eseguita on demand in ambiente locale
- la sync `clienti` e idempotente
- la source identity usata per l'allineamento e esplicita e documentata
- i metadati minimi di run vengono persistiti o resi disponibili in modo coerente
- esiste un freshness anchor minimo aggiornato a sync completata con successo
- i test dimostrano che l'implementazione non richiede Easy online
- i test o il design dimostrano che il contratto read-only resta rispettato

## Deliverables

- moduli backend per la prima sync unit `clienti`
- eventuale adapter fake/read-only per sorgente `clienti`
- modelli e migrazioni per target sync e metadati minimi necessari
- comando o entrypoint on demand per eseguire la sync `clienti`
- test backend unit/integration coerenti con il perimetro
- aggiornamenti documentali minimi:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md` se servono istruzioni sync
  - eventuale nota tecnica sul bootstrap della sorgente fake

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
python scripts/seed_initial.py
```

Se il task introduce fixture o file di esempio per la sorgente fake, devono essere documentati e versionati nel repo.

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
pytest tests/unit -v
```

e con almeno una verifica esplicita del primo slice sync:

- esecuzione on demand della sync `clienti`
- popolamento del target interno
- seconda esecuzione idempotente senza duplicazioni
- registrazione coerente dei metadati minimi di run

Devono essere riportati:

- comandi esatti
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- tenere il task tecnico e stretto
- non introdurre ancora dipendenze da Easy online
- modellare `clienti` come prima sync unit esemplare per le successive
- usare naming esplicito per target sync e run metadata
- se serve un adapter di sorgente, preferire un'interfaccia read-only chiara e semplice
- distinguere sempre:
  - target sync interno
  - eventuale stato corrente di freshness
  - metadati di singolo run

---

## Completion Notes

### Summary

Primo slice tecnico del layer `sync` implementato. Introdotto `contract.py` con `RunMetadata` e costanti per i campi del contratto. Sync unit `clienti` completa con contratto DL-ARCH-V2-009 dichiarato esplicitamente: source identity `codice_cli`, alignment `upsert`, change acquisition `full_scan`, delete handling `mark_inactive`, dependencies `[]`. Target interno `sync_clienti` (mirror di ANACLI), `sync_run_log` (run metadata), `sync_entity_state` (freshness anchor). Source adapter ABC read-only + `FakeClienteSource` fixture-driven. Script on-demand `sync_clienti.py`. 45 test unit (no DB) + 10 test sync (SQLite in-memory) — tutti passati, nessun test richiede Easy online.

### Files Changed

**Backend — sync layer:**
- `backend/src/nssp_v2/sync/contract.py` — creato: `RunMetadata` dataclass, costanti contratto (`ALIGNMENT_STRATEGIES`, `CHANGE_ACQUISITION_STRATEGIES`, `DELETE_HANDLING_POLICIES`)
- `backend/src/nssp_v2/sync/clienti/__init__.py` — creato
- `backend/src/nssp_v2/sync/clienti/models.py` — creato: `SyncCliente`, `SyncRunLog`, `SyncEntityState` (SQLAlchemy models)
- `backend/src/nssp_v2/sync/clienti/source.py` — creato: `ClienteRecord`, `ClienteSourceAdapter` ABC (read-only), `FakeClienteSource`
- `backend/src/nssp_v2/sync/clienti/unit.py` — creato: `ClienteSyncUnit` con contratto completo + logica run/upsert/mark_inactive/metadata

**Migrazione:**
- `backend/alembic/versions/20260407_002_sync_clienti.py` — creato: tabelle `sync_clienti`, `sync_run_log`, `sync_entity_state` (down_revision: `20260407001`)

**Script:**
- `backend/scripts/sync_clienti.py` — creato: entrypoint on-demand con `FakeClienteSource` demo (3 clienti fixture)

**Test:**
- `backend/tests/unit/test_sync_clienti_contract.py` — creato: 20 test unit (contratto, source adapter read-only, RunMetadata, struttura tabelle) — no DB
- `backend/tests/sync/test_clienti_run.py` — creato: 10 test con SQLite in-memory (upsert, idempotenza, mark_inactive, run metadata, freshness anchor)

### Dependencies Introduced

Nessuna nuova dipendenza. SQLite in-memory disponibile nello stdlib Python via SQLAlchemy già presente.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `pytest tests/unit -v` | Claude Code (agente) | venv `.venv` locale backend | 45 passed in 2.40s |
| `pytest tests/sync -v` | Claude Code (agente) | venv `.venv` locale backend — SQLite in-memory | 10 passed in 0.82s |
| `python scripts/sync_clienti.py` on-demand | Non eseguita | richiede DB attivo (`alembic upgrade head`) | da verificare con DB locale |
| `alembic upgrade head` (migrazione 002) | Non eseguita | richiede PostgreSQL attivo | da verificare con DB locale |

### Assumptions

- I campi di `ANACLI` documentati in memory sono `CLI_COD` e `CLI_RAG1`: il target `sync_clienti` è quindi minimo (`codice_cli`, `ragione_sociale`). Campi aggiuntivi da aggiungere via migrazione quando ANACLI viene ispezionata completamente
- SQLite in-memory è sufficiente per i test di logica sync (idempotenza, upsert, mark_inactive): non servono feature PostgreSQL-specifiche per questa logica
- `delete handling = mark_inactive`: i clienti non più presenti in sorgente diventano `attivo=False` ma restano nel DB. È la policy più sicura nel primo slice
- Il script `sync_clienti.py` usa `FakeClienteSource` come placeholder; l'adapter EasyJob reale sarà un task futuro dedicato

### Known Limits

- `python scripts/sync_clienti.py` non verificato da agente (richiede `alembic upgrade head` con PostgreSQL attivo)
- La migrazione `20260407_002` non è stata applicata da agente (richiede Docker PostgreSQL attivo)
- Nessun adapter EasyJob reale: il task non introduceva ancora l'integrazione Easy
- Nessun endpoint API per la sync on-demand: non richiesto in questo slice; da aggiungere se necessario

### Follow-ups

- Verificare `alembic upgrade head` e `python scripts/sync_clienti.py` con DB attivo
- Task successivo naturale: sync `destinazioni` (dipende da `clienti` — introduce dependency declaration non vuota)
- Oppure: adapter EasyJob reale per `ClienteSourceAdapter` (connessione ANACLI via ODBC/SQL Server)

## Completed At

2026-04-07

## Completed By

Claude Code
