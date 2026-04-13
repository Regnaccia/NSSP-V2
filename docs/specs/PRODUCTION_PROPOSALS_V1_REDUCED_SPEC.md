# PRODUCTION_PROPOSALS_V1_REDUCED_SPEC

## Purpose

This document defines the first implementable slice of `Production Proposals`.

It is intentionally narrower than [PRODUCTION_PROPOSALS_SPEC_V1_0.md](PRODUCTION_PROPOSALS_SPEC_V1_0.md):

- proposal created from an already identified need
- no scoring in the first slice
- no scheduling
- no advanced effort model
- no drawing archive
- warnings kept separate from proposal lifecycle

Its purpose is to give a clean base for the first `DL` and the first implementation tasks.

## Context

The current V2 already provides:

- canonical quantitative facts:
  - `inventory`
  - `commitments`
  - `customer_set_aside`
  - `availability`
- `Planning Candidates`
- planning policy values resolved at article level
- production browsing and active production sync

What is still missing is the decision layer that transforms a detected need into an operational object with its own lifecycle.

## V1 Goal

`Production Proposals V1` must:

- take an already detected need from `Planning Candidates`
- turn it into a persistent operational proposal
- allow manual override
- support validation before export
- prepare robust reconciliation with Easy

It does not yet answer:

- scheduling
- machine assignment
- final prioritization via score
- effort optimization

## Scope

### In scope

- persistent `Production Proposal` object
- proposal created from `Planning Candidates`
- proposal quantity separated from override quantity
- minimal workflow:
  - `draft`
  - `validated`
  - `exported`
  - `reconciled`
- correlation key for Easy export
- negative stock handled through operational clamp
- warnings separated from proposal lifecycle

### Out of scope

- scoring
- scheduling
- resource assignment
- cycle-time logic
- drawing archive
- predictive logic
- advanced stock-policy logic
- warning workflow beyond simple exposure

## Upstream Dependency

V1 proposals are downstream of `Planning Candidates`.

Rule:

- `Planning Candidates` detects the need
- `Production Proposals` takes that need and turns it into an operational decision object

For V1:

- `required_qty` is derived from the upstream planning candidate
- proposal logic does not recompute the need from scratch

## Central Entity

### Production Proposal

`Production Proposal` is the main operational object.

It is not a transient view.

It is a persistent projection with:

- source need snapshot
- proposal decision
- override data
- workflow state

## Canonical Inputs

V1 uses names aligned with the current V2 model.

- `article_code`
- `required_qty`
- `stock_calculated`
- `commitments`

### required_qty

Derived from the upstream planning candidate.

For V1 it represents the minimum shortage or need already computed upstream.

### stock_calculated

Operationally useful but not always trustworthy for proposal logic when negative.

Therefore V1 introduces:

```text
stock_effective = max(stock_calculated, 0)
```

Rule:

- `stock_calculated` is preserved for audit/debug
- `stock_effective` is used for operational reasoning

## Proposal Decision Fields

Suggested V1 decision fields:

- `proposed_qty`
- `lot_applied`
- `multiple_applied`
- `stock_replenishment_qty`
- `policy_snapshot`

V1 principle:

- proposal logic starts from `required_qty`
- proposal may expand that quantity according to business policy
- final production quantity is still not a scheduling result

## Override

V1 must support explicit operator override.

Suggested fields:

- `override_qty`
- `override_reason`
- `override_by`
- `override_at`

Resolution rule:

```text
final_qty = override_qty if present, otherwise proposed_qty
```

## Workflow

V1 uses a minimal lifecycle:

- `draft`
- `validated`
- `exported`
- `reconciled`

Meaning:

- `draft`: proposal exists but is still editable
- `validated`: accepted for export pipeline
- `exported`: sent to Easy
- `reconciled`: matched back to the real Easy production

## Warning Separation

Warnings are not part of the proposal lifecycle.

V1 warning type in scope:

- `NEGATIVE_STOCK`

A proposal may expose warning presence, but:

- warning state is separate
- warning existence does not automatically create production

## Easy Integration

Easy IDs are not suitable as proposal identity.

V1 uses a correlation key:

```text
[ODE_REF=PP000123]
```

It is written into Easy notes and used for reconciliation:

```text
ODE export
-> Easy creates production
-> ODE sync productions
-> reconciliation by ODE_REF
```

Expected mapping:

- `proposal_id <-> easy_production_id`

## Output Shape

A first V1 proposal model should be minimal and explainable.

Suggested fields:

- `proposal_id`
- `article_code`
- `required_qty`
- `stock_calculated`
- `stock_effective`
- `proposed_qty`
- `override_qty`
- `final_qty`
- `workflow_status`
- `warning_count` or `has_warning`
- `ode_ref`
- `computed_at`

Optional descriptive fields for UI:

- `article_description`
- `family_name`

## Interaction With Existing Modules

### Planning Candidates

- upstream detector of need

### Warnings

- parallel anomaly module
- proposal may show warning badges, but does not own warning lifecycle

### Produzioni

- downstream reconciliation target after export

## Explicit V1 Tradeoffs

Accepted limitations:

- no scoring yet
- no operational effort model yet
- no scheduling semantics
- no predictive logic
- no advanced anomaly workflow

These are future expansions, not blockers for V1.

## Future Expansion Path

The design intentionally leaves room for:

- scoring
- effort estimation
- richer warning lifecycle
- export audit trail
- drawing archive integration
- historical or predictive proposal refinement

V1 must stay small enough to validate the proposal lifecycle before those expansions.
