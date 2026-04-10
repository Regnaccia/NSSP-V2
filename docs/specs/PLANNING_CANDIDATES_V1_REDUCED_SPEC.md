# PLANNING CANDIDATES - V1 REDUCED SPEC

## Purpose

This document defines the first implementable slice of `Planning Candidates`.

It is intentionally narrower than [PLANNING_CANDIDATES_SPEC_V1_1.md](PLANNING_CANDIDATES_SPEC_V1_1.md):

- only `customer-driven`
- only aggregated by `article`
- no stock-driven policy
- no temporal horizon
- no scoring
- no aggregation policy variants yet

Its purpose is to give a clean base for the first `DL` and the first implementation tasks.

## Context

The current V2 already provides:

- `inventory`
- `commitments`
- `customer_set_aside`
- `availability`
- `customer_order_lines`
- `produzioni attive`
- semantic backend refreshes
- a first `criticita articoli` view based on `availability_qty < 0`

The planning module must now move from pure criticality detection to a first operational question:

> Do we still need to start or plan new production for an article?

## V1 Goal

`Planning Candidates V1` must identify articles that still require new production attention even after considering:

- current free availability
- active productions already in progress

The module does not answer:

- when production will be ready
- how much to produce as final batch quantity
- how to schedule or assign resources

## Scope

### In scope

- article-level aggregated planning signal
- customer-driven demand only
- active production treated as simple incoming supply
- simple shortage logic
- first operational list of candidates

### Out of scope

- stock-driven candidates
- safety stock / target stock
- planning horizon
- due-date prioritization
- scoring / ranking formula
- order-line candidates
- aggregation policy variants
- lot sizing
- scheduling

## Canonical Inputs

The V1 uses names already aligned with the current V2 model.

- `availability_qty`
- `customer_open_demand_qty`
- `incoming_supply_qty`

### availability_qty

Already available canonical fact.

Meaning:

- currently free quantity after subtracting `customer_set_aside` and `commitments`

### customer_open_demand_qty

Aggregated open customer demand by article.

For V1 this is a planning-facing aggregate derived from open customer order lines.

### incoming_supply_qty

Aggregated open supply already in progress from active productions.

For V1:

- it is binary in semantic intent: production is already active, therefore supply is considered incoming
- no ETA or horizon logic is applied
- no distinction yet between near-term and late supply

## New V1 Concept

### future_availability_qty

Formula:

```text
future_availability_qty = availability_qty + incoming_supply_qty
```

Meaning:

- quantity expected to be available after already active productions are completed
- still intentionally time-agnostic in V1

This becomes the main quantitative reference for Planning Candidates V1.

## Candidate Generation Rule

V1 is fully aggregated by article.

There is no per-order-line candidate in this first slice.

### Primary rule

An article becomes a planning candidate if:

```text
future_availability_qty < 0
```

Meaning:

- current free availability is not enough
- active incoming production is still not enough
- therefore new production attention is still required

### Required quantity

V1 may expose a minimum shortage quantity as:

```text
required_qty_minimum = abs(future_availability_qty)
```

only when `future_availability_qty < 0`, otherwise `0`.

## Candidate Identity

For V1 the candidate identity is:

```text
article_code
```

There is at most one active planning candidate per article.

## Candidate Status

V1 does not use multiple states such as `monitor`.

The simplified model is:

- candidate present
- candidate absent

Reason:

- once `incoming_supply_qty` is already incorporated into `future_availability_qty`, the intermediate state "not covered now but already covered by active production" is no longer needed for V1

## Output Shape

A first V1 candidate/read model should be explainable and minimal.

Suggested fields:

- `article_code`
- `availability_qty`
- `incoming_supply_qty`
- `future_availability_qty`
- `required_qty_minimum`
- `computed_at`

Optional descriptive fields for UI projection:

- `article_description`
- `family_name`
- `considera_in_produzione`

## Interaction With Existing Logic

`Planning Candidates V1` is not a replacement for `criticita articoli`.

Relationship:

- `criticita articoli` answers: is the article currently uncovered now?
- `planning candidates` answers: after considering active incoming production, do we still need new production attention?

This means:

- `criticita` remains useful as immediate shortage signal
- `planning candidates` becomes a more planning-oriented signal

## Explicit V1 Tradeoffs

Accepted limitations:

- no temporal credibility check on active productions
- no distinction between reliable and unreliable incoming supply
- no demand slicing by due date
- no stock policy reasoning
- no aggregation-policy refinement

These are future expansions, not blockers for V1.

## Future Expansion Path

The design intentionally leaves room for:

- stock-driven candidates
- planning horizon
- incoming supply within horizon
- order-line or non-aggregable candidates
- aggregation policy by family or article
- scoring and prioritization

V1 must not block these evolutions, but it must not implement them prematurely either.
