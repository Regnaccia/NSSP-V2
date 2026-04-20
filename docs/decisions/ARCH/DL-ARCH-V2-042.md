# DL-ARCH-V2-042 - Rebase target di `Planning Candidates`: modello semplice + `priority_score` evolutivo

## Status
Active

## Date
2026-04-17

## Context

Il rebase V2 ha gia fissato:

- `Planning Candidates` come inbox del bisogno
- split esplicito `need vs release now`
- `Unified Planning Workspace` come surface primaria

Restano pero ambiguita semantiche nell'area planning, in particolare tra:

- classificazione del bisogno
- urgenza temporale
- ordinamento operativo dei candidate

I casi reali discussi durante il rebase mostrano che il modello attuale basato su:

- `customer_horizon_days` dentro il calcolo di `customer_shortage_qty`
- `stock horizon` nella sola componente scorta

produce candidate corretti per slicing operativo locale, ma meno lineari da spiegare quando:

- esistono ordini cliente futuri gia noti
- il bisogno non e urgente oggi
- ma l'articolo appare comunque come caso `stock`

Questa complessita rischia di trasferire nel Core un problema che appartiene piu correttamente al livello di priorita.

## Decision

Il target del rebase planning viene chiarito con questa regola:

> il Core planning deve restare semplice e stabile; l'urgenza operativa deve crescere in un layer separato di `priority_score`

## Contract

### 1. Il candidate ha quattro assi semantici distinti

Ogni candidate deve essere leggibile su quattro assi indipendenti:

1. `perche esiste`
   - `primary_driver`
   - `reason_code`
   - `reason_text`
2. `quanto manca`
   - `customer_shortage_qty`
   - `stock_replenishment_qty`
   - `required_qty_total`
   - `required_qty_eventual`
3. `quanto e lanciabile ora`
   - `release_qty_now_max`
   - `release_status`
4. `quanto e prioritario adesso`
   - `priority_score`

Regola:

- il planning Core non deve mischiare questi quattro assi nello stesso numero o nello stesso badge

### 2. Target del modello planning

Nel modello target del rebase:

- la componente `customer` rappresenta la domanda cliente aperta reale
- la componente `stock` rappresenta il buffer/target di scorta
- la priorita temporale non ridefinisce da sola il driver del candidate

Target concettuale:

- `customer_shortage_qty`
  - basato sulla domanda cliente aperta reale
- `stock_replenishment_qty`
  - basato sulla policy di scorta
- `required_qty_total`
  - somma delle due componenti

Conseguenza desiderata:

- `Cliente`
- `Cliente + Magazzino`
- `Magazzino`

restano classificazioni stabili e spiegabili, senza dover introdurre nel Core nuovi sotto-tipi ibridi solo per rappresentare l'urgenza.

### 3. `customer_horizon` cambia ruolo nel target rebase

Nel target rebase:

- `customer_horizon_days` non e piu il fondamento semantico della classificazione `customer`
- diventa un input di workspace/priorita
- puo continuare a essere usato in UI per:
  - evidenza ordini vicini
  - filtri visivi
  - ranking
  - spiegazione del contesto

Nota:

- la chiusura operativa di questa scelta e stata poi fissata in `DL-ARCH-V2-043`
- quindi la V2 non mantiene una lunga fase di compatibilita: `customer_horizon` esce dal Core planning

### 4. `priority_score` viene introdotto come layer evolutivo separato

`priority_score` non ridefinisce il bisogno.

Serve a:

- ordinare i candidate
- evidenziare i casi da trattare prima
- incorporare progressivamente nuove informazioni operative senza destabilizzare il Core planning

Regole:

- deve essere spiegabile
- non deve essere un numero opaco o "magico"
- deve poter evolvere per componenti

Vocabolario iniziale raccomandato:

- `priority_score`
- opzionalmente in futuro:
  - `priority_customer_urgency`
  - `priority_supply_risk`
  - `priority_release_penalty`
  - `priority_warning_penalty`

### 5. Baseline iniziale dello score

La V1 dello score puo essere semplice.

Input iniziali raccomandati:

- prossimita della prima data cliente rilevante
- severita della componente `customer_shortage_qty`
- `release_status`
- presenza warning

Questa baseline deve essere trattata come:

- placeholder utile
- non ancora algoritmo definitivo

### 6. Roadmap evolutiva dello score

Il modello e progettato per crescere.

Input futuri ammessi:

- prima data realmente scoperta dopo allocazione stock
- priorita ordine
- assegnazione automatica stock a ordini
- costo / penalita di cambio setup
- tempi di processo e lavorazione
- data minima di inizio produzione
- data minima di completamento

Regola:

- questi input futuri raffinano `priority_score`
- non devono cambiare retroattivamente il significato dei fact base del candidate

### 7. Impatto sul `Unified Planning Workspace`

La surface planning deve riflettere questa separazione:

- colonna sinistra:
  - mostra `priority_score` come segnale di ordinamento/priorita
- colonna centrale:
  - spiega bisogno, release e contesto
- colonna destra:
  - governa configurazione e proposta

Regola:

- `priority_score` non sostituisce `reason_code`, `reason_text` o `release_status`
- li affianca

## Consequences

### Positive

- il planning target diventa piu lineare
- il tempo viene gestito nel posto corretto: la priorita
- la classificazione `Cliente / Cliente + Magazzino / Magazzino` torna piu stabile
- il progetto si prepara meglio ai futuri moduli:
  - allocazione stock
  - priorita ordini
  - processi e setup

### Transitional

- il modello attuale con `customer_horizon` nel calcolo resta ancora compatibilita implementata
- servira un task esplicito di rebase Core planning per convergere al target
- i task UI gia aperti sul workspace non vanno buttati:
  - vanno riletti alla luce di `priority_score` come layer separato

### Guardrail

- non introdurre `priority_score` come algoritmo opaco unico
- non spostare nel punteggio regole di dominio che dovrebbero restare nei fact base
- non usare lo score per correggere fact incoerenti o ambigui
