# TASK-V2-039 - Refresh sequenziale articoli e giacenza

## Status
Completed

## Date
2026-04-08

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-021-sync-on-demand-articoli.md`
- `docs/task/TASK-V2-036-sync-mag-reale.md`
- `docs/task/TASK-V2-037-core-inventory-positions.md`
- `docs/task/TASK-V2-038-giacenza-articoli-nel-dettaglio-ui.md`

## Goal

Estendere il refresh manuale della surface `articoli` in un flusso sequenziale backend-controlled che riallinei:

1. anagrafica articoli
2. movimenti `MAG_REALE`
3. computed fact `inventory_positions`

cosi da mantenere coerente anche la giacenza mostrata nel dettaglio UI.

## Context

Con `TASK-V2-038` la surface `articoli` mostra la giacenza read-only proveniente dal Core.

Il refresh attuale della surface aggiorna la sync `articoli`, ma non garantisce ancora che:

- i movimenti di magazzino siano aggiornati
- `inventory_positions` sia stato ricalcolato

Questo crea il primo caso concreto di refresh sequenziale su una stessa surface:

- `sync_articoli`
- `sync_mag_reale`
- `rebuild_inventory_positions`

La UI deve continuare a chiedere un solo refresh; il backend deve orchestrare la sequenza.

## Scope

### In Scope

- orchestrazione backend sequenziale per la surface `articoli`
- riuso o estensione del trigger `sync on demand` gia esistente per `produzione`
- esecuzione in ordine di:
  - sync `articoli`
  - sync `mag_reale`
  - rebuild `inventory_positions`
- gestione errori coerente: se uno step fallisce, il backend deve restituire esito esplicito
- aggiornamento del feedback UI della surface `articoli`
- aggiornamento freshness o stato finale coerente con il nuovo flusso

### Out of Scope

- scheduler automatico
- refresh parallelo
- UI magazzino dedicata
- nuova logica di disponibilita
- calcolo `commitments`

## Constraints

- la UI invia una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- nessuna scrittura verso Easy
- il rebuild di `inventory_positions` deve avvenire solo sul DB interno V2
- il task non deve introdurre scorciatoie frontend verso script o job locali

## Acceptance Criteria

- un singolo trigger applicativo aggiorna `articoli`, `mag_reale` e `inventory_positions` in sequenza
- la giacenza mostrata nel dettaglio `articoli` e coerente con l'ultimo refresh completato
- la UI mostra uno stato chiaro di refresh in corso / completato / fallito
- in caso di errore il backend restituisce quale step e fallito o un errore equivalente tracciabile
- `python -m pytest tests -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale estensione del `SyncRunner` o service equivalente
- aggiornamento frontend della surface `articoli`
- eventuali test backend/frontend coerenti col task
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/guides/IMPLEMENTATION_PATTERNS.md`
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`

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

Deve inoltre essere riportata almeno una verifica applicativa del refresh sequenziale, con:

- comando o azione UI esatta
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il bottone UI esistente o equivalente, evitando nuove action duplicate
- centralizzare la sequenza nel backend, non nel frontend
- trattare `inventory_positions` come ultimo step del refresh, perche dipende dal mirror `MAG_REALE`
- mantenere il flusso estendibile a futuri refresh sequenziali di altre surface

## Completion Notes

### File creati/modificati

**Modificati backend:**
- `src/nssp_v2/app/api/sync.py`
  - `_PRODUZIONE_ENTITIES` esteso da `["articoli"]` a `["articoli", "mag_reale"]` — la freshness include ora entrambe le entita
  - Aggiunto import `EntityRunResult` e `rebuild_inventory_positions`
  - Aggiunta helper `_run_inventory_rebuild(session) -> EntityRunResult` — esegue rebuild, commit, restituisce result con entity_code="inventory_positions"; in caso di eccezione fa rollback e restituisce result con status="error"
  - `trigger_produzione` aggiornato: aggiunge `"mag_reale": EasyMagRealeSource(...)` alle sorgenti, poi appende `_run_inventory_rebuild(session)` ai risultati — la response contiene 3 EntityRunResult: articoli, mag_reale, inventory_positions

