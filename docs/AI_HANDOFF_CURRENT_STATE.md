# ODE V2 - AI Handoff Current State

## Purpose

This document is the fastest entry point for another AI agent that must understand:

- what the software already does today
- which modules are real and usable
- which canonical facts already exist
- which logic is already implemented
- where the current boundaries are
- where the next reasoning should start

It is intentionally higher level than task files and more action-oriented than the generic system overview.

## What The Software Is Today

ODE V2 is a browser-based operational system built on top of Easy read-only data.

At the current stage it already supports:

- user access and surface routing
- customer/destination browsing
- article browsing with internal family classification
- family-level and article-level planning policy configuration
- production browsing
- canonical stock-related facts
- a first operational criticality view for articles
- a real operational `Planning Candidates` surface with branching by planning mode

It is not yet a scheduler, MRP engine, or production planner.

## Core Product Idea

The system reads raw operational data from Easy, mirrors it internally, then builds canonical Core facts and operational views on top of them.

Stable layer model:

- `sync`: technical mirrors of external sources
- `core`: computed facts, read models, domain logic
- `app`: API endpoints and orchestration
- `shared`: shared infrastructure and helpers

Easy is always read-only.

## Active Surfaces

### 1. Admin

Purpose:

- manage users, roles, active/inactive state

### 2. Logistica - Clienti / Destinazioni

Purpose:

- browse customers and destinations
- manage destination nickname

### 3. Produzione - Articoli

Purpose:

- browse article master data
- assign internal article family
- expose effective planning policy values from Core
- inspect canonical stock-related facts

Read-only ODE metrics already shown in article detail:

- `giacenza`
- `customer_set_aside`
- `committed_qty`
- `availability_qty`

Current search behavior:

- separate code search with dimensional normalization
- separate description search without normalization

This is currently the main validation surface for canonical facts.

Planning policy UI already available:

- article override tri-state controls
- read-only effective planning policy values
- explicit planning-mode wording in UI:
  - `by_article`
  - `by_customer_order_line`

### 4. Produzione - Catalogo Famiglie Articolo

Purpose:

- manage internal family catalog
- toggle `is_active`
- toggle `considera_in_produzione`
- toggle `aggrega_codice_in_produzione`

### 5. Produzioni

Purpose:

- browse active and historical productions
- inspect computed production state
- use `forza_completata`

### 6. Produzione - Criticita Articoli

Purpose:

- show the first operational logic built on canonical facts
- current V1 logic: article is critical if `availability_qty < 0`

Current behavior:

- family filter
- sorting by family and quantitative columns
- toggle `solo_in_produzione` with default active
- refresh button wired to full semantic refresh of the article surface
- only articles present and active in `articoli` can appear here

### 7. Produzione - Planning Candidates

Purpose:

- show customer-driven planning candidates
- answer whether a new production need still exists after considering current availability and incoming supply
- support both:
  - `by_article`
  - `by_customer_order_line`

Current behavior:

- code search with normalization
- description search without normalization
- family filter
- toggle `solo_in_produzione` based on `effective_considera_in_produzione`
- refresh button wired to full semantic refresh of the article surface
- incoming supply excludes productions already completed, including `forza_completata`
- contracts expose `planning_mode`
- UI distinguishes:
  - article-level candidates
  - customer-order-line candidates

## Core Projections Already Available

### Planning Candidates

Status:

- Core slice implemented
- UI surface implemented

Current shape:

- customer-driven only
- two modes:
  - `by_article`
  - `by_customer_order_line`
- `by_article` uses:
  - `availability_qty`
  - `incoming_supply_qty`
  - `future_availability_qty`
- `by_customer_order_line` uses:
  - `line_open_demand_qty`
  - `linked_incoming_supply_qty`
  - `line_future_coverage_qty`
- candidates exist only when the relevant coverage metric is negative
- incoming supply excludes productions effectively completed

## Canonical Facts Already Available

These are the most important building blocks already implemented.

### Inventory

Meaning:

- net physical stock per article

Formula:

- `on_hand_qty = sum(load_qty) - sum(unload_qty)`

Source:

- `MAG_REALE`

### Commitments

Meaning:

- open operational demand still requiring coverage

Current sources:

- customer orders
- production

Notes:

- customer commitments derive from order lines
- production commitments derive from active productions
- V1 production scope is intentionally limited

### Customer Set Aside

Meaning:

- quantity already set aside / boxed for customer
- still physically present in stock flow, but no longer free

