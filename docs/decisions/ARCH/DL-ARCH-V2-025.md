# DL-ARCH-V2-025 - Planning Candidates V1 aggregati per articolo

## Status
Accepted

## Date
2026-04-10

## Context

La V2 dispone gia di:

- `customer_order_lines`
- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`
- `produzioni attive`
- refresh semantici backend
- una prima vista operativa `criticita articoli`

La vista `criticita articoli` risponde a una domanda immediata:

> l'articolo e scoperto adesso?

Ma non risponde ancora alla domanda di planning:

> dobbiamo ancora attivare nuova produzione per questo articolo, anche considerando la supply gia in corso?

La spec ampia di `Planning Candidates` contiene anche:

- stock-driven candidates
- planning horizon
- incoming within horizon
- scoring
- politiche di aggregazione
- casi non aggregabili

Questi concetti sono utili, ma non sono ancora abbastanza stabili per la prima implementazione.

Serve quindi una V1 ridotta, implementabile e coerente con il modello canonico attuale.

## Decision

La V1 di `Planning Candidates` e definita come:

- modulo `customer-driven`
- aggregato per `article`
- basato su `availability` attuale e `incoming supply` da produzioni attive
- senza stock policy
- senza orizzonte temporale
- senza scoring
- senza varianti `aggregable / non_aggregable`

## Core Concepts

### 1. availability_qty

`availability_qty` mantiene il significato gia fissato in `DL-ARCH-V2-021`:

- quantita libera attuale
- dopo sottrazione di `customer_set_aside` e `commitments`

Non viene introdotto un nuovo nome alternativo come `available_now_qty`.

### 2. incoming_supply_qty

`incoming_supply_qty` rappresenta la supply gia in corso derivata dalle `produzioni attive`.

Per V1:

- non introduce ETA
- non introduce horizon
- non valuta attendibilita o ritardi
- tratta la produzione attiva come supply in arrivo

### 3. future_availability_qty

La V1 introduce il concetto:

```text
future_availability_qty = availability_qty + incoming_supply_qty
```

Significato:

- copertura futura semplice, ottenuta sommando la disponibilita libera attuale con la supply gia in corso

Questo e il principale riferimento quantitativo della V1 di `Planning Candidates`.

### 4. customer_open_demand_qty

La V1 usa una domanda cliente aperta aggregata per articolo.

Questa domanda rappresenta il lato customer-driven del modulo.

Non vengono ancora introdotti:

- candidate stock-driven
- target di scorta
- safety stock

## Candidate Identity

Per V1 la `planning identity` e:

```text
article_code
```

Esiste al massimo un candidate attivo per articolo.

La V1 non genera candidate per singola riga ordine.

## Generation Rule

La V1 genera candidate a livello aggregato per articolo.

Regola primaria:

```text
future_availability_qty < 0
```

Se questa condizione e vera:

- l'articolo resta scoperto anche dopo la supply gia in corso
- il sistema deve considerarlo un planning candidate

Se la condizione non e vera:

- il candidate non esiste

## Candidate Status Model

La V1 non usa stati multipli come:

- `monitor`
- `immediate`

Motivo:

- una volta incorporata `incoming_supply_qty` dentro `future_availability_qty`, il caso "scoperto ora ma coperto da supply attiva" non deve produrre un candidate

Il modello V1 e quindi binario:

- candidate presente
- candidate assente

## Required Quantity

La V1 puo esporre una quantita minima di scopertura:

```text
required_qty_minimum = abs(future_availability_qty)
```

solo quando `future_availability_qty < 0`, altrimenti `0`.

Questa quantita:

- non e ancora quantita produttiva finale
- non include lotti, multipli, arrotondamenti o policy operative

## Relationship With Existing Logic

`Planning Candidates V1` non sostituisce `criticita articoli`.

Le due viste hanno significati diversi:

- `criticita articoli`
  - segnala scopertura attuale
  - regola V1: `availability_qty < 0`
- `planning candidates`
  - segnala necessita di nuova attenzione produttiva
  - regola V1: `future_availability_qty < 0`

Questo permette di mantenere:

- una vista immediata di criticita
- una vista piu vicina al planning

senza forzare entrambe dentro una sola logica.

## Architectural Positioning

`Planning Candidates V1` e:

- una projection/read model del Core
- costruita su fact canonici esistenti
- governata da una logica di dominio separata, coerente con `DL-ARCH-V2-023`

Non e:

- un nuovo fact canonico di base come `inventory` o `availability`
- uno scheduler
- un motore MRP completo

## Deferred Concepts

Restano esplicitamente fuori dalla V1:

- stock-driven candidates
- planning horizon
- `incoming_within_horizon_qty`
- due-date urgency
- scoring e ranking
- `aggregable / non_aggregable`
- candidate per riga ordine
- policy per famiglia o articolo

Questi concetti verranno affrontati come espansioni future del modulo, non come prerequisiti della V1.

## Consequences

### Positive

- V1 molto piu semplice da spiegare e validare
- forte riuso dei fact canonici gia esistenti
- nessun blocco immediato sul tema ancora aperto `aggregable / non_aggregable`
- prima vista planning operativa senza congelare troppo presto logiche piu sofisticate

### Negative

- perdita della granularita per riga ordine
- assenza di logica temporale vera
- nessuna priorita nativa tra candidate
- nessuna distinzione ancora tra shortage cliente e future policy stock-driven

## References

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/PLANNING_CANDIDATES_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/ARCH/DL-ARCH-V2-024.md`
