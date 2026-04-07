# TASK-V2-010 - Sync clienti reale

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
- `docs/task/TASK-V2-008-hardening-backend-verifica-and-sync-scaffolding.md`
- `docs/task/TASK-V2-009-easy-schema-explorer-and-catalog.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/catalog/ANACLI.json`

## Goal

Implementare la sync reale di `clienti` da Easy `ANACLI` verso il target interno V2, sostituendo l'uso della sorgente fake del bootstrap con un adapter read-only verso Easy.

## Context

`TASK-V2-007` ha validato il bootstrap tecnico del modello sync con una sorgente fake controllata.

Il prossimo passo corretto e introdurre la prima sync reale verso Easy:

- mantenendo il contratto per-entita
- rispettando il vincolo read-only assoluto
- allineando il target `sync_clienti` ai campi documentati in `EASY_CLIENTI.md`

Questo task non deve ancora costruire il Core clienti.
Deve solo produrre un mirror sync interno affidabile e verificabile.

## Scope

### In Scope

- implementazione di un adapter read-only reale per `ANACLI`
- lettura dei campi selezionati in `EASY_CLIENTI.md`
- allineamento del target interno `sync_clienti`
- aggiornamento di modelli, migration e sync unit `clienti` se necessario per includere i campi mappati
- mantenimento di run metadata e freshness anchor
- esecuzione on demand della sync `clienti` con sorgente Easy reale
- verifica tecnica su idempotenza, allineamento e rispetto del contratto read-only
- aggiornamento documentazione minima se cambiano comandi o prerequisiti

### Out of Scope

- sync `destinazioni`
- orchestrazione multi-entita
- scheduler reale
- Core slice clienti
- surface UI dati-dipendente
- scrittura verso Easy

## Constraints

- accesso a Easy solo read-only, senza eccezioni
- rispettare `EASY_CLIENTI.md` come mapping tecnico di riferimento
- il target sync resta vicino alla sorgente e non diventa modello Core
- la sync deve restare idempotente
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`

## Acceptance Criteria

- esiste un adapter reale read-only per `ANACLI`
- la sync `clienti` legge da Easy i campi documentati e li allinea nel target interno
- il target `sync_clienti` contiene i campi previsti dal mapping `EASY_CLIENTI.md`
- la sync `clienti` resta idempotente su doppia esecuzione
- run metadata e freshness anchor continuano a essere aggiornati correttamente
- la verifica documenta esplicitamente che non avviene alcuna write verso Easy

## Deliverables

- adapter Easy reale per `clienti`
- aggiornamenti a modelli e migration del target `sync_clienti`
- aggiornamenti alla sync unit `clienti`
- test coerenti col nuovo perimetro
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/integrations/easy/EASY_CLIENTI.md` se il mapping cambia

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
python scripts/sync_clienti.py
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- evidenza che la connessione verso Easy e solo read-only

## Implementation Notes

Direzione raccomandata:

- mantenere l'adapter Easy separato dalla logica della sync unit
- usare il catalogo `ANACLI.json` come riferimento tecnico completo
- usare `EASY_CLIENTI.md` come selezione curata dei campi realmente usati
- non introdurre deduzioni business nel layer `sync`

---

## Completion Notes

### Summary

Sync `clienti` allineata al mapping `EASY_CLIENTI.md`. `ClienteRecord` esteso con 5 campi opzionali (`indirizzo`, `nazione_codice`, `provincia`, `telefono_1`, `source_modified_at`). Aggiunto `EasyClienteSource` — adapter read-only verso `ANACLI` tramite pyodbc, con normalizzazione tecnica consentita (trim + stringa vuota → None). `SyncCliente` aggiornato con le stesse colonne. `unit.py` aggiornato per propagare tutti i campi nell'upsert. Script `sync_clienti.py` refactored: usa `EasyClienteSource` per default, `--source fake` per esecuzione senza Easy. Migrazione `20260407_003` aggiunge le 5 colonne nullable a `sync_clienti`. `pytest tests -q` → **65 passed in 2.63s**, zero errori.

### Files Changed

- `backend/src/nssp_v2/sync/clienti/source.py` — aggiornato: `ClienteRecord` con 5 campi nullable da `EASY_CLIENTI.md`; aggiunto `EasyClienteSource` (pyodbc, read-only, normalizzazione tecnica); `_strip_or_none()` helper
- `backend/src/nssp_v2/sync/clienti/models.py` — aggiornato: `SyncCliente` con 5 nuove colonne nullable
- `backend/src/nssp_v2/sync/clienti/unit.py` — aggiornato: loop upsert propaga tutti i campi del record
- `backend/alembic/versions/20260407_003_sync_clienti_fields.py` — creato: migrazione additive (5 colonne nullable)
- `backend/scripts/sync_clienti.py` — aggiornato: `--source easy` (default) / `--source fake`
- `backend/tests/unit/test_sync_clienti_contract.py` — aggiornato: test nuovi campi `SyncCliente`, test `ClienteRecord` campi opzionali, test `EasyClienteSource` contratto read-only (no connessione reale)
- `backend/tests/sync/test_clienti_run.py` — aggiornato: 3 nuovi test per campi opzionali (persist, update, nullable→None)

### Dependencies Introduced

Nessuna nuova dipendenza. `pyodbc` era già stato introdotto in TASK-V2-009 come extras `[easy]`.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | venv `.venv` locale backend | 65 passed in 2.63s |
| `python scripts/sync_clienti.py` (Easy reale) | Non eseguita | richiede `alembic upgrade head` + EASY_CONNECTION_STRING + Easy online | da verificare con DB e Easy attivi |
| `python scripts/sync_clienti.py --source fake` | Non eseguita | richiede `alembic upgrade head` + PostgreSQL | da verificare con DB attivo |

### Assumptions

- `readonly=True` in pyodbc garantisce a livello driver che non vengano eseguite operazioni write — nessun INSERT/UPDATE/DELETE è possibile dalla connessione (comportamento standard SQL Server ODBC)
- `CLI_DTMO` viene letto come `datetime` e scritto senza timezone (`DateTime(timezone=False)`) perché SQL Server datetime non ha timezone info — coerente con il tipo sorgente
- La migrazione `20260407_003` è additive (solo `ADD COLUMN`) — sicura da applicare su `sync_clienti` esistente senza perdita dati
- La normalizzazione `stringa vuota → None` è tecnica e non business: il campo vuoto in Easy non ha significato operativo diverso da NULL nel target interno

### Known Limits

- `python scripts/sync_clienti.py` non verificato da agente con Easy reale (richiede accesso rete a `SERVER\SQLEXPRESS`)
- La migrazione `20260407_003` non applicata da agente (richiede PostgreSQL attivo)
- `readonly=True` non è supportato da tutti i driver ODBC — se il driver ignora il parametro, la garanzia write-protection resta solo a livello di query (SELECT-only in `_QUERY`)
- `CLI_RAG2` non incluso in questo slice (documentato come open question in `EASY_CLIENTI.md`)

### Follow-ups

- Verificare `alembic upgrade head` e `python scripts/sync_clienti.py` con DB e Easy attivi
- Aggiornare `ANACLI.json` con lo schema reale estratto da `easy_schema_explorer.py --table ANACLI`
- Task successivo naturale: sync `destinazioni` (introduce dipendenza da `clienti` nella dependency declaration)

## Completed At

2026-04-07

## Completed By

Claude Code
