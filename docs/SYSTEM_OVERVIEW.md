# ODE V2 - System Overview

## Date
2026-04-08

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
- gestione catalogo famiglie
- flag `considera_in_produzione`
- giacenza read-only dal Core nel pannello dettaglio
- refresh sequenziale backend-controlled `articoli -> mag_reale -> inventory_positions`

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
- `inventory_positions`

## Pattern consolidati

Pattern gia validati:

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- mirror separati + aggregazione nel Core + computed fact con override
- catalogo interno di riferimento + associazione a entita
- pattern UIX generale + spec concreta

## Prossimo passo naturale

Task aperti nel flusso documentato:

- `TASK-V2-042` `commitments` cliente
- `TASK-V2-043` `commitments` produzione

I prossimi candidati naturali emersi dalla documentazione sono:

- `commitments` cliente come prima provenienza `customer_order`
- `commitments` produzione per materiali `CAT_ART1 != 0`
- `commitments` come building block separato da `inventory`
- futura `availability` come derivato di `inventory` e `commitments`

## References

- `docs/roadmap/STATUS.md`
- `docs/guides/IMPLEMENTATION_PATTERNS.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
