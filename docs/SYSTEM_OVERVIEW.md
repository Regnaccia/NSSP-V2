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

## Mirror sync attivi

Gia presenti:

- `sync_clienti`
- `sync_destinazioni`
- `sync_articoli`
- `sync_produzioni_attive`
- `sync_produzioni_storiche`

## Dati interni gia introdotti

- `nickname_destinazione`
- `famiglia articolo`
- `considera_in_produzione`

## Pattern consolidati

Pattern gia validati:

- mapping -> sync -> core -> ui -> sync on demand
- mirror esterno + arricchimento interno
- mirror separati + aggregazione nel Core + computed fact con override
- catalogo interno di riferimento + associazione a entita
- pattern UIX generale + spec concreta

## Prossimo passo naturale

Il prossimo step strutturale aperto e:

- `TASK-V2-034` per rendere la vista `produzioni` sostenibile su dataset grandi, con default `active` e storico solo esplicito

## References

- `docs/roadmap/STATUS.md`
- `docs/guides/IMPLEMENTATION_PATTERNS.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