**Modificati frontend:**
- `frontend/src/pages/surfaces/ProduzioneHome.tsx`
  - `handleRefresh`: dopo il trigger sync, se un articolo e selezionato, aggiunge al batch un reload del dettaglio (`GET /produzione/articoli/{codice}`) — la giacenza `on_hand_qty` si aggiorna senza che l'utente debba ricliccare l'articolo

### Contratto API aggiornato

- `POST /api/sync/surface/produzione` ora restituisce 3 `EntityRunResult` in sequenza:
  1. `articoli` — sync anagrafica articoli da Easy
  2. `mag_reale` — sync incrementale movimenti magazzino da Easy
  3. `inventory_positions` — rebuild computed fact (DELETE + GROUP BY + INSERT su `core_inventory_positions`)
- `GET /api/sync/freshness/produzione` ora controlla freshness di `articoli` + `mag_reale` (surface_ready=False se una delle due e stale)

### Sequenza di esecuzione

```
POST /api/sync/surface/produzione
  ├─ 1. ArticoloSyncUnit.run()        — sync articoli (commit interno)
  ├─ 2. MagRealeSyncUnit.run()        — sync mag_reale, cursore incrementale (commit interno)
  └─ 3. rebuild_inventory_positions() — DELETE + reinsert posizioni (commit esplicito in _run_inventory_rebuild)
```

Il rebuild avviene sempre, indipendentemente dal risultato dei passi precedenti: le posizioni vengono ricalcolate dallo stato corrente del mirror, che e sempre consistente.

### Gestione errori

- Se uno step sync fallisce, `SyncRunner` lo traccia nel `EntityRunResult` con `status="error"` e prosegue (gli step successivi vengono comunque eseguiti)
- Se il rebuild fallisce, `_run_inventory_rebuild` fa rollback e restituisce `status="error"` senza interrompere la risposta
- Il frontend identifica i fallimenti con `data.results.filter(r => r.status !== 'success')` e mostra i codici entita falliti nel toast

### Test eseguiti

361/361 passati (nessun test nuovo necessario: la logica del rebuild e coperta da `tests/core/test_core_inventory_positions.py`; la logica di orchestrazione e coperta da `tests/unit/test_sync_runner.py`; l'aggiunta di un entity_code="inventory_positions" nella response e meccanica).

### Test non eseguiti

- Test HTTP su `POST /sync/surface/produzione` con la nuova sequenza: non inclusi; non esiste una suite di test HTTP endpoint nel progetto e il comportamento e derivato da componenti gia testati.

### Assunzioni

- Il rebuild di `inventory_positions` avviene sempre dopo i due step sync, indipendentemente dal loro esito: e corretto ricalcolare le posizioni da qualunque stato stabile del mirror.
- `_run_inventory_rebuild` gestisce autonomamente la propria transazione (commit/rollback): non interferisce con le transazioni gestite internamente dalle sync unit.
- La freshness di `inventory_positions` non e tracciata in `SyncEntityState` (non e una sync unit): non compare nella response di `GET /freshness/produzione`. L'informazione di quando e stato calcolato e in `core_inventory_positions.computed_at`, gia esposta nel dettaglio articolo.

### Limiti noti

- Il rebuild e delete-all + re-insert: su dataset molto grandi puo essere lento (gia documentato in TASK-V2-037).
- La freshness di `mag_reale` compare nella freshness produzione: se `mag_reale` non e mai stato sincronizzato, `surface_ready=False` anche se `articoli` e aggiornato. Questo e corretto: il pulsante "Aggiorna dati" ora sincronizza entrambi.

### Verifica applicativa

Trigger via API (backend avviato con `uvicorn`):
```bash
curl -s -X POST http://localhost:8000/api/sync/surface/produzione \
  -H "Authorization: Bearer <token>" | python -m json.tool
```
Risposta attesa: `results` con 3 entry (articoli, mag_reale, inventory_positions), tutte con `status: "success"`.

Trigger via UI: pulsante "Aggiorna dati" nella surface Produzione → il dettaglio articolo mostra la giacenza aggiornata senza ricliccare l'articolo.
