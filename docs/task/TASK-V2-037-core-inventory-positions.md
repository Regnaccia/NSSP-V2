# TASK-V2-037 - Core inventory positions

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il primo computed fact canonico di giacenza articoli:

- `inventory_positions`

a partire dai movimenti sincronizzati in `sync_mag_reale`.

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/integrations/easy/EASY_MAG_REALE.md`
- `docs/task/TASK-V2-036-sync-mag-reale.md`

## Goal

Costruire una posizione di inventario riusabile cross-modulo, calcolata deterministicamente dai movimenti di magazzino e indipendente da logiche locali di `produzione`.

## Prerequisite

Prima di eseguire questo task deve risultare completato:

- `TASK-V2-036`

## Context

`DL-ARCH-V2-016` introduce `inventory` / `on hand stock` come computed fact canonico:

`on_hand_qty = sum(load_qty) - sum(unload_qty)`

Il primo slice deve esporre la giacenza netta per articolo, senza disponibilita avanzate, allocazioni o logiche multi-magazzino.

## In Scope

- computed fact `inventory_positions`
- aggregazione per `article_code`
- almeno i seguenti campi:
  - `article_code`
  - `total_load_qty`
  - `total_unload_qty`
  - `on_hand_qty`
  - `computed_at`
  - `source_last_movement_date`
- eventuale `movement_count` come campo debug utile
- rebuild completo deterministico della giacenza a partire dal mirror sync
- query/read model Core consumabile da futuri moduli

## Out of Scope

- multi-magazzino
- disponibilita promettibile
- allocazioni
- prenotazioni
- stock bloccato
- UI magazzino
- scheduler automatico del rebuild

## Constraints

- il `core` deve consumare i movimenti sync, non Easy direttamente
- la formula canonica deve restare:
  - `sum(load_qty) - sum(unload_qty)`
- il risultato e per `article_code`
- il task non deve introdurre logiche di modulo locali

## Acceptance Criteria

- esiste una computed fact `inventory_positions`
- il calcolo di `on_hand_qty` e coerente con la formula canonica
- l'aggregazione avviene per `article_code`
- il rebuild completo dal mirror e deterministico
- il contratto Core e riusabile da moduli futuri
- `python -m pytest tests -q` passa

## Deliverables

- modelli/query/read model `inventory_positions`
- migration necessaria, se prevista dal modello scelto
- command o job interno di rebuild della giacenza
- test backend minimi su:
  - formula di calcolo
  - aggregazione per articolo
  - determinismo del rebuild

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica coerente del rebuild `inventory_positions`.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- query/read model introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/core/inventory_positions/__init__.py` — package, esporta `rebuild_inventory_positions`, `list_inventory_positions`, `get_inventory_position`, `InventoryPositionItem`
- `src/nssp_v2/core/inventory_positions/models.py` — `CoreInventoryPosition` (tabella `core_inventory_positions`, UNIQUE `article_code`, 7 campi: article_code, total_load_qty, total_unload_qty, on_hand_qty, movement_count, computed_at, source_last_movement_date)
- `src/nssp_v2/core/inventory_positions/read_models.py` — `InventoryPositionItem` (frozen Pydantic)
- `src/nssp_v2/core/inventory_positions/queries.py` — `rebuild_inventory_positions` (delete-all + GROUP BY + insert), `list_inventory_positions`, `get_inventory_position`, `_to_item`
- `alembic/versions/20260408_013_core_inventory_positions.py` — migration
- `tests/core/test_core_inventory_positions.py` — 15 test di integrazione

**Creati (post-task):**
- `scripts/rebuild_inventory_positions.py` — script CLI standalone; esegue `rebuild_inventory_positions` + commit e stampa il numero di posizioni create; nessun argomento richiesto

### Migration introdotte

- `20260408_013_core_inventory_positions.py` — crea `core_inventory_positions` (down_revision: 20260408012)

### Script/command introdotti

- `scripts/rebuild_inventory_positions.py` — script CLI standalone:
  ```bash
  cd backend
  python scripts/rebuild_inventory_positions.py
  ```
  Prerequisito: `sync_mag_reale` deve essere già stata eseguita almeno una volta.

### Query/read model introdotti

- `rebuild_inventory_positions(session) -> int` — rebuild completo: DELETE + GROUP BY `codice_articolo` su `sync_mag_reale` + INSERT; restituisce n. righe create; il chiamante gestisce commit
- `list_inventory_positions(session) -> list[InventoryPositionItem]` — tutte le posizioni ordinate per `article_code`
- `get_inventory_position(session, article_code) -> InventoryPositionItem | None` — posizione per singolo articolo
- Formula: `on_hand_qty = sum(coalesce(quantita_caricata, 0)) - sum(coalesce(quantita_scaricata, 0))` per `codice_articolo`

### Test eseguiti

15 test in `tests/core/test_core_inventory_positions.py`:
- Formula: solo carico, solo scarico, carico+scarico combinati ✓
- NULL trattati come 0 ✓
- Aggregazione: articoli separati, lista ordinata, articoli senza codice esclusi ✓
- movement_count corretto ✓
- source_last_movement_date = max(data_movimento), None se tutte null ✓
- Rebuild deterministico: stesso input stesso output ✓
- Rebuild ricalcola dopo nuovi movimenti ✓
- Rebuild rimuove posizioni di articoli scomparsi dal mirror ✓
- Mirror vuoto → 0 posizioni ✓
- get_inventory_position su articolo inesistente → None ✓

Suite completa: 361/361 passed.

### Test non eseguiti

- Test HTTP su eventuali endpoint API magazzino: non inclusi — il task non introduce API (UI fuori scope).
- Test di performance su grandi dataset: fuori scope.

### Assunzioni

- Il rebuild è delete-all + re-insert (non upsert) per garantire determinismo: lo stesso input produce esattamente lo stesso output, senza dipendenze da stato precedente.
- `coalesce(qty, 0)` per entrambe le colonne: un movimento con entrambe NULL contribuisce 0 al totale di carico e 0 allo scarico (neutro).
- I movimenti con `codice_articolo = NULL` vengono ignorati: non possono contribuire a una posizione identificabile.
- Il chiamante (`rebuild_inventory_positions`) non chiama `commit()`: la gestione della transazione resta al chiamante (endpoint, script o test).
- Nessuna FK verso `sync_mag_reale`: indipendenza di layer come da architettura V2.

### Limiti noti

- Il rebuild completo ha costo O(n) sui movimenti totali: per dataset molto grandi può essere lento; il rebuild incrementale è un follow-up naturale.
- La giacenza può risultare negativa se gli scarichi superano i carichi — è un dato corretto dalla formula, non un errore.
- Nessun endpoint API esposto in questo task: la computed fact è consumabile da moduli futuri.
- Nessun scheduler automatico del rebuild: deve essere triggerable manualmente o da endpoint futuro.

### Follow-up suggeriti

- Endpoint `POST /api/magazzino/inventory/rebuild` per trigger manuale del rebuild.
- Surface UI magazzino con lista posizioni inventariali.
- Integrazione della giacenza nel lancio produzione (disponibilità materiale).
- Rebuild incrementale su delta movimenti (senza delete-all) per dataset grandi.
- Scheduler periodico del rebuild (es. una volta al giorno).
