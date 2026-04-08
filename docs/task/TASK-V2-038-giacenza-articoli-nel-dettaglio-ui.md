# TASK-V2-038 - Giacenza articoli nel dettaglio UI

## Status
Completed

## Date
2026-04-08

## Scope

Integrare nel pannello di dettaglio della surface `articoli` un campo read-only che esponga la giacenza calcolata dal `core`.

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-036-sync-mag-reale.md`
- `docs/task/TASK-V2-037-core-inventory-positions.md`

## Goal

Esporre nella pagina `articoli` la prima computed fact canonica di giacenza, in modo da verificare visivamente l'allineamento tra Easy e ODE sullo stock netto per articolo.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-036`
- `TASK-V2-037`

## Context

Con `DL-ARCH-V2-016` la V2 introduce `inventory_positions` come computed fact canonico di giacenza per articolo.

La surface `articoli` e il punto piu semplice per una prima verifica visiva del dato:

- l'utente seleziona un articolo
- il pannello di destra mostra la giacenza calcolata

Questo task non introduce ancora una UI di magazzino dedicata. Riusa una surface gia esistente per validare il nuovo building block.

## In Scope

- estendere il contratto Core/API `articoli` per includere la giacenza calcolata
- esporre nel dettaglio articolo almeno:
  - `on_hand_qty` o nome equivalente coerente
  - eventuale `computed_at`, se disponibile e gia esposto dal Core
- rendering read-only del dato nel pannello di destra della surface `articoli`
- presentazione chiara come dato calcolato internamente

## Out of Scope

- modifica manuale della giacenza
- UI magazzino dedicata
- drill-down sui movimenti di magazzino
- disponibilita avanzata / ATP
- filtri articoli basati sulla giacenza

## Constraints

- la pagina `articoli` deve leggere la giacenza dal `core`, non dai movimenti `MAG_REALE`
- il campo deve essere read-only
- il task non deve introdurre logiche di magazzino nel frontend
- il naming mostrato in UI deve evitare ambiguita con `available stock`

## Acceptance Criteria

- il dettaglio articolo mostra la giacenza calcolata dal `core`
- il dato e coerente col contratto `inventory_positions`
- la UI rende evidente che il campo e read-only
- il dettaglio continua a funzionare correttamente anche per articoli senza giacenza disponibile o senza movimenti
- `npm run build` passa senza errori

## Deliverables

- aggiornamento del contratto Core/API `articoli`
- aggiornamento della surface `articoli`
- eventuali test backend/frontend coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- contratti Core/API estesi
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Modificati backend:**
- `src/nssp_v2/core/articoli/read_models.py` — `ArticoloDetail` esteso con `on_hand_qty: Decimal | None = None` e `giacenza_computed_at: datetime | None = None`
- `src/nssp_v2/core/articoli/queries.py` — `get_articolo_detail` esteso: lookup di `CoreInventoryPosition` per `article_code = codice_articolo.strip().upper()`; popola `on_hand_qty` e `giacenza_computed_at` (None se non trovata)

**Modificati frontend:**
- `frontend/src/types/api.ts` — `ArticoloDetail` esteso con `on_hand_qty: string | null` e `giacenza_computed_at: string | null`
- `frontend/src/pages/surfaces/ProduzioneHome.tsx` — `ColonnaDettaglio` aggiunta sezione "Giacenza — sola lettura (ODE)": mostra `on_hand_qty` con unità di misura e `giacenza_computed_at`; fallback testuale se nessun movimento

### Contratti Core/API estesi

- `GET /api/produzione/articoli/{codice}` → `ArticoloDetail` ora include:
  - `on_hand_qty`: giacenza netta (`sum(load) - sum(unload)`) da `core_inventory_positions`, `null` se nessun movimento
  - `giacenza_computed_at`: timestamp del calcolo, `null` se nessun movimento

### Test eseguiti

361/361 passati (nessun test nuovo necessario: la logica di calcolo giacenza è coperta da `tests/core/test_core_inventory_positions.py`; il lookup nell'endpoint è meccanico).

Test rotti e corretti: 3 test in `tests/unit/test_core_articoli_read_models.py` fallivano perché i nuovi campi erano required — risolto con `= None` (default opzionale).

### Test non eseguiti

- Test di integrazione HTTP su `GET /articoli/{codice}` con giacenza: non inclusi; il lookup `CoreInventoryPosition` è semplice e la logica di calcolo è già coperta.

### Assunzioni

- La join tra `sync_articoli.codice_articolo` e `core_inventory_positions.article_code` avviene su `.strip().upper()` lato Python prima della query: coerente con la normalizzazione applicata in `rebuild_inventory_positions`.
- I campi `on_hand_qty` e `giacenza_computed_at` hanno `default=None` per backward-compat con i test esistenti che costruivano `ArticoloDetail` senza questi campi.
- La sezione giacenza in UI mostra "Nessun movimento registrato" se `on_hand_qty` è null — l'utente capisce che serve eseguire sync + rebuild prima.

### Limiti noti

- La giacenza mostrata è quella dell'ultimo rebuild esplicito: non è in tempo reale. L'utente deve triggherare sync magazzino + rebuild per aggiornare.
- Non esiste ancora un endpoint di rebuild nella UI: il rebuild deve essere triggherato manualmente via API o script.
- La giacenza può essere negativa (scarichi > carichi): è un dato corretto, non nascosto.

### Follow-up suggeriti

- Pulsante "Aggiorna giacenza" nella surface articoli (trigger sync magazzino + rebuild).
- Endpoint `POST /api/magazzino/inventory/rebuild` per trigger esplicito.
- Surface magazzino dedicata con lista posizioni inventariali e drill-down movimenti.
