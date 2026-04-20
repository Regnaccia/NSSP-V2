# DL-ARCH-V2-044 - Contratto di `priority_score_v1_basic`

## Status
Active

## Date
2026-04-19

## Context

Il rebase planning ha gia fissato che:

- il Core deve restare semplice
- `customer_horizon` non deve piu alterare il bisogno
- `priority_score` e un layer separato di ordinamento/priorita

La baseline introdotta in `TASK-V2-145` ha aperto il campo `priority_score`, ma non ha ancora congelato un contratto V1 abbastanza stabile e spiegabile per:

- sorting della inbox planning
- lettura UX coerente
- evoluzione futura verso score piu raffinati

## Decision

La V1 del punteggio viene fissata come:

> `priority_score_v1_basic` = policy di scoring sostituibile, unica policy attiva iniziale, spiegabile per componenti

Regole:

- lo score non ridefinisce il bisogno
- lo score non cambia `primary_driver`, `reason_code`, `reason_text` o `release_status`
- lo score ordina i candidate
- la V1 usa componenti additive semplici e difendibili

## Contract

### 1. Policy model

Il modello target e:

- `priority_score_policy_key`
  - iniziale: `priority_score_v1_basic`

Vincolo:

- in V1 non si introduce ancora una governance admin complessa
- esiste una sola policy attiva globale
- l'architettura resta comunque sostituibile

### 2. Input minimi

La policy V1 puo usare:

- `primary_driver`
- `customer_shortage_qty`
- `stock_replenishment_qty`
- `required_qty_eventual`
- `release_status`
- `active_warning_codes`
- `requested_delivery_date` nel ramo `by_customer_order_line`
- `earliest_customer_delivery_date` / `nearest_delivery_date` nel ramo `by_article`
- `stock_effective_qty`
- `target_stock_qty`

### 3. Output minimi

La V1 deve esporre almeno:

- `priority_score`
  - range target `0..100`

Output opzionali ma raccomandati:

- `priority_band`
  - `low`
  - `medium`
  - `high`
  - `critical`
- `priority_reason_summary`
- `priority_components`

### 4. Formula V1

La formula V1 e additiva:

```text
priority_score =
  time_urgency
  + customer_pressure
  + stock_pressure
  - release_penalty
  - warning_penalty
```

Poi:

- clamp minimo `0`
- clamp massimo `100`

### 5. Componenti

#### `time_urgency`

Data rilevante:

- `by_customer_order_line` -> `requested_delivery_date`
- `by_article` -> `earliest_customer_delivery_date ?? nearest_delivery_date`

Fasce iniziali:

- `<= 7 giorni` -> `35`
- `<= 15 giorni` -> `28`
- `<= 30 giorni` -> `20`
- `<= 60 giorni` -> `10`
- `> 60 giorni` -> `4`
- nessuna data -> `0`

#### `customer_pressure`

Regole:

- se `customer_shortage_qty <= 0` -> `0`
- altrimenti:
  - base `20`
  - severita quantita:
    - `> 0` -> `+5`
    - `>= 100` -> `+10`
    - `>= 500` -> `+15`
    - `>= 1000` -> `+20`

Cap componente:

- max `40`

#### `stock_pressure`

La V1 usa una severita **ratio-based**, non una scala assoluta sulla quantita.

Indicatore:

```text
stock_position_ratio = stock_effective_qty / target_stock_qty
```

Uso:

- se `stock_replenishment_qty <= 0` -> `0`
- se `target_stock_qty <= 0` -> `0`
- altrimenti:
  - `ratio >= 1.0` -> `0`
  - `0.75 <= ratio < 1.0` -> `4`
  - `0.50 <= ratio < 0.75` -> `8`
  - `0.25 <= ratio < 0.50` -> `14`
  - `0 <= ratio < 0.25` -> `20`
  - `ratio < 0` -> `24`

Motivazione:

- l'urgenza stock deve riflettere la posizione relativa rispetto al target
- non la sola quantita assoluta proposta

#### `release_penalty`

- `launchable_now` -> `0`
- `launchable_partially` -> `8`
- `blocked_by_capacity_now` -> `18`
- `null` -> `0`

#### `warning_penalty`

- `0 warning` -> `0`
- `1 warning` -> `4`
- `2-3 warning` -> `8`
- `>= 4 warning` -> `12`

### 6. Bande V1

- `0..24` -> `low`
- `25..49` -> `medium`
- `50..74` -> `high`
- `75..100` -> `critical`

### 7. Guardrail

- `customer` pesa piu di `stock`
- lo score non corregge fact di dominio sbagliati
- il tempo influenza la priorita, non il bisogno
- warning e release penalizzano, ma non annullano da soli il candidate

## Consequences

### Positive

- inbox planning ordinabile con criterio leggibile
- `stock_pressure` piu coerente con la gravita reale
- preparazione corretta per evoluzioni future:
  - priorita ordini
  - allocazione stock
  - setup e tempi produzione

### Deferred

Restano fuori da V1:

- policy admin selezionabili
- score per articolo o famiglia
- allocazione stock a ordini
- priorita ERP
- setup/processi
- earliest start / completion

## Follow-up

- task attuativo dedicato:
  - `TASK-V2-149`
