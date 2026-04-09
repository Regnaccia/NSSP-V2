# TASK-V2-053 - Refresh sequenziale articoli con commitments

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`
- `docs/task/TASK-V2-043-commitments-produzione.md`
- `docs/task/TASK-V2-047-refresh-articoli-con-ordini-per-set-aside.md`
- `docs/task/TASK-V2-049-core-availability.md`
- `docs/task/TASK-V2-051-refresh-sequenziale-articoli-con-availability.md`

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-051`

## Goal

Estendere il refresh manuale della surface `articoli` in modo che riallinei anche i `commitments`, sia da provenienza `customer_order` sia da provenienza `production`, prima del rebuild finale di `availability`.

## Context

Il refresh attuale della surface `articoli` riallinea:

1. `sync_articoli`
2. `sync_mag_reale`
3. `sync_righe_ordine_cliente`
4. `rebuild_inventory_positions`
5. `rebuild_customer_set_aside`
6. `rebuild_availability`

Questo lascia un limite noto:

- `committed_qty` mostrato nel dettaglio `articoli` puo restare stantio
- `availability` viene ricalcolata usando i `commitments` piu recenti presenti, ma non necessariamente aggiornati nello stesso refresh

Per avere una catena coerente servono entrambe le provenienze:

- `commitments cliente` da `righe_ordine_cliente`
- `commitments produzione` da `produzioni_attive`

Quindi la chain della surface `articoli` deve includere anche:

- `sync_produzioni_attive`
- `rebuild_commitments`

Questo task resta il fix operativo immediato. L'eventuale refactor verso refresh semantici backend con dipendenze interne e rinviato a un task successivo.

## Scope

### In Scope

- estensione del refresh backend della surface `articoli`
- aggiornamento della sequenza a:
  - `sync_articoli`
  - `sync_mag_reale`
  - `sync_righe_ordine_cliente`
  - `sync_produzioni_attive`
  - `rebuild_inventory_positions`
  - `rebuild_customer_set_aside`
  - `rebuild_commitments`
  - `rebuild_availability`
- tracciamento dello step `commitments` nella risposta backend
- aggiornamento della documentazione del flusso

### Out of Scope

- `sync_produzioni_storiche`
- scheduler automatico
- refresh parallelo
- nuovi endpoint separati per `commitments`
- nuove surface dedicate a `commitments`

## Constraints

- la UI continua a inviare una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- `commitments` va ricostruito solo dopo avere aggiornato sia `righe_ordine_cliente` sia `produzioni_attive`
- `availability` deve restare ultimo step, dopo `inventory`, `customer_set_aside` e `commitments`
- se `sync_righe_ordine_cliente` fallisce, `rebuild_customer_set_aside`, `rebuild_commitments` e `rebuild_availability` non devono partire
- se `sync_produzioni_attive` fallisce, `rebuild_commitments` e `rebuild_availability` non devono partire
- nessuna scrittura verso Easy
- il task deve mantenere separati:
  - `inventory_positions`
  - `customer_set_aside`
  - `commitments`
  - `availability`

## Acceptance Criteria

- il refresh della surface `articoli` esegue anche `sync_produzioni_attive`
- il refresh della surface `articoli` esegue anche `rebuild_commitments`
- `committed_qty` nel dettaglio `articoli` e coerente con l'ultimo refresh completato
- `availability` viene ricalcolata dopo `rebuild_commitments`
- la risposta backend rende tracciabili anche gli step `produzioni_attive` e `commitments`
- se fallisce uno step prerequisito, gli step downstream dipendenti risultano `skipped` o equivalenti e non producono nuovi dati
- `python -m pytest tests/app tests/core -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale aggiornamento della freshness della surface `articoli`
- eventuali test backend/frontend coerenti col task
- aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/guides/IMPLEMENTATION_PATTERNS.md`
  - `docs/SYSTEM_OVERVIEW.md`
  - `docs/roadmap/STATUS.md`

## Verification Level

`Mirata`

Questo task e un fix operativo intermedio e non una milestone di consolidamento.

Quindi:

- non richiede full suite obbligatoria
- richiede test backend mirati sul flusso refresh `articoli`
- richiede almeno una verifica frontend/build se il task tocca il contratto o il reload UI
- la full suite e rinviata alla milestone di refactor successiva (`TASK-V2-054`)

## Verification Commands

