# ODE V2 - System Overview

## Date
2026-04-14

## Scopo

Questo documento riassume lo stato reale della V2 senza dover partire subito dal codice.

Nota di baseline:

- la V2 resta il progetto attivo
- il progetto e ora sotto `architectural rebase` in-place
- la guida architetturale autoritativa per i prossimi slice e:
  - `DL-ARCH-V2-039`
  - `DL-ARCH-V2-040`

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
- pagina admin per warning visibility
- pagina admin dedicata alle logiche stock
- pagina admin dedicata alle logiche proposal

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
  - `gestione_scorte_attiva`
- override articolo tri-state per le stesse policy
- planning policy effettive esposte dal Core `articoli`:
  - `effective_considera_in_produzione`
  - `effective_aggrega_codice_in_produzione`
  - `effective_gestione_scorte_attiva`
  - `planning_mode`
- metriche quantitative read-only nel dettaglio:
  - `giacenza`
  - `customer_set_aside`
  - `committed_qty`
  - `availability_qty`
- metriche stock policy nel dettaglio:
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`
  - `stock_strategy_key`
  - `stock_computed_at`
- override stock articolo:
  - `override_gestione_scorte_attiva`
  - `override_stock_months`
  - `override_stock_trigger_months`
  - `capacity_override_qty`
- configurazione proposal articolo:
  - `proposal_logic_key`
  - `proposal_logic_article_params`
- valore effettivo proposal esposto:
  - `effective_proposal_logic_key`
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
- stock-driven by-article gia integrato con:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `required_qty_total`
  - `primary_driver`
- la componente stock-driven si applica solo con:
  - `planning_mode = by_article`
  - `effective_gestione_scorte_attiva = true`
- primi horizon planning gia attivi:
  - `customer horizon`
  - `stock horizon`
- `customer horizon` e `stock horizon` sono ora separati correttamente
- `required_qty_minimum` nel ramo `by_article` segue il driver primario anche nei casi `stock-only`
- la tabella planning espone la data richiesta con semantica distinta:
  - `requested_delivery_date` nel ramo per-riga
  - `earliest_customer_delivery_date` nel ramo aggregato solo se esiste componente customer
- il contratto descrittivo planning e ora unificato:
  - `description_parts`
  - `display_description`
- la leggibilita UI planning e stata rifinita con:
  - colonna `misura`
  - badge famiglia
  - badge motivi sintetici
  - destinazione richiesta leggibile
  - colonna `Warnings`
  - quick config modal articolo
- la vista planning consuma anche warning articolo attivi filtrati per area
- quick edit planning -> articoli usa bridge case-insensitive tra codice canonical e codice raw
- surface UI dedicata con:
  - ricerca `codice`
  - ricerca `descrizione`
  - filtro famiglia
  - toggle `solo_in_produzione`
  - `Aggiorna`
  - filtri per driver:
    - `Tutti`
    - `Solo fabbisogno cliente`
    - `Solo scorta`
  - filtro `customer horizon`

Non ancora disponibile:

- scoring
- policy di aggregazione avanzata

Rebase target:

- distinguere esplicitamente:
  - `required_qty_eventual`
  - `release_qty_now_max`
  - `release_status`
- non usare piu una sola quantita implicita per need e rilascio

### Warnings

Disponibile:

- modulo trasversale `warnings`
- warning canonici iniziali:
  - `NEGATIVE_STOCK`
  - `INVALID_STOCK_CAPACITY`
- surface dedicata `Warnings`
- configurazione admin iniziale della visibilita

Stato attuale:

- il warning e unico e non duplicato per reparto
- la configurazione attuale usa gia `visible_to_areas`
- gli utenti operativi vedono nella surface `Warnings` solo i warning inclusi nella propria area
- `admin` mantiene vista trasversale completa

### Production Proposals

Disponibile:

- nuovo dominio Core/API `production_proposals`
- surface dedicata `Production Proposals`
- granularita che segue il candidate:
  - `by_article`
  - `by_customer_order_line`
- workspace temporaneo generato da selezione in `Planning Candidates`
- storico persistente degli export con workflow:
  - `exported`
  - `reconciled`
  - `cancelled`
- logica proposal V1 minima:
  - `proposal_target_pieces_v1`
- configurazione globale logiche proposal in `admin`
- assegnazione e parametri proposal specifici per articolo
- export `xlsx` del workspace
- riconciliazione via `ODE_REF` sui mirror produzioni

Rebase target:

- `proposal_logic_key` resta surface di compatibilita
- il modello concettuale futuro va letto come bundle di policy:
  - `proposal_base_qty_policy`
  - `proposal_lot_policy`
  - `proposal_capacity_policy`
  - `proposal_customer_guardrail_policy`
  - `proposal_note_policy`

### Criticita Articoli

Disponibile:

- vista operativa minima basata su `availability_qty < 0`
- filtro famiglia
- ordinamenti quantitativi
- toggle `solo_in_produzione`
- refresh agganciato a `refresh_articoli()`

Nota:

- resta disponibile ma non e piu lo stream operativo primario
- la deprecazione formale e stata gia completata con `TASK-V2-080`

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
- `production_proposals`

## Pattern consolidati

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- refresh semantici backend con dipendenze interne
- logiche di dominio sopra fact canonici
- planning policy con default famiglia + override articolo
- distinzione tra chiave articolo raw e chiave canonica
- `Planning Candidates` come modulo planning customer-driven
- `Warnings` come modulo trasversale separato dal planning
- stock policy V1 come estensione del ramo `by_article`, con riuso di `future_availability_qty` e flag esplicito `gestione_scorte_attiva`
- configurazione logiche stock V1 con `strategy_key` selezionabile per `monthly_stock_base_qty` e `capacity_from_containers_v1` fissa
- algoritmo stock V1 riallineato con finestre multiple, percentile, filtro outlier e parametri configurabili
- modello descrittivo planning unificato con `description_parts` + `display_description`
- integrazione contestuale `Warnings -> Planning Candidates` senza duplicare logica warning
- bridge case-insensitive planning -> articoli per lookup e write config
- proposal logic config con suite globale `admin` + override articolo
- `Production Proposals` come workspace temporaneo downstream di `Planning Candidates`, con persistenza solo all'export

## Stato attuale

Il perimetro quantitativo e planning V1/V2 di base e operativo:

- `inventory`, `commitments`, `customer_set_aside`, `availability`
- `Planning Candidates` V2 con branching reale
- primo slice `Warnings` V1
- primo slice `stock_policy` Core con metriche dedicate
- consumo UI delle metriche stock nella surface `articoli`
- stock-driven planning gia integrato nel ramo `by_article`
- governance stock separata in `admin`
- primi horizon planning gia introdotti
- primo slice `Production Proposals` V1 con workspace temporaneo, export batch e reconcile

Task aperti correnti:

- `TASK-V2-115` contratti Core/API per preview export EasyJob in `Production Proposals`
- `TASK-V2-116` tabella UI `Production Proposals` allineata alla preview export EasyJob

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
- `docs/decisions/ARCH/DL-ARCH-V2-031.md`
- `docs/decisions/ARCH/DL-ARCH-V2-032.md`
- `docs/decisions/ARCH/DL-ARCH-V2-033.md`
