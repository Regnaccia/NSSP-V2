# DL-ARCH-V2-039 - V2 architectural rebase baseline using V4 as knowledge

## Status
Active

## Date
2026-04-15

## Context

La V2 ha ormai una base tecnica reale e valida:

- layer stabili `sync / core / app / shared`
- Easy sempre read-only
- fact canonici consolidati
- `Planning Candidates` come inbox operativa reale
- `Warnings` come modulo trasversale canonico
- `Production Proposals` come workspace/export module downstream

Il punto di attenzione non e piu il bootstrap tecnico, ma la frammentazione progressiva del modello di dominio, in particolare tra:

- need vs release now
- warning canonico vs diagnostica locale
- proprieta dei dati tra finito, materiale grezzo, famiglia e admin
- logiche proposal cresciute come elenco di strategie monolitiche

Il progetto legacy V4 contiene logiche operative utili, ma non deve essere copiato strutturalmente. Va usato come fonte di conoscenza per consolidare il modello della V2.

## Decision

La V2 non viene abbandonata e non si apre una nuova `V3`.

Si adotta invece un `architectural rebase` in-place con questi principi stabili.

### 1. Moduli principali congelati

I moduli architetturali di riferimento della V2 sono:

- `canonical facts`
- `planning`
- `warnings`
- `proposals`
- `admin / articoli / famiglie`

I loro confini vengono considerati stabili.

### 2. Planning risponde al bisogno, non all'export

`Planning Candidates` risponde alla domanda:

```text
is there a need?
```

Ma da ora in poi deve anche distinguere il bisogno eventuale dalla fattibilita di rilascio immediata.

Contratto target del modulo:

- `required_qty_eventual`
- `release_qty_now_max`
- `release_status`
  - `launchable_now`
  - `launchable_partially`
  - `blocked_by_capacity_now`

Compatibilita:

- i campi oggi esistenti restano durante la transizione
- `required_qty_total` resta il breakdown quantitativo attuale del need
- il nuovo split non sostituisce subito il contratto attuale, lo chiarisce

Giustificazione V4:

```text
da_produrre = min(cap_residua, prod_a_scorta)
```

Questa formula mostra che:

- il need eventuale
- e la quantita lanciabile ora

non sono lo stesso concetto.

### 3. Proposals risponde al rilascio/export downstream

`Production Proposals` resta downstream di `Planning Candidates` e risponde alla domanda:

```text
what do we release/export?
```

La fattibilita di rilascio non deve nascere solo dentro le logiche proposal.

Il modulo proposals:

- consuma candidate selezionati
- lavora su uno snapshot/workspace
- prepara override, export e reconcile

ma non deve diventare una seconda inbox che ridefinisce da zero il bisogno.

### 4. Le logiche proposal evolvono verso assi di policy configurabili

Il modello concettuale target non e un elenco infinito di strategy key monolitiche.

Le future logiche proposal vanno pensate come bundle di policy su assi distinti:

- `proposal_base_qty_policy`
- `proposal_lot_policy`
- `proposal_capacity_policy`
- `proposal_customer_guardrail_policy`
- `proposal_note_policy`

Compatibilita a breve termine:

- `proposal_logic_key` resta la surface di compatibilita nel modello reale
- le key esistenti vengono reinterpretate come bundle impliciti di assi

Mapping concettuale iniziale:

- `proposal_target_pieces_v1`
  - base qty: `required_qty_total`
  - lot policy: `pieces`
  - capacity policy: `none`
  - customer guardrail: `cover_customer_shortage`
  - note policy: `none`
- `proposal_full_bar_v1`
  - base qty: `required_qty_total`
  - lot policy: `full_bar`
  - capacity policy: `strict_capacity`
  - customer guardrail: `never_undercover_customer`
  - note policy: `bar_count`
- `proposal_full_bar_v2_capacity_floor`
  - base qty: `required_qty_total`
  - lot policy: `full_bar`
  - capacity policy: `capacity_floor`
  - customer guardrail: `never_undercover_customer`
  - note policy: `bar_count`

La conoscenza V4 da assorbire negli assi di policy e:

- `use_all`
- `print_to_note`
- tentativo `ceil` e poi `floor` sotto capienza
- eccedenza lato cliente resa esplicita come componente magazzino, non nascosta

### 5. Ownership dei dati materiale congelata

La proprieta dei dati viene fissata cosi:

- articolo finito:
  - semantica cliente/scorta
  - assegnazione della proposal logic
  - input `mm` per pezzo
- articolo materiale grezzo:
  - `raw_bar_length_mm`
  - configurazione di processo specifica del grezzo
- famiglia:
  - flag di abilitazione/eligibility
  - default di configurazione
  - mai stato esecutivo
- admin:
  - registry globali
  - default globali delle policy

Regola esplicita:

- `raw_bar_length_mm` appartiene semanticamente all'articolo materiale grezzo, non al finito

### 6. Warning canonici separati dalla diagnostica locale

Questa separazione diventa regola generale di progetto:

- `Warnings` contiene anomalie cross-module e canoniche
- la diagnostica locale spiega esiti decisionali interni del singolo modulo

Esempi:

- warning canonico:
  - `MISSING_RAW_BAR_LENGTH`
- diagnostica locale proposal:
  - `requested_proposal_logic_key`
  - `effective_proposal_logic_key`
  - `proposal_fallback_reason`

Nuovi slice non devono piu mescolare questi due piani.

### 7. Il rebase di dominio e separato dal backbone hardening

La roadmap viene separata in due stream indipendenti.

#### Domain Rebase

- baseline architetturale
- contratto planning `need vs release now`
- contratto proposal a policy axes
- riscrittura backlog proposal

#### Backbone Hardening

- strategia strutturale `MAG_REALE`
- refresh fail-fast e freshness
- gestione orfani `core_articolo_config`

Ordine di esecuzione raccomandato:

1. baseline architetturale
2. rebase planning
3. rebase proposal
4. backlog rewrite
5. backbone hardening

## Consequences

### Positive

- si evita una falsa ripartenza `V3`
- si preserva il valore tecnico gia costruito in V2
- si chiariscono i confini tra need, release, warning, proposal e ownership dati
- le future logiche proposal vengono progettate come policy composte e non come lista aperta di eccezioni

### Operational

- i task proposal `115-127` non sono piu una roadmap lineare da eseguire ciecamente
- i task gia chiusi restano validi come slice di compatibilita, ma vanno riletti nel nuovo modello
- il backlog attivo deve essere riscritto esplicitamente contro questa baseline

### Guardrail

- nessun nuovo repository `V3`
- nessuna riscrittura dei layer
- nessuna logica futura deve ridefinire ownership o boundaries senza nuovo DL esplicito
