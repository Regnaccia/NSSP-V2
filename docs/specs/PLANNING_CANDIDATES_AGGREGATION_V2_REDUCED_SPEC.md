# PLANNING CANDIDATES - AGGREGATION V2 REDUCED SPEC

## Purpose

This document defines the first reduced expansion of `Planning Candidates` after the current V1.

It introduces two planning modes driven by effective planning policy:

- `by_article`
- `by_customer_order_line`

The purpose is to make aggregation behavior explicit without yet introducing:

- scoring
- planning horizon
- stock-driven logic
- advanced scheduling

## Context

Current V2 already provides:

- `Planning Candidates` V1 aggregated by `article`
- family defaults and article overrides for planning policy
- effective policy values exposed by Core `articoli`
- customer order lines with stable row identity
- active and historical productions with customer-order references

The current open design question is no longer whether planning candidates exist, but how they must behave when aggregation by article is not operationally correct.

## Goal

`Planning Candidates Aggregation V2` must support two distinct planning behaviors:

- aggregated by `article` when aggregation is allowed
- per customer order line when aggregation is not allowed

This decision must be driven by effective planning policy, not by UI hardcode.

## Planning Policy Driver

The controlling policy is:

- `effective_aggrega_codice_in_produzione`

Semantics:

- `true` -> planning mode `by_article`
- `false` -> planning mode `by_customer_order_line`

This keeps the behavior aligned with:

- family-level defaults
- article-level overrides
- effective policy resolution already introduced in V2

## Planning Modes

### 1. by_article

This is the current V1 behavior and remains unchanged.

It applies when:

```text
effective_aggrega_codice_in_produzione = true
```

Identity:

```text
article_code
```

Main inputs:

- `availability_qty`
- `customer_open_demand_qty`
- `incoming_supply_qty`

Formula:

```text
future_availability_qty = availability_qty + incoming_supply_qty
```

Candidate rule:

```text
future_availability_qty < 0
```

Minimum shortage:

```text
required_qty_minimum = abs(future_availability_qty)
```

### 2. by_customer_order_line

This is the new reduced V2 mode.

It applies when:

```text
effective_aggrega_codice_in_produzione = false
```

The planning candidate is no longer article-aggregated.
It is tied to a specific customer order line.

## by_customer_order_line - Identity

Minimum identity:

- `numero_ordine_cliente`
- `riga_ordine_cliente`

In implementation terms this should map to the stable order-line identity already available in Core order lines.

There can therefore be multiple planning candidates for the same `article_code`.

## by_customer_order_line - Demand

Open demand is not aggregated by article.

The per-line demand is:

```text
line_open_demand_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```

This intentionally mirrors the existing semantic already used in `customer_order_lines`.

## by_customer_order_line - Availability

Current free stock is intentionally ignored.

For this mode:

```text
availability_qty = 0
```

Reason:

- the planning decision is not "is there free stock for the article in general?"
- the planning decision is "is this specific order line already covered by linked production?"

This makes the mode operationally commessa/riga-oriented instead of stock-oriented.

## by_customer_order_line - Incoming Supply

Incoming supply is not aggregated by article.

It is computed only from productions explicitly linked to the same customer order line.

Matching keys:

- candidate side:
  - `numero_ordine_cliente`
  - `riga_ordine_cliente`
- production side:
  - `riferimento_numero_ordine_cliente`
  - `riferimento_riga_ordine_cliente`

Relevant production supply includes:

- active productions linked to that order line

Historical productions may be consulted only if needed for correctness or continuity, and should be time-filtered conservatively if performance requires it.

Suggested minimum performance guard:

- if historical productions are used, filter from `order_date` forward

## by_customer_order_line - Coverage Metric

This mode should not reuse the article-level meaning of `future_availability_qty` ambiguously.

Suggested metric:

```text
line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty
```

Meaning:

- positive or zero: the linked production already covers the line
- negative: the line still requires new production attention

Candidate rule:

```text
line_future_coverage_qty < 0
```

Minimum shortage:

```text
required_qty_minimum = abs(line_future_coverage_qty)
```

## Unified Interpretation

The module now has two valid candidate-generation behaviors:

- stock/code-oriented planning
- order-line-oriented planning

They are both valid, but they must not be mixed implicitly.

The consumer must always be able to infer which planning mode produced the candidate.

Suggested explicit output field:

- `planning_mode`

Allowed values:

- `by_article`
- `by_customer_order_line`

## Reduced Output Shape

### by_article

Suggested fields:

- `planning_mode`
- `article_code`
- `availability_qty`
- `incoming_supply_qty`
- `future_availability_qty`
- `required_qty_minimum`
- `computed_at`

### by_customer_order_line

Suggested fields:

- `planning_mode`
- `article_code`
- `numero_ordine_cliente`
- `riga_ordine_cliente`
- `line_open_demand_qty`
- `linked_incoming_supply_qty`
- `line_future_coverage_qty`
- `required_qty_minimum`
- `computed_at`

## Explicit Non-Goals

Still out of scope for this reduced V2:

- stock-driven candidates
- planning horizon
- ETA-based logic
- scoring / ranking
- lot sizing
- machine scheduling
- richer aggregation policy than the single mode switch above

## Practical Consequence

This reduced V2 is not just a UI refinement.

It introduces a structural fork in planning logic:

- one candidate model by `article`
- one candidate model by `customer_order_line`

This is therefore expected to require:

- a dedicated `DL`
- Core work before UI refinement

## Future Expansion Path

This reduced V2 intentionally prepares later expansions:

- richer aggregation policies beyond the simple boolean switch
- family defaults plus article exceptions already in place
- order-line planning with temporal slices
- stock-driven candidates
- score and prioritization layers
