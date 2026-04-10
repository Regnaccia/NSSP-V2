# ODE V2 - System Overview

## Date
2026-04-10

## Scopo

Questo documento riassume lo stato reale della V2 senza dover partire subito dal codice.

## Architettura attiva

La V2 adotta quattro layer espliciti:

- `sync`
- `core`
- `app`
- `shared`

Regole stabili:

- Easy e sempre `read-only`
- il `sync` costruisce mirror tecnici
- il `core` aggrega, arricchisce e calcola significato applicativo
- la UI consuma solo API/Core, mai mirror sync direttamente

## Stream oggi attivi

### Admin

Disponibile:

- auth browser
- ruoli multipli
- surface `admin`
- gestione utenti e ruoli

### Logistica

Disponibile:

- sync `clienti`
- sync `destinazioni`
- Core `clienti + destinazioni`
- destinazione principale derivata dal cliente
- UI browser a 3 colonne
- sync on demand backend-controlled

### Produzione / Articoli

Disponibile:

- sync `articoli`
- Core `articoli`
- UI browser a 2 colonne
- sync on demand backend-controlled
- catalogo interno `famiglie articolo`
- associazione articolo -> famiglia
- filtro famiglia
- ricerca separata per:
  - `codice` con normalizzazione dimensionale
  - `descrizione` testuale
- gestione catalogo famiglie
- planning policy di default a livello famiglia:
  - `considera_in_produzione`
  - `aggrega_codice_in_produzione`
- planning policy effettive esposte dal Core `articoli`:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
- giacenza read-only dal Core nel pannello dettaglio
- computed fact `customer_set_aside` esposto nel pannello dettaglio
- `committed_qty` e `availability_qty` esposti nel pannello dettaglio
- refresh semantico backend-controlled `refresh_articoli()` con chain interna completa a 8 step

### Produzione / Criticita Articoli

Disponibile:

- vista operativa minima di criticita basata su `availability_qty < 0`
- logica di dominio V1 applicata nel Core backend
- filtro famiglia
- ordinamenti quantitativi
- toggle del perimetro `considera_in_produzione` con default attivo
- refresh della vista agganciato al refresh semantico completo `refresh_articoli()`
- perimetro ristretto ai soli articoli presenti e attivi nella surface `articoli`
- hardening delle join cross-source sulla chiave articolo canonica

### Produzioni

Disponibile:

- mapping Easy da `DPRE_PROD` e `SDPRE_PROD`
- mirror sync separati per attive e storiche
- Core aggregato con `bucket`
- computed fact `stato_produzione`
- override interno `forza_completata`
- UI consultiva a `2 colonne`
- sync on demand backend-controlled
- prima gestione operativa di `forza_completata`
- default lista su `active`
- storico disponibile solo in modo esplicito
- filtro `stato_produzione`
- ricerca per `codice_articolo` e `numero_documento`

### Inventory

Disponibile:

- mirror `sync_mag_reale`
- computed fact `inventory_positions`
- formula canonica `on_hand_qty = sum(load) - sum(unload)`
- integrazione read-only della giacenza nella surface `articoli`

### Ordini cliente

Disponibile:

- mirror `sync_righe_ordine_cliente` da `V_TORDCLI`
- Core `customer_order_lines`
- `open_qty = max(DOC_QTOR - DOC_QTAP - DOC_QTEV, 0)`
- supporto a `description_lines` per righe con `COLL_RIGA_PREC = true`
- enrichment cliente/destinazione demand-driven a livello query/read model

Mirror operativo attivo:

- `delete_absent_keys`: le righe non piu presenti in `V_TORDCLI` vengono rimosse dalla sync successiva
- le righe con `COLL_RIGA_PREC = true` restano finche la sorgente le include

### Commitments

Disponibile:

- computed fact `commitments` da provenienza `customer_order`
- `committed_qty = open_qty` per righe ordine ancora aperte
- estensione `commitments` alla provenienza `production`
- perimetro V1 `production` limitato a materiali con `CAT_ART1 != 0`
- `commitments` mantenuto separato da `inventory`

