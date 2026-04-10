# 📄 PLANNING CANDIDATES — MODULE SPEC (V1.1)

---

## 1. Contesto

Il sistema dispone di:

* sincronizzazione dati da EasyJob (read-only)
* fact canonici:

  * inventory
  * commitments
  * availability
* dati su produzioni attive
* logiche di dominio sugli articoli
* refresh semantico backend

È presente una vista **“criticità articoli”** basata su disponibilità negativa (`availability < 0`), utile ma limitata.

---

## 2. Obiettivo del modulo

Il modulo **Planning Candidates** ha lo scopo di:

> Identificare e rappresentare i fabbisogni produttivi che meritano attenzione, tenendo conto di domanda, stock e copertura già in essere.

Produce una lista:

* spiegabile
* non duplicata
* prioritizzata

---

## 3. Scope

### ✔ Il modulo FA

* identifica fabbisogni produttivi
* integra domanda cliente, stock e produzioni attive
* evita duplicazioni logiche
* distingue aggregazione / non aggregazione
* introduce dimensione temporale
* priorizza tramite scoring

---

### ❌ Il modulo NON FA

* non calcola quantità produttive finali
* non applica lotti o multipli
* non schedula produzione
* non assegna risorse/macchine

---

## 4. Posizionamento architetturale

Layer:

* Core / Domain Logic (read model / projection)

Input:

* articoli
* righe ordine cliente
* stock
* commitments
* produzioni attive

Output:

* lista Planning Candidates

---

## 5. Concetti chiave

---

### 5.1 Planning Identity

Unità logica su cui si genera un candidate:

* articolo (se aggregabile)
* riga ordine (se non aggregabile)

---

### 5.2 Unicità del candidate

> Per ogni Planning Identity esiste al massimo un candidate principale.

Non sono ammessi duplicati per:

* shortage cliente
* reintegro stock

---

### 5.3 Origine del fabbisogno

```text
customer
stock
```

---

### 5.4 Comportamento di aggregazione

```text
aggregable
non_aggregable
```

---

### 5.5 Candidate multi-causale

Un candidate può avere più cause attive:

Esempi:

* `customer_shortage`
* `stock_below_target`
* `future_shortage`

---

## 6. Dimensione temporale

Parametro:

* **planning_horizon**

Distinzione:

* domanda entro orizzonte
* domanda oltre orizzonte

---

## 7. Stati del candidate

```text
immediate
monitor
```

---

### Immediate

* scopertura entro orizzonte

### Monitor

* copertura nel breve
* scopertura futura

---

## 8. Integrazione produzioni attive

Le produzioni attive sono considerate:

> copertura futura (incoming supply)

NON sono origine del candidate.

---

### Campi chiave

* available_now_qty
* incoming_production_qty
* incoming_within_horizon_qty

---

### Effetto

Le produzioni attive:

* riducono la scopertura reale
* influenzano stato e priorità

---

## 9. Quantità (multi-livello)

Il candidate espone più livelli:

* required_qty_customer
* required_qty_stock
* required_qty_minimum
* stock_gap_qty

---

### Definizioni

* **required_qty_customer** → scopertura da domanda cliente
* **required_qty_stock** → gap rispetto a target stock
* **required_qty_minimum** → fabbisogno minimo certo
* **stock_gap_qty** → differenza da target

---

### Esclusioni

NON viene calcolata:

* quantità produttiva finale

---

## 10. Regole stock vs customer

### Caso 1 — presenza domanda cliente

→ un solo candidate

* origine primaria: customer
* stock diventa causa secondaria

---

### Caso 2 — nessuna domanda cliente

→ candidate stock-driven autonomo

---

## 11. Sistema di scoring

### Formula

```text
priority_score =
  origin_weight
+ urgency_score
+ shortage_score
```

---

### Componenti

#### Origin Weight

* customer → alto
* stock → medio/basso

---

#### Urgency Score

* basato su date consegna

---

#### Shortage Score

* basato su scopertura reale (post produzione)

---

### Trasparenza

Ogni candidate include:

* priority_score
* score_breakdown

---

## 12. Entity Model

```text
PlanningCandidate

candidate_id

planning_key
scope_type (article / order_line)

primary_origin_type

aggregation_policy

article_code

order_id (optional)
order_line_id (optional)

candidate_status

active_reason_codes

reason_text

demand_due_date_min
demand_due_date_max

total_committed_qty
horizon_committed_qty

available_now_qty

incoming_production_qty
incoming_within_horizon_qty

net_available_qty

required_qty_customer
required_qty_stock
required_qty_minimum

stock_gap_qty

priority_score
score_breakdown
```

---

## 13. Regole di generazione

---

### Customer + Aggregable

* aggregazione per articolo
* calcolo copertura netta (inclusa produzione)

---

### Customer + Non Aggregable

* un candidate per riga ordine

---

### Stock-driven

* solo se nessuna domanda cliente rilevante
* policy esplicita richiesta

---

## 14. Esempi concreti

---

### Caso 1 — Produzione già attiva

Input:

* stock: 500
* domanda entro horizon: 1200
* produzione attiva: 900 (entro horizon)

Output:

```text
required_qty_customer: 0

candidate_status: monitor
reason: covered_by_incoming_production
```

---

### Caso 2 — Shortage reale

Input:

* stock: 500
* domanda: 1200
* produzione: 400

Output:

```text
required_qty_customer: 300

candidate_status: immediate
reason: shortage_within_horizon
```

---

### Caso 3 — Codice S

Input:

* riga 1: 50pz
* riga 2: 80pz

Output:

```text
2 candidate separati (non aggregable)
```

---

### Caso 4 — Mix customer + stock

Input:

* stock: 300
* domanda: 500
* target stock: 800

Output:

```text
required_qty_customer: 200
stock_gap_qty: 500

reason_codes:
  - customer_shortage
  - stock_below_target
```

---

### Caso 5 — Solo stock

Input:

* stock: 100
* target: 500
* nessun ordine

Output:

```text
candidate stock-driven

required_qty_stock: 400
candidate_status: monitor
```

---

## 15. Output del modulo

Lista ordinata di Planning Candidates:

* non duplicata
* multi-causale
* spiegabile

---

## 16. Relazione con sistema attuale

* evolve la logica di criticità
* introduce un livello decisionale superiore
* mantiene compatibilità con fact esistenti

---

## 17. Relazione con moduli futuri

Output → input per:

* Production Proposal
* Scheduler

---

## 18. Principio guida finale

> Planning Candidates rappresenta la pressione produttiva reale, considerando domanda cliente, politiche di stock e copertura già in essere, evitando duplicazioni e senza anticipare decisioni produttive.

---