```bash
cd backend
python -m pytest tests/app tests/core -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- introdurre un helper `_run_commitments_rebuild(session)` nello stesso stile di inventory/set_aside/availability
- aggiungere `produzioni_attive` alla chain della surface `articoli` solo come prerequisito dei commitments produzione
- non introdurre `produzioni_storiche` nel refresh `articoli`: non serve ai commitments V1
- trattare questo task come fix operativo della chain attuale; il consolidamento in refresh semantici backend e oggetto di `TASK-V2-054`

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- nuova sequenza completa del refresh `articoli`
- gestione errori / step saltati
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

---

## Completion Notes

### File modificati

**Backend:**

- `src/nssp_v2/app/api/sync.py`
  - Import aggiunto: `from nssp_v2.core.commitments.queries import rebuild_commitments`
  - `_PRODUZIONE_ENTITIES`: aggiunto `"produzioni_attive"` (ora 4 entita sync)
  - Nuovo helper `_skipped_result(entity_code) -> EntityRunResult`: produce un risultato con `status="skipped"` per step saltati per dipendenza mancante
  - Nuovo helper `_run_commitments_rebuild(session) -> EntityRunResult`: stesso pattern di `_run_inventory_rebuild` e `_run_set_aside_rebuild`
  - `trigger_produzione`: riscritta con 8 step e logica condizionale; docstring aggiornata
  - Docstring modulo aggiornata: sequenza 8 step documentata

**Tests:**

- `tests/app/__init__.py` (nuovo)
- `tests/app/test_sync_produzione_helpers.py` (nuovo): 15 test

### Sequenza refresh produzione (finale — 8 step)

```
POST /api/sync/surface/produzione
  Step 1 — sync articoli                (EasyArticoloSource)
  Step 2 — sync mag_reale               (EasyMagRealeSource)
  Step 3 — sync righe_ordine_cliente    (EasyRigheOrdineClienteSource)
  Step 4 — sync produzioni_attive       (EasyProduzioneAttivaSource)       ← nuovo
  Step 5 — rebuild inventory_positions  (da mirror mag_reale aggiornato)
  Step 6 — rebuild customer_set_aside   (da righe_ordine_cliente)           [skip se step 3 non OK]
  Step 7 — rebuild commitments          (da ordini + produzioni)            [skip se step 3 o 4 non OK]  ← nuovo
  Step 8 — rebuild availability         (da inventory + set_aside + commitments) [skip se step 5/6/7 non OK]
```

Restituisce 8 `EntityRunResult`:
- `articoli`
- `mag_reale`
- `righe_ordine_cliente`
- `produzioni_attive`
- `inventory_positions`
- `customer_set_aside`
- `commitments`
- `availability`

### Gestione errori / step saltati

Ogni step di rebuild Core controlla lo status degli step upstream prima di procedere:

| Step | Condizione per esecuzione | Altrimenti |
|---|---|---|
| `rebuild_customer_set_aside` (6) | `righe_ordine_cliente == "success"` | `skipped` |
| `rebuild_commitments` (7) | `righe_ordine_cliente == "success"` AND `produzioni_attive == "success"` | `skipped` |
| `rebuild_availability` (8) | step 5 + 6 + 7 tutti `"success"` | `skipped` |

Uno step con `status="skipped"` non modifica il DB e non propaga errori.

### `_PRODUZIONE_ENTITIES` e freshness

`_PRODUZIONE_ENTITIES` ora include `produzioni_attive`: la freshness della surface produzione include anche l'entita `produzioni_attive`. Questo e coerente con il fatto che il refresh della surface aggiorna anche questo mirror.

### Test eseguiti

- `python -m pytest tests/app tests/core -q`: 264/264 passed
- `npm run build`: zero errori

### Test non eseguiti

- Test HTTP end-to-end per `trigger_produzione`: non inclusi. L'endpoint richiede TestClient + auth. La logica condizionale e coperta dai test degli helper direttamente (stesso pattern di TASK-V2-046).

### Assunzioni

- `_run_commitments_rebuild` segue lo stesso pattern di `_run_inventory_rebuild`: esegue fuori dal lock del SyncRunner (il concurrency guard copre solo le 4 sync unit Easy, non i rebuild Core).
- `freshness_produzione` ora traccia anche `produzioni_attive`: accettabile — e parte della catena di refresh.

### Limiti noti

- `produzioni_storiche` non e nella chain: i commitments produzione V1 usano solo le produzioni attive. Lo storico non contribuisce a `commitments`.
- La logica di skip e implementata nel router, non nel SyncRunner: il SyncRunner non sa nulla delle dipendenze tra step di rebuild Core. Il consolidamento in un orchestratore con dipendenze esplicite e oggetto di TASK-V2-054.

### Follow-up suggeriti

- `TASK-V2-054`: refactor verso refresh semantici backend con dipendenze dichiarate — astrae il pattern di skip in un orchestratore riusabile.

## Completed At

2026-04-09

## Completed By

Claude Code
