# PRODUCTION_PROPOSALS_SPEC_V1_0

## 1. Contesto

Il sistema dispone gia di:

- mirror Easy read-only
- fact canonici:
  - `inventory`
  - `commitments`
  - `customer_set_aside`
  - `availability`
- Core `produzioni`
- Core e UI `Planning Candidates`
- planning policy a livello famiglia e articolo

`Planning Candidates` identifica oggi il bisogno produttivo.

Manca ancora il livello successivo:

- trasformare il bisogno in una proposta operativa persistente
- gestire override, validazione, export e riconciliazione

## 2. Obiettivo del modulo

Il modulo `Production Proposals` ha lo scopo di:

- determinare cosa produrre
- proporre quantita operative realistiche
- supportare validazione ed export verso Easy
- mantenere separate le anomalie dati dalla decisione produttiva

## 3. Posizionamento architetturale

Pipeline target:

```text
Easy facts
-> ODE canonical facts
-> ODE Planning Candidates
-> ODE Production Proposals
-> ODE validation / export
-> Easy execution
-> ODE sync produzioni attive
```

Regola chiave:

- `Planning Candidates` rileva il bisogno
- `Production Proposals` prende in carico il bisogno e lo trasforma in decisione operativa persistente

## 4. Scope V1

### Il modulo FA

- crea una proposal persistente a partire da un bisogno gia identificato
- mantiene separati:
  - facts di partenza
  - proposta calcolata
  - override operatore
  - stato workflow
- consente validazione operativa prima dell'export
- prepara la correlazione robusta con Easy

### Il modulo NON FA ancora

- non fa scheduling
- non assegna macchine o risorse
- non calcola tempi reali di produzione
- non usa ancora scoring come parte del primo slice
- non introduce ancora archivio disegni o logiche predittive

## 5. Entita centrale

### Production Proposal

`Production Proposal` e l'oggetto operativo principale.

Rappresenta:

- fabbisogno derivato dai dati reali
- proposta quantitativa generata dalle logiche di business
- stato decisionale e operativo

Non e una semplice vista.
E una projection operativa con lifecycle proprio.

## 6. Dati base della proposal

### Facts di riferimento

- `article_code`
- `stock_calculated`
- `required_qty`
- `commitments`

### Dati derivati operativi

- `stock_effective = max(stock_calculated, 0)`
- `proposal_expansion_ratio = proposed_qty / required_qty`

Regola:

- `stock_calculated` resta sempre visibile per audit e debug
- `stock_effective` e il valore usato dalle logiche operative

## 7. Proposal decisionale

Campi attesi:

- `proposed_qty`
- `lot_applied`
- `multiple_applied`
- `stock_replenishment_qty`
- `policy_snapshot`

V1:

- la proposal parte dal `required_qty` gia emerso a monte
- applica solo la logica decisionale della proposta
- non ridefinisce da zero il bisogno

## 8. Override

Campi:

- `override_qty`
- `override_reason`
- `override_by`
- `override_at`

Regola:

```text
final_qty = override_qty se presente, altrimenti proposed_qty
```

## 9. Workflow minimo

Stati previsti:

- `draft`
- `validated`
- `exported`
- `reconciled`

## 10. UX V1

### Lista principale

Una singola lista operativa che mostra:

- articolo
- qty richiesta
- qty proposta
- indicatori sintetici
- eventuali warning

### Azioni principali

- apertura dettaglio
- override tramite modal
- validazione per export

## 11. Gestione giacenza negativa

### Problema

```text
stock_calculated < 0
```

### Regola V1

- `stock_effective = max(stock_calculated, 0)`

Usato per:

- logiche di produzione
- disponibilita operativa

### Conservazione del dato originario

- `stock_calculated` viene sempre mantenuto

Uso:

- audit
- debug
- analisi anomalie

### Principio

Le giacenze negative non generano automaticamente produzione.

Le anomalie vivono in un modulo separato:

- `Warnings`

## 12. Warnings

`Warnings` e un modulo separato da `Production Proposals`.

### Primo tipo V1

- `NEGATIVE_STOCK`

### Dati warning

- `article_code`
- `stock_calculated`
- `anomaly_qty`
- `type`
- `severity`
- `created_at`

### Nota

Le proposals possono mostrare:

- badge warning
- link alla schermata anomalie

Ma il lifecycle del warning resta separato dalla proposal.

## 13. Origine del need

Driver principale V1:

- domanda reale gia identificata in `Planning Candidates`

Driver futuri:

- candidate stock-driven
- policy piu ricche

Anomalie:

- non sempre generano produzione
- vanno trattate separatamente

## 14. Integrazione con Easy

### Problema

Easy assegna ID non controllati.

### Soluzione

Introduzione di una correlation key:

```text
[ODE_REF=PP000123]
```

### Posizionamento

Inserita nel campo note di Easy.

### Flusso di riconciliazione

```text
ODE export
-> Easy crea produzione
-> ODE sync produzioni
-> match tramite ODE_REF
```

### Mapping atteso

- `proposal_id <-> easy_production_id`

### Scelte escluse

- lettura "ultima riga Easy"
- flag booleani generici
- matching su articolo e quantita

## 15. Scoring

Lo scoring appartiene al modulo `Production Proposal`, ma non entra nel primo slice attuativo.

Posizionamento futuro:

- post-logica proposal
- pre-validazione o come supporto alla lista

Output futuri attesi:

- `need_score`
- `operational_cost_score`
- `business_value_score`
- `final_priority_score`

## 16. Principio architetturale

- ODE = sistema decisionale
- Easy = sistema esecutivo

Conseguenze:

- logica complessa in ODE
- Easy riceve solo l'output minimo necessario
- la robustezza del modulo non dipende dai limiti del gestionale

## 17. Relazione con moduli esistenti

### Upstream

- `Planning Candidates`
  - detection del bisogno
  - input della proposal

### Parallelo

- `Warnings`
  - gestione separata delle anomalie

### Downstream

- export Easy
- sync produzioni attive
- riconciliazione proposal <-> produzione Easy

## 18. Principio guida finale

> `Production Proposals` prende in carico un bisogno gia identificato, lo trasforma in una decisione operativa persistente e validabile, mantenendo separate le anomalie dati dalla logica produttiva.
