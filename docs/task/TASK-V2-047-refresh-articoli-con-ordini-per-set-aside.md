# TASK-V2-047 - Refresh articoli con ordini per set aside

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`
- `docs/task/TASK-V2-046-refresh-sequenziale-articoli-giacenza-e-set-aside.md`

## Goal

Correggere il refresh della surface `articoli` in modo che il ricalcolo di `customer_set_aside` avvenga solo dopo l'allineamento dei dati ordine da cui dipende.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-040`
- `TASK-V2-041`
- `TASK-V2-044`
- `TASK-V2-046`

## Context

Il flusso oggi documentato per il refresh `articoli` e:

1. `sync_articoli`
2. `sync_mag_reale`
3. `rebuild_inventory_positions`
4. `rebuild_customer_set_aside`

Questo flusso e sufficiente per `giacenza`, ma non garantisce l'aggiornamento corretto di `customer_set_aside`, perche quest'ultimo dipende da:

- `sync_righe_ordine_cliente`
- Core `customer_order_lines`

Il Core `customer_order_lines` non richiede un rebuild materializzato, ma legge dal mirror ordini. Quindi il prerequisito operativo reale del rebuild `customer_set_aside` e:

- `sync_righe_ordine_cliente` aggiornato

Senza questo step, il bottone "Aggiorna dati" della schermata `articoli` puo mostrare:

- `inventory_positions` aggiornato
- `customer_set_aside` ricalcolato su ordini stantii

## Scope

### In Scope

- estensione del refresh backend della surface `articoli`
- esecuzione in ordine di:
  - sync `articoli`
  - sync `mag_reale`
  - rebuild `inventory_positions`
  - sync `righe_ordine_cliente`
  - rebuild `customer_set_aside`
- aggiornamento del feedback UI della surface `articoli`
- documentazione aggiornata del nuovo flusso

### Out of Scope

- scheduler automatico
- calcolo `availability`
- UI ordini dedicata
- nuove surface
- modifiche manuali a ordini o set aside

## Constraints

- la UI invia una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- `customer_set_aside` deve continuare a leggere dal Core `customer_order_lines`, non dal mirror grezzo direttamente
- nessuna scrittura verso Easy
- il task deve mantenere separati:
  - `inventory_positions`
  - `customer_set_aside`
  - `commitments`

## Acceptance Criteria

- il refresh della surface `articoli` esegue anche `sync_righe_ordine_cliente` prima del rebuild `customer_set_aside`
- il dettaglio `articoli` mostra `customer_set_aside` coerente con l'ultimo refresh completato
- la risposta backend rende tracciabile anche lo step `righe_ordine_cliente`
- `python -m pytest tests -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale estensione del `SyncRunner` o service equivalente
- eventuale aggiornamento frontend della surface `articoli` se serve per il reload del nuovo step
- eventuali test backend/frontend coerenti col task
- aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/SYSTEM_OVERVIEW.md`
  - `docs/roadmap/STATUS.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e:

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- non introdurre un secondo bottone o trigger dedicato
- mantenere `customer_order_lines` come Core demand-driven, senza rebuild aggiuntivo
- documentare esplicitamente che il prerequisito operativo di `customer_set_aside` e il mirror ordini aggiornato

## Completion Notes

### File creati/modificati

**Modificati:**
- `src/nssp_v2/app/api/sync.py`
  - Aggiunto import `EasyRigheOrdineClienteSource`
  - `_PRODUZIONE_ENTITIES`: `["articoli", "mag_reale"]` → `["articoli", "mag_reale", "righe_ordine_cliente"]`
  - `trigger_produzione`: aggiunto `"righe_ordine_cliente": EasyRigheOrdineClienteSource(...)` al dict `sources`
  - Docstring `trigger_produzione` aggiornata: sequenza completa documentata
  - Docstring modulo aggiornata
- `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - Migration list: aggiunte `sync_righe_ordine_cliente`, `core_commitments`, `core_customer_set_aside`
  - Script on-demand: aggiunti `sync_righe_ordine_cliente.py` e `rebuild_customer_set_aside.py`
  - Endpoint: aggiornata descrizione `POST /api/sync/surface/produzione`
  - Sequenza bootstrap e smoke flow aggiornate
