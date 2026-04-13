# DL-ARCH-V2-030 - Stock Policy V1 come estensione minima del planning `by_article`

## Status

Accepted

## Date

2026-04-13

## Context

La V2 dispone gia di:

- `Planning Candidates` con:
  - `by_article`
  - `by_customer_order_line`
- `future_availability_qty`
- planning policy con:
  - default a livello famiglia
  - override a livello articolo
  - `planning_mode`

Serve introdurre una prima stock policy V1 senza aprire ancora `Production Proposals`
e senza rompere il significato gia stabilizzato di `Planning Candidates`.

## Decision

### 1. La stock policy V1 vale solo per `by_article`

La stock policy V1 si applica esclusivamente agli articoli con:

- `planning_mode = by_article`

Non si applica al ramo:

- `planning_mode = by_customer_order_line`

Conseguenza:

- non viene introdotto un flag separato `has_stock_policy`
- l'applicabilita della stock policy discende dal `planning_mode` effettivo

### 2. Configurazione minima

La stock policy V1 introduce:

Default famiglia:

- `stock_months`
- `stock_trigger_months`

Override articolo:

- `override_stock_months`
- `override_stock_trigger_months`
- `capacity_override_qty`

La `capacity` non ha default di famiglia.

Regola:

- la `capacity` e proprieta fisica dell'articolo
- quindi esiste solo a livello articolo come:
  - `capacity_calculated_qty`
  - `capacity_override_qty`
  - `capacity_effective_qty`

### 3. La quantita operativa di confronto resta `future_availability_qty`

La stock policy V1 non introduce un nuovo nome come `future_operational_stock_qty`.

Riusa direttamente:

- `future_availability_qty`

gia stabilita in `Planning Candidates by_article`.

### 4. Metrica base mensile calcolata con logica sostituibile

La stock policy V1 introduce:

- `monthly_stock_base_qty`

come quantita mensile di riferimento per il calcolo della scorta.

Regola architetturale:

- l'algoritmo di calcolo della base mensile deve essere sostituibile
- non deve vivere come formula hardcoded sparsa nei moduli operativi

### 5. Formule V1

La stock policy V1 introduce:

- `target_stock_qty = min(capacity_effective_qty, effective_stock_months * monthly_stock_base_qty)`
- `trigger_stock_qty = effective_stock_trigger_months * monthly_stock_base_qty`

### 6. Trigger stock-driven

Si apre un bisogno stock-driven se:

- `future_availability_qty < trigger_stock_qty`

### 7. Evitare il doppio conteggio con shortage cliente

Nel ramo `by_article` non devono nascere due candidate separati:

- uno per shortage cliente
- uno per scorta

La regola corretta e:

- un solo candidate per articolo
- con breakdown interno:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `required_qty_total`

Formule:

- `customer_shortage_qty = max(-future_availability_qty, 0)`
- `stock_replenishment_qty = max(target_stock_qty - max(future_availability_qty, 0), 0)`
- `required_qty_total = customer_shortage_qty + stock_replenishment_qty`

## Consequences

### Positive

- la stock policy entra nel planning senza introdurre un modulo separato prematuro
- il modello resta coerente con `planning_mode`
- si evita il doppio candidate cliente/scorta
- si prepara bene l'apertura futura di `Production Proposals`

### Tradeoffs

- la stock policy resta inizialmente limitata al solo ramo `by_article`
- l'algoritmo V1 per `monthly_stock_base_qty` dovra essere definito con attenzione nei task attuativi

## Out of Scope

- stagionalita
- algoritmi multipli selezionabili in UI
- stock policy nel ramo `by_customer_order_line`
- `Production Proposals`
- scoring e prioritizzazione

## References

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`
