# DL-ARCH-V2-027 - Planning Candidates Aggregation V2

## Status
Accepted

## Date
2026-04-10

## Context

`Planning Candidates` V1 is already active in the system as a customer-driven projection aggregated by `article`.

Its current V1 logic assumes a single planning behavior for all articles:

- aggregate open demand by `article`
- aggregate incoming supply by `article`
- compute:

```text
future_availability_qty = availability_qty + incoming_supply_qty
```

- create one candidate per `article_code` only when:

```text
future_availability_qty < 0
```

This works for articles whose planning behavior is stock/code-oriented.

It is not sufficient for cases where production must be reasoned per customer order line and not by global article aggregation.

The project now already provides:

- family-level planning policy defaults
- article-level overrides
- effective planning policy values in Core `articoli`
- order-line identity in `customer_order_lines`
- production references to customer order number and line

The system therefore needs a formal rule for switching planning behavior.

## Decision

`Planning Candidates` V2 must support two explicit planning modes:

- `by_article`
- `by_customer_order_line`

The active mode is selected through:

- `effective_aggrega_codice_in_produzione`

Resolution rule:

- `true` -> `planning_mode = by_article`
- `false` -> `planning_mode = by_customer_order_line`

This policy is not a UI hint.
It is a Core planning rule.

## Planning Mode 1 - by_article

This mode preserves the current V1 behavior.

Identity:

- `article_code`

Main quantities:

- `availability_qty`
- `customer_open_demand_qty`
- `incoming_supply_qty`
- `future_availability_qty`

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

This mode is used when the article can be planned through aggregated stock/code reasoning.

## Planning Mode 2 - by_customer_order_line

This mode is used when the article must not be planned through article-level aggregation.

Identity:

- `numero_ordine_cliente`
- `riga_ordine_cliente`

There may therefore be multiple planning candidates for the same `article_code`.

### Demand

The relevant demand is the specific open quantity of the order line:

```text
line_open_demand_qty = max(ordered_qty - set_aside_qty - fulfilled_qty, 0)
```

### Availability

In this mode current generic free stock is intentionally ignored.

Operational rule:

```text
availability_qty = 0
```

Reason:

- the planning question is not "is the article available in general?"
- it is "is this specific order line already covered by explicitly linked production?"

### Incoming Supply

Incoming supply is not aggregated by article.

It is computed only from productions linked to the same customer order line.

Matching keys:

- candidate side:
  - `numero_ordine_cliente`
  - `riga_ordine_cliente`
- production side:
  - `riferimento_numero_ordine_cliente`
  - `riferimento_riga_ordine_cliente`

Completed productions must not contribute to planning supply, including completions derived from override logic such as `forza_completata`.

Historical productions may be used only when needed for correctness, and must be filtered conservatively if performance requires it.

### Coverage Metric

This mode must not reuse the article-level meaning of `future_availability_qty` ambiguously.

The canonical metric is:

```text
line_future_coverage_qty = linked_incoming_supply_qty - line_open_demand_qty
```

Candidate rule:

```text
line_future_coverage_qty < 0
```

Minimum shortage:

```text
required_qty_minimum = abs(line_future_coverage_qty)
```

## Output Contract

`Planning Candidates` must expose the planning mode explicitly.

Required field:

- `planning_mode`

Allowed values:

- `by_article`
- `by_customer_order_line`

This allows UI and future downstream logic to understand which rule produced the candidate.

## Architectural Consequences

This decision formalizes that `Planning Candidates` is no longer a single global aggregation behavior.

It becomes a planning projection with:

- one aggregated mode by `article`
- one linked mode by `customer_order_line`

The choice between the two is driven by effective planning policy, not by ad-hoc branching in the UI.

## Consequences

Positive:

- planning behavior becomes aligned with real operational differences between item families and specific article exceptions
- family defaults remain useful without forcing category explosion
- article-level override remains the correct mechanism for isolated exceptions
- future aggregation logic has a stable place in the model

Tradeoffs:

- Core planning logic becomes bifurcated and more explicit
- UI may need to handle mixed candidate shapes
- downstream sorting/filtering logic must understand `planning_mode`

## Out of Scope

This decision does not yet introduce:

- stock-driven candidates
- planning horizon
- ETA-based reasoning
- scoring / ranking
- lot sizing
- advanced aggregation policies beyond the current boolean mode switch

## Follow-up Direction

Natural follow-up work after this DL:

- Core evolution of `Planning Candidates` to support both planning modes
- UI evolution of the planning surface to represent both candidate shapes correctly
- later refinement of the planning policy model beyond the initial boolean switch
