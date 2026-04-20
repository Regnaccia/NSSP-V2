# PRODUCTION_PROPOSALS_V1_REDUCED_SPEC

## Purpose

This document defines the first implementable slice of `Production Proposals` after the refactor that moved human triage back into `Planning Candidates`.

## V1 Goal

`Production Proposals V1` must:

- start only from explicitly selected planning candidates
- create a temporary server-side workspace
- freeze candidate snapshots into that workspace
- allow quantity override before export
- export the workspace as EasyJob-compatible `xlsx`
- persist only exported proposal snapshots
- reconcile exported snapshots through `ODE_REF`

## In Scope

- `POST /produzione/planning-candidates/generate-proposals-workspace`
- temporary `ProposalWorkspace`
- workspace row override
- workspace export `xlsx`
- workspace abandon
- exported proposal history
- reconcile on exported history
- global proposal logic config in `admin`
- article-specific proposal logic assignment and params

## Out of Scope

- persistent pre-export drafts
- persistent ready queue in planning
- auto-generation from all planning candidates
- auto-refresh / auto-cancel of proposals from planning drift
- scheduling
- scoring
- machine or resource assignment

## Boundary

### Planning Candidates

- remains the only live inbox of need
- supports selection
- triggers workspace generation
- is the target primary operator surface after the UX rebase
- is also the right upstream place to distinguish:
  - eventual need
  - release-now feasibility

### Production Proposals

- `workspace` mode: temporary execution-prep domain surface, expected to be consumed from a unified planning workspace
- `history` mode: exported persistent audit trail

Boundary rule:

- Planning answers `is there a need?`
- Proposals answers `what do we release/export?`

### Unified Planning Workspace Target

Post-rebase UX target:

- `Planning Candidates` becomes the primary unified operator workspace
- left column:
  - synthetic candidate inbox
- center column:
  - candidate detail
- right column:
  - proposal workspace panel

Rule:

- proposal preparation should no longer require a separate primary page transition
- exported history remains a separate surface

## Canonical Input

Workspace generation consumes selected planning candidates with at least:

- `source_candidate_id`
- `planning_mode`
- `article_code`
- `primary_driver`
- `required_qty_minimum`
- `required_qty_total`
- `customer_shortage_qty`
- `stock_replenishment_qty`
- `display_description`
- `requested_delivery_date`
- `requested_destination_display`
- `active_warning_codes`

Workspace rows must also expose proposal-local diagnostics:

- `requested_proposal_logic_key`
- `effective_proposal_logic_key`
- `proposal_fallback_reason`

Architectural rebase note:

- future proposal logic design must reason in policy axes
  - `proposal_base_qty_policy`
  - `proposal_lot_policy`
  - `proposal_capacity_policy`
  - `proposal_customer_guardrail_policy`
  - `proposal_note_policy`
- current `proposal_logic_key` remains the compatibility surface during transition

## Quantity Rule

Base quantity:

- `required_qty_total`

Compatibility fallback:

- `required_qty_minimum` if `required_qty_total` is absent in a legacy slice

First V1 logic:

- `proposal_target_pieces_v1`

Resolution rule:

```text
proposed_qty = base_qty
final_qty = override_qty if present, otherwise proposed_qty
```

First-logic semantics:

- it proposes exactly the missing target pieces
- `proposed_qty = required_qty_total`
- `note_fragment = null`

This first logic is also the default fallback logic for future richer proposal scenarios.

Conceptually, `proposal_target_pieces_v1` is the baseline bundle:

- base qty = `required_qty_total`
- lot policy = `pieces`
- capacity policy = `none`
- customer guardrail = `cover_customer_shortage`
- note policy = `none`

Second V1 logic:

- `proposal_full_bar_v1`

Second-logic semantics:

- it works on full raw-material bars
- it resolves the finished article raw-material code
- family flag `raw_bar_length_mm_enabled` only enables configurability of the bar-length field on raw-material families
- article field `raw_bar_length_mm` is read from the associated raw-material article
- formula:
  - `usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto`
  - `pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)`
  - `bars_required = ceil(required_qty_total / pieces_per_bar)`
  - `proposed_qty = bars_required * pieces_per_bar`
  - `note_fragment = "BAR xN"`
- capacity rule:
  - `availability_qty + proposed_qty <= capacity_effective_qty`

Mandatory fallback to `proposal_target_pieces_v1` if:

- the finished article does not resolve a valid `materiale_grezzo_codice`
- `raw_bar_length_mm` is missing on the associated raw-material article
- `usable_mm_per_piece <= 0`
- `pieces_per_bar <= 0`
- full-bar proposal would overflow `capacity_effective_qty`
- full-bar proposal would under-cover `customer_shortage_qty`

Guardrail:

- `proposal_full_bar_v1` must never return a proposal lower than `customer_shortage_qty`

Third proposal logic:

