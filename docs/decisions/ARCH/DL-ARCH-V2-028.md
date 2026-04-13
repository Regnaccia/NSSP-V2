# DL-ARCH-V2-028 - Refinement finale di Planning Candidates prima di Production Proposals

## Status

Accepted

## Date

2026-04-13

## Context

`Planning Candidates` esiste gia come modulo operativo con branching reale tra:

- `by_article`
- `by_customer_order_line`

Prima di aprire il modulo `Production Proposals`, il planning deve essere chiuso meglio su quattro aspetti:

- regola generale sulla giacenza negativa
- descrizione da mostrare per i candidate non aggregati
- esposizione della misura
- esposizione esplicita della reason del candidate

## Decision

### 1. Stock negativo trattato come anomalia, non come need produttivo

Per tutto il modulo `Planning Candidates` vale la regola:

```text
stock_effective = max(stock_calculated, 0)
```

Conseguenze:

- `stock_calculated` resta disponibile come dato tecnico
- la logica planning usa solo `stock_effective`
- la sola giacenza negativa non genera un candidate
- la giacenza negativa non compare come reason del candidate

La gestione delle anomalie inventariali viene rinviata al futuro modulo `Warnings`.

### 2. Descrizione ramo by_customer_order_line

Quando `planning_mode = by_customer_order_line`, la descrizione mostrata deve essere quella della riga ordine cliente.

La descrizione anagrafica articolo non e la fonte primaria di verita per questo ramo.

### 3. Misura esposta nella vista

La vista `Planning Candidates` deve esporre anche la misura, per migliorare la leggibilita operativa dei candidate.

### 4. Reason obbligatoria

Ogni candidate deve esporre in modo esplicito:

- `reason_code`
- `reason_text`

La presence del candidate non deve essere opaca o interpretabile solo indirettamente dai numeri.

## Consequences

### Positive

- separazione piu chiara tra bisogno produttivo e anomalia dati
- UI planning piu leggibile nel ramo per-riga ordine
- migliore continuita semantica verso il futuro modulo `Production Proposals`

### Tradeoffs

- il modulo `Warnings` diventa un follow-up necessario per non perdere visibilita sulle anomalie inventariali
- il read model planning deve portare qualche campo descrittivo in piu

## Out of Scope

- introdurre gia il modulo `Warnings`
- aprire il lifecycle di `Production Proposals`
- introdurre scoring, horizon o policy stock-driven

## References

- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`
- `docs/specs/PLANNING_CANDIDATES_AGGREGATION_V2_REDUCED_SPEC.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/decisions/ARCH/DL-ARCH-V2-027.md`