### Customer Set Aside

Disponibile:

- computed fact `customer_set_aside` da `DOC_QTAP`
- `set_aside_qty = DOC_QTAP` per righe ordine con quota appartata > 0
- separato da `commitments` e da `inventory`
- esposto nel dettaglio UI `articoli` come campo read-only ODE
- ricalcolato nel refresh sequenziale dopo `sync_righe_ordine_cliente`

### Availability

Disponibile:

- computed fact `availability`
- formula canonica V1: `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`
- rebuild deterministic (`delete-all + re-insert`)
- valori negativi ammessi
- un record per `article_code` (UniqueConstraint)
- script on-demand: `scripts/rebuild_availability.py`

Esposto nel dettaglio `articoli` come campo read-only ODE.
Ricalcolato nel refresh semantico `articoli` come step 8, dopo `inventory`, `customer_set_aside` e `commitments`.

### Planning Candidates V1

Disponibile:

- primo slice Core `planning_candidates`
- modulo customer-driven aggregato per articolo
- `incoming_supply_qty` aggregata da produzioni attive
- `future_availability_qty = availability_qty + incoming_supply_qty`
- candidate presente solo se `future_availability_qty < 0`
- `required_qty_minimum` come scopertura minima residua

Non ancora disponibile:

- surface UI dedicata
- scoring
- planning horizon
- policy di aggregazione avanzata

## Mirror sync attivi

Gia presenti:

- `sync_clienti`
- `sync_destinazioni`
- `sync_articoli`
- `sync_produzioni_attive`
- `sync_produzioni_storiche`
- `sync_mag_reale`
- `sync_righe_ordine_cliente`

## Dati interni gia introdotti

- `nickname_destinazione`
- `famiglia articolo`
- `considera_in_produzione`
- `aggrega_codice_in_produzione`
- `inventory_positions`
- `commitments`
- `customer_set_aside`
- `availability`
- `planning_candidates`

## Pattern consolidati

Pattern gia validati:

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- mirror separati + aggregazione nel Core + computed fact con override
- catalogo interno di riferimento + associazione a entita
- pattern UIX generale + spec concreta
- refresh semantici backend con dipendenze interne (DL-ARCH-V2-022)
- logiche di dominio come funzioni intercambiabili su fact canonici (DL-ARCH-V2-023)
- distinzione esplicita tra chiave articolo raw e chiave articolo canonica (DL-ARCH-V2-024)
- primo DL del modulo `Planning Candidates` nella V1 ridotta customer-driven aggregata per articolo (DL-ARCH-V2-025)
- planning policy con default a livello famiglia e override puntuale a livello articolo (DL-ARCH-V2-026)

### Refresh semantici (DL-ARCH-V2-022)

La surface `articoli` espone un refresh semantico nominato.
Il router chiama `refresh_articoli()` e non conosce gli step interni.
La chain (8 step, dipendenze condizionali) vive in `app/services/refresh_articoli.py`.

Chain completa:

```text
POST /api/sync/surface/produzione
  Step 1 - sync articoli
  Step 2 - sync mag_reale
  Step 3 - sync righe_ordine_cliente
  Step 4 - sync produzioni_attive
  Step 5 - rebuild inventory_positions
  Step 6 - rebuild customer_set_aside
  Step 7 - rebuild commitments
  Step 8 - rebuild availability
```

## Stato attuale

Il perimetro V1 del modello quantitativo e completo e operativo:

- `inventory`, `commitments`, `customer_set_aside`, `availability`
- tutti e quattro i fact esposti nel dettaglio `articoli`
- refresh semantico completo: tutti i fact ricalcolati in un solo trigger
- normalizzazione `article_code` canonica cross-source (`normalize_article_code`)
- prima vista operativa `criticita articoli` gia attiva e coerente con la surface `articoli`

Task aperti correnti:

- `TASK-V2-065` UI `Planning Candidates` V1

## References

- `docs/roadmap/STATUS.md`
- `docs/guides/IMPLEMENTATION_PATTERNS.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-020.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-024.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
