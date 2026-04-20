# DL-ARCH-V2-043 - `customer_horizon` rimosso dal Core planning e mantenuto solo come segnale UI/priorita

## Status
Active

## Date
2026-04-17

## Context

`DL-ARCH-V2-042` ha fissato il target di rebase di `Planning Candidates`:

- Core planning semplice
- `priority_score` come layer separato
- tempo e urgenza fuori dalla semantica base del bisogno

Resta pero una scelta da chiudere:

- migrazione graduale, mantenendo `customer_horizon_days` nel calcolo ancora per un periodo
- oppure rimozione diretta dal Core planning

Dato l'obiettivo del rebase, mantenere a lungo entrambe le semantiche produrrebbe:

- doppio modello mentale
- task Core piu ambigui
- UI costretta a spiegare eccezioni generate dal calcolo

## Decision

La V2 adotta la scelta piu netta:

> `customer_horizon_days` viene rimosso dal calcolo Core di `Planning Candidates`

Da questo punto in avanti:

- la componente `customer` e sempre calcolata sulla domanda cliente aperta reale
- la componente `stock` resta basata sulla stock policy
- `customer_horizon_days` non partecipa piu alla definizione di `customer_shortage_qty`

## Contract

### 1. Nuova semantica Core

Nel ramo `by_article`:

- `customer_shortage_qty`
  - si basa sulla domanda cliente aperta reale
- `stock_replenishment_qty`
  - resta basata sulla policy di scorta
- `required_qty_total`
  - resta la somma delle due componenti

Regola:

- il tempo non cambia piu il driver `customer` vs `stock`

### 2. Nuovo ruolo di `customer_horizon_days`

`customer_horizon_days` non sparisce dal prodotto, ma cambia definitivamente ruolo.

Da ora puo essere usato solo per:

- ranking / `priority_score`
- filtri visivi della surface planning
- evidenza ordini vicini vs ordini lontani
- contestualizzazione nel workspace

Non e piu ammesso usarlo per:

- abbassare `customer_shortage_qty`
- trasformare un caso cliente in `stock-only`
- alterare il driver primario del candidate

### 3. Impatto sulla classificazione

La classificazione planning deve tornare lineare:

- `Cliente`
- `Cliente + Magazzino`
- `Magazzino`

Questa classificazione dipende solo dalle componenti quantitative reali:

- `customer_shortage_qty`
- `stock_replenishment_qty`

e non da filtri temporali.

### 4. Impatto sullo score

Il tempo continua a contare, ma nel posto corretto:

- `priority_score`

Input temporali ammessi:

- prossimita del primo ordine cliente rilevante
- in futuro:
  - prima data realmente scoperta
  - priorita ordine
  - earliest feasible start / completion

## Consequences

### Positive

- il Core planning diventa piu semplice da spiegare
- si elimina l'ambiguita tra bisogno cliente e urgenza cliente
- il rebase procede con una sola semantica, non con doppia compatibilita

### Operational

- `TASK-V2-145` deve essere eseguito con rimozione diretta di `customer_horizon_days` dal calcolo Core
- i task UI che parlano di `Orizzonte cliente` vanno riletti come:
  - filtro visivo
  - segnale di priorita
  - non filtro semantico del bisogno

### Guardrail

- non reintrodurre eccezioni `future shortage` dentro il Core per compensare questa scelta
- se serve piu raffinatezza, aggiungerla nello score o nella spiegazione UI