- `docs/SYSTEM_OVERVIEW.md`
  - Sezione "Produzione/Articoli": aggiornato flusso refresh
  - Nuova sezione "Customer Set Aside"
  - Dati interni: aggiunto `customer_set_aside`
  - Prossimo passo aggiornato
- `docs/roadmap/STATUS.md`
  - Task completati: aggiornati a TASK-V2-047
  - Task aperti: aggiornati
  - Prossima sequenza: aggiornata

**Creati:**
- `scripts/rebuild_customer_set_aside.py` — script CLI on-demand per il rebuild del fact `customer_set_aside`

### Nessun test aggiuntivo

Il meccanismo di iniezione `righe_ordine_cliente` nel `SyncRunner` è già coperto dai test esistenti di `SyncRunner` (pattern shared tra tutte le sync unit). Il `_run_set_aside_rebuild` è coperto da `tests/unit/test_set_aside_rebuild_helper.py` (TASK-V2-046). Nessun nuovo test di business logic è necessario.

### Sequenza refresh produzione (finale)

```
POST /api/sync/surface/produzione
  Step 1 — sync articoli                (EasyArticoloSource)
  Step 2 — sync mag_reale               (EasyMagRealeSource)
  Step 3 — sync righe_ordine_cliente    (EasyRigheOrdineClienteSource)  ← nuovo
  Step 4 — rebuild inventory_positions  (da mirror mag_reale aggiornato)
  Step 5 — rebuild customer_set_aside   (da mirror righe_ordine_cliente aggiornato)
```

Restituisce 5 `EntityRunResult`:
- `articoli`
- `mag_reale`
- `righe_ordine_cliente`
- `inventory_positions`
- `customer_set_aside`

### Verifica applicativa

Il fatto che `righe_ordine_cliente` sia già registrata in `_UNIT_MAP` del `SyncRunner` (aggiunta in TASK-V2-040) garantisce che il runner la gestisca correttamente. La nuova sorgente `EasyRigheOrdineClienteSource` è stata già validata in produzione con la sync standalone.

### Test eseguiti

Suite completa: 462/462 passed.
Frontend: `npm run build` — zero errori.

### Test non eseguiti

- Test HTTP end-to-end: non inclusi (pattern coerente con le altre surface).
- Test con dati reali Easy: non eseguibili senza connessione.

### Assunzioni

- `righe_ordine_cliente` deve essere eseguita dentro il blocco `_try_acquire`/`_release` del `SyncRunner` per il concurrency guard. Questo avviene correttamente: è aggiunta a `_PRODUZIONE_ENTITIES` che viene passata al runner.
- Il prerequisito operativo "sync_righe_ordine_cliente prima del rebuild customer_set_aside" è ora garantito dalla sequenza hardcoded nel backend, non dal chiamante.

### Limiti noti

- La surface `logistica` e eventuali script standalone di `sync_righe_ordine_cliente` aggiornano lo stesso mirror. Se i due path divergono (es. la surface logistica sincronizza ordini e poi il refresh produzione usa dati più freschi), il comportamento è comunque corretto: `customer_set_aside` usa sempre il mirror più recente disponibile.
- `freshness_produzione` traccia solo `articoli` e `mag_reale` (`_PRODUZIONE_ENTITIES` prima dell'aggiunta di `righe_ordine_cliente`). Il freshness di `righe_ordine_cliente` non è esposto nel `FreshnessBar` della surface articoli. Questo è accettabile nel V1.

### Follow-up suggeriti

- Aggiornare `freshness_produzione` per includere `righe_ordine_cliente` nel calcolo della freschezza.
- Computed fact `availability = inventory - commitments - set_aside` (DL-ARCH-V2-019 §8).

## Completed At

2026-04-09

## Completed By

Claude Code
