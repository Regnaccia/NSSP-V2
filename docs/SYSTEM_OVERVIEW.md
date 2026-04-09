# ODE V2 - System Overview

## Date
2026-04-09

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
- computed fact `customer_set_aside` esposto nel pannello dettaglio
- refresh sequenziale backend-controlled `articoli -> mag_reale -> righe_ordine_cliente -> inventory_positions -> customer_set_aside`

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

Correzione ancora aperta:

- il mirror ordini cliente deve essere riallineato come specchio delle sole righe ancora presenti in `V_TORDCLI`

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
- separato da `commitments` (open_qty) e da `inventory` (stock fisico)
- esposto nel dettaglio UI `articoli` come campo read-only ODE
- ricalcolato nel refresh sequenziale dopo `sync_righe_ordine_cliente`

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
- `commitments`
- `customer_set_aside`

## Pattern consolidati

Pattern gia validati:

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- mirror separati + aggregazione nel Core + computed fact con override
- catalogo interno di riferimento + associazione a entita
- pattern UIX generale + spec concreta

## Prossimo passo naturale

I building block canonici ora disponibili:

- `inventory` - stock fisico netto
- `commitments` - domanda operativa aperta (`customer_order` + `production`)
- `customer_set_aside` - quota gia fisicamente appartata (`DOC_QTAP`)

Prima del passo `availability` e aperto un riallineamento necessario:

- `TASK-V2-048` per rendere `sync_righe_ordine_cliente` un mirror operativo delle sole righe ancora presenti in `V_TORDCLI`

Dopo questo riallineamento, il passo naturale successivo torna a essere `availability` come derivato di questi tre fact (DL-ARCH-V2-019, sezione 8).

## References

- `docs/roadmap/STATUS.md`
- `docs/guides/IMPLEMENTATION_PATTERNS.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-020.md`