Source:

- `DOC_QTAP` from customer order lines

### Availability

Meaning:

- currently free quantity after subtracting set-aside and commitments

Formula:

- `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`

Negative values are allowed and are meaningful.

## Planning Policy Model Already Available

The project now also has a first planning-policy model on top of articles and families.

### Family Defaults

Available at family level:

- `considera_in_produzione`
- `aggrega_codice_in_produzione`

These are no longer just local UI flags.
They are default planning policy values.

### Article Overrides

Articles can now hold nullable overrides for the same policy dimensions.

Rule:

- article override wins if set
- otherwise family default is used

### Effective Values

The Core `articoli` now exposes:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`
- `planning_mode`

These effective values are the intended contract for future consumers such as:

- `planning candidates`
- future criticality refinements
- future aggregation policy logic

## Current Domain Logic Already Implemented

### Article Criticality V1

Status:

- implemented and visible in UI

Current rule:

- critical if `availability_qty < 0`

Important architectural rule:

- logic lives as a domain function on top of canonical facts
- it is meant to be replaceable or refinable later

This is the first real business logic layer beyond mechanical calculation.

## Semantic Refresh Model

The most important semantic refresh already implemented is:

- `refresh_articoli()`

It encapsulates the full dependency chain for the article surface.

Current chain:

1. sync articoli
2. sync mag_reale
3. sync righe_ordine_cliente
4. sync produzioni_attive
5. rebuild inventory_positions
6. rebuild customer_set_aside
7. rebuild commitments
8. rebuild availability

This is important because UI views should not reconstruct dependency chains themselves.

The criticality view now correctly reuses this refresh.

## Important Data Rules Already Fixed

### Canonical vs Raw Article Code

This is a critical rule for future work.

There is now an explicit distinction between:

- raw article key
- canonical article key

Canonical key is produced through `normalize_article_code`.

Rule:

- canonical key is used for cross-source facts, joins, logic, projections
- raw key is kept for source-facing or traceability needs
- direct raw/canonical mixed joins are not allowed

This rule exists because a real bug already happened when canonical facts and raw article codes were joined incorrectly.

## What The Software Does Not Do Yet

Not implemented yet:

- planning proposals
- production scheduling
- lot sizing / multiples
- machine/resource allocation
- safety stock logic
- stock policy logic
- temporal planning slices
- advanced prioritization logic

Current system is therefore:

- already operational for browsing and first criticality detection
- not yet a planning engine

## Current Open Tasks

Currently open in the active roadmap:

- none in the current snapshot

Operational note:

- `TASK-V2-073` has already completed a full `sync_mag_reale` re-bootstrap and downstream rebuild, restoring exact alignment with Easy for the current dataset
- the long-term architectural issue remains open in `docs/reviews/KNOWN_BUGS.md`: `sync_mag_reale` still uses `append_only + no_delete_handling`

## What Is The Next Logical Reasoning Area

The next meaningful step is no longer infrastructure.

The next reasoning area is domain logic and the first real planning-oriented operational view:

- `Planning Candidates`
  - evolve beyond the current two-mode V2
  - add richer aggregation policy, filters, and later scoring/temporal logic

- richer criticality logic
- stock policy logic
- family-aware logic
- temporal planning logic

This is exactly where the new `docs/specs/` area becomes useful.

## How To Use The Existing Docs

Recommended reading order for another AI agent:

1. this file
2. [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
3. [guides/UI_SURFACES_OVERVIEW.md](guides/UI_SURFACES_OVERVIEW.md)
4. [roadmap/STATUS.md](roadmap/STATUS.md)
5. relevant DLs:
   - `DL-ARCH-V2-016`
   - `DL-ARCH-V2-017`
   - `DL-ARCH-V2-019`
   - `DL-ARCH-V2-021`
   - `DL-ARCH-V2-022`
   - `DL-ARCH-V2-023`
   - `DL-ARCH-V2-024`
6. relevant specs in `docs/specs/`

Task files should be read only when fine-grained implementation history matters.

## Practical Summary

If another AI agent must start reasoning today, the correct mental model is:

- ODE V2 already has solid canonical operational facts
- article detail is the main fact inspection surface
- article criticality is the first real domain logic surface
- Planning Candidates is now the first planning-oriented operational surface
- semantic refresh and canonical article-key discipline are already established
- the next major evolution is richer planning logic, not more raw sync scaffolding
