# ODE V2 - System Overview

## Date
2026-04-13

## Scopo

Questo documento riassume lo stato reale della V2 senza dover partire subito dal codice.

## Architettura attiva

La V2 adotta quattro layer espliciti:

- `sync`
- `core`
- `app`
- `shared`

Regole stabili:

- Easy e `read-only`
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
- prima pagina admin per la configurazione warning visibility

Nota:

- la configurazione warning usa `visible_to_areas`
- `admin` governa la configurazione e ha vista trasversale

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
- override articolo tri-state per le stesse policy
- planning policy effettive esposte dal Core `articoli`:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
  - `planning_mode`
- metriche quantitative read-only nel dettaglio:
  - `giacenza`
  - `customer_set_aside`
  - `committed_qty`
  - `availability_qty`
- refresh semantico backend-controlled `refresh_articoli()` con chain interna completa

### Produzioni

Disponibile:

- mirror sync separati per attive e storiche
- Core aggregato con `bucket`
- computed fact `stato_produzione`
- override interno `forza_completata`
- UI consultiva a 2 colonne
- sync on demand backend-controlled
- default lista su `active`
- storico disponibile solo in modo esplicito
- filtro `stato_produzione`
- ricerca per articolo/documento

### Inventory

Disponibile:

- mirror `sync_mag_reale`
- computed fact `inventory_positions`
- formula canonica `on_hand_qty = sum(load) - sum(unload)`
- integrazione della giacenza nella surface `articoli`
- re-bootstrap completo del mirror gia eseguito con `TASK-V2-073`

Nota:

- il problema strutturale `append_only + no_delete_handling` resta aperto in [KNOWN_BUGS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/KNOWN_BUGS.md#L1)

### Ordini cliente

Disponibile:

- mirror `sync_righe_ordine_cliente` da `V_TORDCLI`
- Core `customer_order_lines`
- `open_qty = max(DOC_QTOR - DOC_QTAP - DOC_QTEV, 0)`
- supporto a `description_lines`
- enrichment cliente/destinazione demand-driven a livello query/read model

### Commitments

Disponibile:

- computed fact `commitments` da provenienza `customer_order`
- estensione `commitments` alla provenienza `production`
- `commitments` mantenuto separato da `inventory`

### Customer Set Aside

Disponibile:

- computed fact `customer_set_aside` da `DOC_QTAP`
- esposto nel dettaglio UI `articoli`

### Availability

Disponibile:

- computed fact `availability`
- formula canonica:
  - `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`
- valori negativi ammessi
- rebuild deterministic

### Planning Candidates

Disponibile:

- modulo customer-driven con due modalita:
  - `by_article`
  - `by_customer_order_line`
- nel ramo `by_article`:
  - `incoming_supply_qty`
  - `future_availability_qty = availability_qty + incoming_supply_qty`
- nel ramo `by_customer_order_line`:
  - `line_open_demand_qty`
  - `linked_incoming_supply_qty`
  - `line_future_coverage_qty`
- le produzioni completate sono escluse, anche via `forza_completata`
- `required_qty_minimum` come scopertura minima residua
- refinement finale gia applicato:
  - `stock_effective = max(stock_calculated, 0)`
  - `reason_code` / `reason_text`
  - `misura`
  - descrizione ordine primaria nel ramo per-riga
- surface UI dedicata con:
  - ricerca `codice`
  - ricerca `descrizione`
  - filtro famiglia
  - toggle `solo_in_produzione`
  - `Aggiorna`

Non ancora disponibile:

- scoring
- planning horizon
- policy di aggregazione avanzata

### Warnings

Disponibile:

- modulo trasversale `warnings`
- primo warning canonico `NEGATIVE_STOCK`
- surface dedicata `Warnings`
- configurazione admin iniziale della visibilita

Stato attuale:

- il warning e unico e non duplicato per reparto
- la configurazione attuale usa gia `visible_to_areas`
- gli utenti operativi vedono nella surface `Warnings` solo i warning inclusi nella propria area
- `admin` mantiene vista trasversale completa

### Criticita Articoli

Disponibile:

- vista operativa minima basata su `availability_qty < 0`
- filtro famiglia
- ordinamenti quantitativi
- toggle `solo_in_produzione`
- refresh agganciato a `refresh_articoli()`

Nota:

- resta disponibile ma non e piu lo stream operativo primario
- la deprecazione formale e aperta in `TASK-V2-080`

## Mirror sync attivi

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
- `warnings`

## Pattern consolidati

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- refresh semantici backend con dipendenze interne
- logiche di dominio sopra fact canonici
- planning policy con default famiglia + override articolo
- distinzione tra chiave articolo raw e chiave canonica
- `Planning Candidates` come modulo planning customer-driven
- `Warnings` come modulo trasversale separato dal planning
- stock policy V1 come estensione del ramo `by_article`, senza flag separato e con riuso di `future_availability_qty`

## Stato attuale

Il perimetro quantitativo e planning V1/V2 di base e operativo:

- `inventory`, `commitments`, `customer_set_aside`, `availability`
- `Planning Candidates` V2 con branching reale
- primo slice `Warnings` V1

Task aperti correnti:

Nessuno nello snapshot corrente.

Task deferred:

- `TASK-V2-079` badge warning in `articoli` e `Planning Candidates`

## References

- `docs/roadmap/STATUS.md`
- `docs/guides/IMPLEMENTATION_PATTERNS.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-024.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`
