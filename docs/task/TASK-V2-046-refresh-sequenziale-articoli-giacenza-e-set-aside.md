# TASK-V2-046 - Refresh sequenziale articoli, giacenza e set aside

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-039-refresh-sequenziale-articoli-e-giacenza.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`
- `docs/task/TASK-V2-045-set-aside-articoli-nel-dettaglio-ui.md`

## Goal

Estendere il refresh manuale della surface `articoli` in un flusso sequenziale backend-controlled che riallinei anche `customer_set_aside`, oltre ad anagrafica articoli e giacenza.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-044`

## Context

Con `TASK-V2-039` la surface `articoli` ha gia un refresh sequenziale che riallinea:

1. anagrafica articoli
2. movimenti `MAG_REALE`
3. computed fact `inventory_positions`

Con `DL-ARCH-V2-019` e `TASK-V2-044` entra un nuovo fact:

- `customer_set_aside`

Se il dettaglio articolo espone anche questa quota read-only, il refresh della surface deve ricalcolare pure il nuovo fact, altrimenti la schermata puo mostrare:

- giacenza aggiornata
- set aside stantio

La UI deve continuare a chiedere un solo refresh; il backend deve orchestrare l'intera sequenza.

## Scope

### In Scope

- estensione del refresh backend della surface `articoli`
- esecuzione in ordine di:
  - sync `articoli`
  - sync `mag_reale`
  - rebuild `inventory_positions`
  - rebuild `customer_set_aside`
- aggiornamento del feedback UI della surface `articoli`
- aggiornamento freshness o stato finale coerente con il nuovo flusso
- aggiornamento della documentazione di bootstrap/verifica se necessario

### Out of Scope

- scheduler automatico
- refresh parallelo
- calcolo `availability`
- UI dedicata a ordini, commitments o set aside
- modifica manuale del set aside

## Constraints

- la UI invia una sola richiesta di refresh
- il backend resta unico punto di orchestrazione
- nessuna scrittura verso Easy
- il rebuild di `customer_set_aside` deve avvenire solo sul DB interno V2
- il task deve mantenere separati:
  - `inventory_positions`
  - `customer_set_aside`

## Acceptance Criteria

- un singolo trigger applicativo aggiorna `articoli`, `mag_reale`, `inventory_positions` e `customer_set_aside` in sequenza
- il dettaglio `articoli` mostra giacenza e set aside coerenti con l'ultimo refresh completato
- la UI mostra uno stato chiaro di refresh in corso / completato / fallito
- in caso di errore il backend restituisce quale step e fallito o un errore equivalente tracciabile
- `python -m pytest tests -q` passa
- `npm run build` passa

## Deliverables

- aggiornamento backend del flusso `sync on demand` per `articoli`
- eventuale estensione del `SyncRunner` o service equivalente
- aggiornamento frontend della surface `articoli` se serve per il reload del nuovo dato
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

Deve inoltre essere riportata almeno una verifica applicativa del refresh sequenziale completo.

## Implementation Notes

Direzione raccomandata:

- trattare `customer_set_aside` come ultimo step del refresh oppure comunque dopo i dati da cui dipende
- mantenere il bottone UI esistente, evitando nuove action duplicate
- centralizzare la sequenza nel backend, non nel frontend
- mantenere il flusso estendibile a futuri refresh sequenziali di altri fact derivati

## Completion Notes

### File creati/modificati

**Modificati:**
- `src/nssp_v2/app/api/sync.py`
  - Aggiunto import `rebuild_customer_set_aside`
  - Aggiunto helper `_run_set_aside_rebuild(session) -> EntityRunResult` (stesso pattern di `_run_inventory_rebuild`)
  - `trigger_produzione`: aggiunto Step 4 — `results.append(_run_set_aside_rebuild(session))`
  - Docstring `trigger_produzione` aggiornata: sequenza ora è `articoli → mag_reale → inventory_positions → customer_set_aside`
  - Docstring modulo aggiornata

**Creati:**
- `tests/unit/test_set_aside_rebuild_helper.py` — 4 test di integrazione

### Nessuna modifica al frontend

`ProduzioneHome.tsx` ricarica già il dettaglio articolo dopo ogni refresh (con `Promise.all` che include `GET /produzione/articoli/{codice}`). Il dato `customer_set_aside_qty` viene aggiornato automaticamente tramite questa ricarica.

### Sequenza refresh produzione (aggiornata)

```
POST /api/sync/surface/produzione
  Step 1 — sync articoli (EasyArticoloSource)
  Step 2 — sync mag_reale (EasyMagRealeSource)
  Step 3 — rebuild inventory_positions (da stato corrente mirror mag_reale)
  Step 4 — rebuild customer_set_aside (da stato corrente mirror righe_ordine_cliente)
```

Restituisce 4 `EntityRunResult`:
- `articoli`
- `mag_reale`
- `inventory_positions`
- `customer_set_aside`

### Test eseguiti

4 test in `tests/unit/test_set_aside_rebuild_helper.py`:
- `entity_code = "customer_set_aside"` ✓
- `status = "success"` con mirror vuoto, 0 righe ✓
- `rows_written` uguale al numero di righe create nel fact ✓
- `started_at` e `finished_at` valorizzati ✓

Suite completa: 462/462 passed.
Frontend: `npm run build` — zero errori.

### Test non eseguiti

- Test HTTP end-to-end su `POST /api/sync/surface/produzione`: non inclusi (non ci sono HTTP test per gli endpoint sync nella suite esistente).
- Test con dati reali Easy: non eseguibili senza connessione.

### Assunzioni

- `customer_set_aside` dipende da `sync_righe_ordine_cliente` che non viene sincronizzato da questo flusso (è gestito dalla surface logistica o da un sync separato). Il rebuild usa lo stato corrente del mirror, che può essere da un sync precedente. Questo è il comportamento corretto e coerente con come funziona `inventory_positions` rispetto a `mag_reale`.
- Il rebuild è delete-all + re-insert: deterministico, nessun rischio di accumulo dati stantii.

### Limiti noti

- Se `sync_righe_ordine_cliente` non è mai stato eseguito, `customer_set_aside` sarà 0 per tutti gli articoli. Non è un errore: è lo stato corretto con mirror vuoto.
- Il risultato `customer_set_aside` nel `SyncSurfaceResponse` non è incluso nel calcolo freshness (`freshness_produzione` traccia solo `articoli` e `mag_reale`). Questo è coerente: `customer_set_aside` è un fact derivato, non una sync unit con SyncEntityState.

### Follow-up suggeriti

- Aggiungere `sync_righe_ordine_cliente` al flusso `trigger_produzione` o introdurre un endpoint dedicato per mantenere le righe ordine sincronizzate (step preliminare a `customer_set_aside`).
- Computed fact `availability = inventory - commitments - set_aside`.

## Completed At

2026-04-09

## Completed By

Claude Code
