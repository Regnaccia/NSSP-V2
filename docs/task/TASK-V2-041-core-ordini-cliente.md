# TASK-V2-041 - Core ordini cliente

## Status
Completed

## Date
2026-04-08

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`

## Goal

Costruire il primo Core `ordini cliente` a partire dal mirror `sync_righe_ordine_cliente`, esponendo
`customer_order_lines` come entita canonica riusabile per stream futuri.

## Prerequisite

Prima di eseguire questo task deve risultare completato:

- `TASK-V2-040`

## Context

Con `DL-ARCH-V2-018` la V2 introduce `ordine` come entita canonica cross-modulo.

La sorgente reale Easy e `V_TORDCLI`, gia granularizzata per riga ordine. Il primo slice Core deve quindi:

- partire da `customer_order_line`
- mantenere distinti:
  - `ordered_qty`
  - `fulfilled_qty`
  - `set_aside_qty`
  - `open_qty`
- gestire le righe descrittive con `COLL_RIGA_PREC = true`

La formula V1 di `open_qty` e:

- `open_qty = max(DOC_QTOR - DOC_QTAP - DOC_QTEV, 0)`

perche la quantita gia inscatolata/appartata per il cliente non richiede piu nuovo impegno operativo.

## Scope

### In Scope

- modello Core `customer_order_lines` o equivalente
- identity Core derivata da `(DOC_NUM, NUM_PROGR)`
- campi canonici minimi:
  - `order_reference`
  - `line_reference`
  - `customer_code`
  - `destination_code`
  - `customer_destination_progressive`
  - `customer_order_reference`
  - `article_code`
  - `ordered_qty`
  - `fulfilled_qty`
  - `set_aside_qty`
  - `open_qty`
  - `order_date`
  - `expected_delivery_date`
  - `article_measure`
  - `net_unit_price`
- aggregazione delle righe `COLL_RIGA_PREC = true` in una struttura tipo:
  - `description_lines`
- regola `NUM_PROGR_CLIENTE` vuoto => destinazione principale
- read model/query per arricchire al bisogno i dati cliente/destinazione leggendo dai Core gia esistenti

### Out of Scope

- computed fact `commitments` cliente
- disponibilita
- UI ordini
- persistenza duplicata di dati descrittivi cliente/destinazione dentro il Core ordini
- workflow commerciale avanzato

## Constraints

- il Core deve leggere dal mirror `sync_righe_ordine_cliente`, non da Easy
- i dati cliente/destinazione devono restare riferimenti canonici, non copie persistite premature
- l'arricchimento cliente/destinazione va fatto in query/read model, non come duplicazione stabile nel modello
- le righe con `COLL_RIGA_PREC = true` non devono generare nuova quantita autonoma
- `open_qty` deve usare la formula:
  - `max(DOC_QTOR - DOC_QTAP - DOC_QTEV, 0)`

## Acceptance Criteria

- esiste un Core `customer_order_lines` o equivalente, coerente con `DL-ARCH-V2-018`
- `open_qty` e calcolata correttamente come `max(ordered_qty - set_aside_qty - fulfilled_qty, 0)`
- `description_lines` preserva la struttura descrittiva multi-riga derivata da `COLL_RIGA_PREC`
- il Core non duplica in persistenza i dati descrittivi cliente/destinazione gia disponibili altrove
- esiste almeno un read model/query riusabile per consumatori futuri
- `python -m pytest tests -q` passa

## Deliverables

- modelli Core ordini cliente
- eventuale migration necessaria
- query/read models canonici
- test backend minimi su:
  - `open_qty`
  - `description_lines`
  - righe `COLL_RIGA_PREC`
  - enrichment cliente/destinazione a livello query

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita del read model Core ordini.

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- read models/queries introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- trattare `customer_order_line` come entita canonica primaria del primo slice
- esporre `customer_order` aggregata solo se realmente necessaria
- mantenere `ordered_qty`, `fulfilled_qty`, `set_aside_qty` e `open_qty` come campi distinti
- rinviare il calcolo di `commitments` a un task successivo basato su questa entita canonica

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/core/ordini_cliente/__init__.py` — package; esporta `list_customer_order_lines`, `get_order_lines_by_order`, `get_order_line`, `CustomerOrderLineItem`
- `src/nssp_v2/core/ordini_cliente/read_models.py` — `CustomerOrderLineItem` (frozen Pydantic, 17 campi)
- `src/nssp_v2/core/ordini_cliente/queries.py` — `list_customer_order_lines`, `get_order_lines_by_order`, `get_order_line`, `_build_items`, `_compute_open_qty`, `_to_item`
- `tests/core/test_core_ordini_cliente.py` — 23 test di integrazione

