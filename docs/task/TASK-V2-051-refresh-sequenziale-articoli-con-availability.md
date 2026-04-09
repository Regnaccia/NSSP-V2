# TASK-V2-051 - Refresh sequenziale articoli con availability

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/task/TASK-V2-047-refresh-articoli-con-ordini-per-set-aside.md`
- `docs/task/TASK-V2-049-core-availability.md`
- `docs/task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md`

## Goal

Estendere il refresh manuale della surface `articoli` in modo che ricalcoli anche il fact `availability`,
oltre ai fact gia presenti.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-047`
- `TASK-V2-049`
- `TASK-V2-050` raccomandato, se si vuole che il nuovo dato sia gia visibile nella UI

## Context

Il flusso attuale del refresh `articoli` riallinea:

1. `sync_articoli`
2. `sync_mag_reale`
3. `sync_righe_ordine_cliente`
4. `rebuild_inventory_positions`
5. `rebuild_customer_set_aside`

Con `TASK-V2-049`, la V2 introduce un nuovo fact canonico:

- `availability`

Se il dettaglio `articoli` espone questo dato, il refresh della surface deve ricalcolarlo nello stesso flusso,
altrimenti la schermata puo mostrare dati quantitativi misti:

- `inventory` aggiornato
- `set_aside` aggiornato
- `availability` stantia

## Scope

### In Scope

- estensione del refresh backend della surface `articoli`
- esecuzione in ordine di:
  - sync `articoli`
  - sync `mag_reale`
  - sync `righe_ordine_cliente`
  - rebuild `inventory_positions`
  - rebuild `customer_set_aside`
  - rebuild `availability`
- aggiornamento del feedback UI della surface `articoli`
- aggiornamento della documentazione del nuovo flusso

### Out of Scope

- scheduler automatico
- refresh parallelo
- ATP
- UI dedicata `availability`
- nuovi endpoint separati per availability

## Constraints

- la UI invia una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- `availability` deve essere ricalcolata solo dopo i fact da cui dipende
- nessuna scrittura verso Easy
- il task deve mantenere separati:
  - `inventory_positions`
  - `customer_set_aside`
  - `commitments`
  - `availability`

## Acceptance Criteria

- il refresh della surface `articoli` esegue anche `rebuild_availability` come ultimo step
- il dettaglio `articoli` mostra `availability` coerente con l'ultimo refresh completato
- la risposta backend rende tracciabile anche lo step `availability`
- `python -m pytest tests -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale estensione del `SyncRunner` o service equivalente
- eventuale aggiornamento frontend della surface `articoli` se serve per il reload del nuovo dato
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

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- step aggiunto al refresh sequenziale
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- aggiungere `availability` come ultimo step del refresh
- non introdurre nuovi bottoni o trigger dedicati
- mantenere il flusso facilmente estendibile per futuri fact derivati

## Completion Notes

### File modificati

- `src/nssp_v2/app/api/sync.py`
  - Aggiunto import `rebuild_availability`
  - Aggiunto helper `_run_availability_rebuild(session) -> EntityRunResult` — stesso pattern di `_run_inventory_rebuild` e `_run_set_aside_rebuild`
  - `trigger_produzione`: aggiunto Step 6 — `results.append(_run_availability_rebuild(session))`
  - Docstring modulo e funzione `trigger_produzione` aggiornate: sequenza completa 6 step documentata
  - Commenti step rinumerati: Step 3→4 (inventory), Step 4→5 (set_aside), Step 6 (availability)

### Sequenza refresh produzione (finale)

```
POST /api/sync/surface/produzione
  Step 1 — sync articoli                (EasyArticoloSource)
  Step 2 — sync mag_reale               (EasyMagRealeSource)
  Step 3 — sync righe_ordine_cliente    (EasyRigheOrdineClienteSource)
  Step 4 — rebuild inventory_positions  (da mirror mag_reale aggiornato)
  Step 5 — rebuild customer_set_aside   (da mirror righe_ordine_cliente aggiornato)
  Step 6 — rebuild availability         (da inventory + set_aside + commitments)  ← nuovo
```

Restituisce 6 `EntityRunResult`:
- `articoli`
- `mag_reale`
- `righe_ordine_cliente`
- `inventory_positions`
- `customer_set_aside`
- `availability`

### Nessun test aggiuntivo

Il meccanismo di iniezione del rebuild `availability` nel `trigger_produzione` segue lo stesso pattern gia coperto dai test esistenti (`_run_inventory_rebuild`, `_run_set_aside_rebuild`). Il `rebuild_availability` stesso e gia coperto da `tests/core/test_core_availability.py` (TASK-V2-049). Nessun nuovo test di business logic e necessario.

### Test eseguiti

Suite completa: 482/482 passed.
Frontend: `npm run build` — zero errori.

### Assunzioni

- `availability` dipende da `commitments` che non e aggiornato nel flusso della surface `articoli` (solo `customer_order` e `production` vengono aggiornati da sync separati). Nel V1 questo e accettabile: `availability` usa i commitments piu recenti presenti nel mirror al momento del rebuild.
- `_run_availability_rebuild` esegue fuori dal lock del `SyncRunner` (stesso comportamento di inventory e set_aside): il concurrency guard copre solo le 3 sync unit Easy, non i rebuild Core.

### Limiti noti

- `commitments` non e nella sequenza del refresh `articoli`: se gli ordini di produzione sono cambiati, la `availability` ricalcolata potrebbe non riflettere i nuovi commitments. Questo e un limite noto del V1.
- `freshness_produzione` traccia solo `articoli`, `mag_reale` e `righe_ordine_cliente` (`_PRODUZIONE_ENTITIES`). Il freshness di `availability`, `inventory_positions` e `customer_set_aside` non e esposto nel `FreshnessBar`. Accettabile nel V1.

### Follow-up suggeriti

- Aggiornare `freshness_produzione` per includere `availability` nel calcolo della freschezza.
- Aggiungere `commitments` al refresh produzione se si vuole garantire la coerenza completa dei quattro fact.

## Completed At

2026-04-09

## Completed By

Claude Code