- `proposal_full_bar_v2_capacity_floor`

Third-logic semantics:

- same raw-material resolution model as `proposal_full_bar_v1`
- first try `ceil`
- if `ceil` would overflow capacity, try `floor`
- `floor` is allowed only if:
  - it stays within `capacity_effective_qty`
  - it remains `> 0`
  - it does not under-cover `customer_shortage_qty`
- otherwise fallback to `proposal_target_pieces_v1`

Formula:

- `pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)`
- `bars_ceil = ceil(required_qty_total / pieces_per_bar)`
- `qty_ceil = bars_ceil * pieces_per_bar`
- `bars_floor = floor(required_qty_total / pieces_per_bar)`
- `qty_floor = bars_floor * pieces_per_bar`

Note fragment:

- `BAR xN`, where `N` is the number of bars effectively used

Conceptually, `proposal_full_bar_v1` and `proposal_full_bar_v2_capacity_floor` are compatibility bundles over the same policy axes, not the long-term target model by themselves.

Proposal-local diagnostics:

- `requested_proposal_logic_key` is the logic configured on the article
- `effective_proposal_logic_key` is the logic actually used to compute `proposed_qty`
- `proposal_fallback_reason` explains why a richer requested logic fell back to a simpler one

Initial fallback reasons:

- `missing_raw_bar_length`
- `invalid_usable_mm_per_piece`
- `pieces_per_bar_le_zero`
- `capacity_overflow`
- `customer_undercoverage`

These diagnostics are local to `Production Proposals` and must not be modeled as canonical `Warnings`.

## Workspace Semantics

Workspace entity:

- `workspace_id`
- `status`:
  - `open`
  - `exported`
  - `abandoned`
- `created_at`
- `expires_at`
- `updated_at`

Key rule:

- once generated, the workspace is frozen
- later planning refreshes do not mutate workspace rows

## Export Boundary

Persistence starts at export time.

After export:

- an `xlsx` file is produced
- `ODE_REF` is assigned
- exported proposal snapshots are persisted
- workspace becomes `exported`

## EasyJob XLSX Mapping

V1 target columns:

- `cliente`
- `codice`
- `descrizione`
- `immagine`
- `misura`
- `quantità`
- `materiale`
- `mm_materiale`
- `ordine`
- `note`
- `user`

Mapping:

- `cliente`
  - `requested_destination_display` when the candidate contains customer demand
  - otherwise `MAGAZZINO`
- `codice`
  - `article_code`
- `descrizione`
  - `description_parts` serialized as Python-list literal
- `immagine`
  - article image code
- `misura`
  - article measure
- `quantità`
  - `final_qty`
- `materiale`
  - raw material article code
- `mm_materiale`
  - raw material required quantity
- `ordine`
  - `order_reference/line_reference`
  - mandatory for customer-driven rows
  - empty for stock-only rows
- `note`
  - deterministic business note + `ODE_REF`
- `user`
  - export operator username, optional

For `proposal_full_bar_v1`, the production-logic note fragment is:

- `BAR xN`

Blocking validation:

- if the row contains customer demand and `ordine` cannot be built because `line_reference` is missing, export fails

## Persistent History

Persistent exported snapshots keep:

- frozen proposal quantities
- warning context
- `ode_ref`
- `export_batch_id`
- reconcile status

Exported-history lifecycle:

- `exported`
- `reconciled`
- `cancelled` only for future audit use

## Warnings

Proposal/workspace may consume canonical warning codes from `Warnings`.

Relevant warning introduced by the full-bar domain:

- `MISSING_RAW_BAR_LENGTH`

Meaning:

- raw-material family requires `raw_bar_length_mm`
- raw-material article configuration is missing or invalid

The warning remains owned by `Warnings`; proposal logic does not own the warning lifecycle.

## Reconcile

Reconcile works only on exported history:

```text
exported snapshot
-> Easy execution
-> sync produzioni
-> match via ODE_REF
```

## UI

### Planning Candidates

- checkbox selection
- `Genera proposte`

### Production Proposals

If opened with `workspace_id`:

- show workspace rows as export preview
- allow override
- `Esporta`
- `Chiudi senza esportare`

If opened without `workspace_id`:

- show exported history
- allow reconcile

Workspace preview table should expose, as main columns:

- `cliente`
- `codice`
- `descrizione`
- `immagine`
- `misura`
- `quantità`
- `materiale`
- `mm_materiale`
- `ordine`
- `note`
- `user`
- `warnings`

UI rendering rule for `descrizione`:

- export keeps the Python-list literal
- UI renders the same underlying `description_parts` as a multiline field
- each item is displayed on its own visual line

## Final Principle

`Planning Candidates` detects and triages live need and becomes the primary operator workspace. `Production Proposals` survives as temporary frozen workspace domain + exported history. Only exported rows become persistent business history.