### Migration introdotte

Nessuna. Il Core legge direttamente da `sync_righe_ordine_cliente`: nessuna nuova tabella, nessuna migration necessaria.

### Read models/queries introdotti

- `list_customer_order_lines(session) -> list[CustomerOrderLineItem]` — tutte le righe ordine canoniche, ordinate per `(order_reference, line_reference)`; le continuation rows sono aggregate in `description_lines`
- `get_order_lines_by_order(session, order_reference) -> list[CustomerOrderLineItem]` — righe di un singolo ordine
- `get_order_line(session, order_reference, line_reference) -> CustomerOrderLineItem | None` — singola riga; restituisce None se la riga e una continuation (non e un'entita autonoma)

### Formula open_qty

```
open_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```
- valori None trattati come 0
- risultato sempre >= 0

### Algoritmo description_lines

Le righe `continues_previous_line=True` vengono accumulate in `description_lines` della riga principale immediatamente precedente **solo se appartengono allo stesso ordine** (stessa `order_reference`). Continuation rows di ordini diversi vengono scartate silenziosamente. Le righe di continuazione non generano `CustomerOrderLineItem` autonomi.

### Test eseguiti

23 test in `tests/core/test_core_ordini_cliente.py`:
- open_qty formula base ✓
- None trattati come 0 ✓
- open_qty mai negativo ✓
- set_aside_qty riduce disponibile ✓
- tutto evaso → 0 ✓
- ordered_qty None → 0 ✓
- riga senza continuation ha description_lines=[] ✓
- continuation aggregata in description_lines ✓
- piu continuation accumulate in ordine ✓
- continuation non compaiono come item autonomi ✓
- continuation con segment None non aggiunta ✓
- description_lines non attraversano ordini diversi ✓
- is_main_destination con progressivo None → True ✓
- is_main_destination con progressivo valorizzato → False ✓
- mirror vuoto → lista vuota ✓
- get_order_lines_by_order filtro, ordine inesistente, description_lines ✓
- get_order_line trovata, non trovata, continuation=None, description_lines ✓
- list ordinato per (order_reference, line_reference) ✓

Suite completa: 400/400 passed.

### Test non eseguiti

- Test HTTP su eventuali endpoint API ordini: non inclusi — il task non introduce API.
- Enrichment cliente/destinazione da Core: rinviato a follow-up (out of scope V1).

### Assunzioni

- Il Core legge direttamente da `sync_righe_ordine_cliente` senza tabella materializzata: il dataset e piccolo e la query e semplice.
- Le righe `continues_previous_line=True` appartengono sempre all'ordine della riga principale precedente nella stessa finestra di ordinamento; il codice difensivamente controlla `order_reference` per evitare bleeding tra ordini.
- Una riga con `continues_previous_line=True` senza riga principale precedente nello stesso ordine viene scartata silenziosamente (anomalia di dati sorgente).
- `open_qty = max(ordered - set_aside - fulfilled, 0)`: la quantita gia inscatolata (`set_aside_qty`) riduce la domanda aperta al pari della quantita evasa.

### Limiti noti

- Nessun endpoint API esposto: le query sono consumabili da moduli futuri via import Python (contratto Core).
- Enrichment cliente/destinazione (ragione sociale, indirizzo) non incluso: i read model espongono solo i codici canonici.
- La formula `open_qty` e V1 e potrebbe essere raffinata con nuove provenienze dati.

### Follow-up suggeriti

- Endpoint `GET /api/ordini/righe` e `GET /api/ordini/{order_reference}` per surface UI ordini.
- Computed fact `commitments` da righe con `open_qty > 0` (TASK futuro, DL-ARCH-V2-017).
- Enrichment query con ragione sociale cliente e nome destinazione da `sync_clienti`/`sync_destinazioni`.
- Surface UI ordini cliente (visualizzazione stato ordine, open_qty per riga).
