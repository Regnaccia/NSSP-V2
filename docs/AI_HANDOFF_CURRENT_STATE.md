# ODE V2 - AI Handoff Current State

## Purpose

This document is the fastest entry point for another AI agent that must understand:

- what the software already does today
- which modules are real and usable
- which canonical facts already exist
- which logic is already implemented
- where the current boundaries are
- where the next reasoning should start

## What The Software Is Today

ODE V2 is a browser-based operational system built on top of Easy read-only data.

At the current stage it already supports:

- user access and surface routing
- customer/destination browsing
- article browsing with internal family classification
- family-level and article-level planning policy configuration
- production browsing
- canonical stock-related facts
- a real operational `Planning Candidates` surface with branching by planning mode
- a transversal `Warnings` module with first dedicated surface
- first stock-policy governance with dedicated `admin` page and explicit stock-enabled flag

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
- host transversal internal configuration

Current note:

- warning visibility is configured by `visible_to_areas`
- stock logic configuration has its own dedicated page
- `admin` has transversal visibility for governance

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
- stock policy metrics:
  - `monthly_stock_base_qty`
  - `capacity_calculated_qty`
  - `capacity_effective_qty`
  - `target_stock_qty`
  - `trigger_stock_qty`
  - `stock_strategy_key`
  - `stock_computed_at`

Planning policy UI already available:

- article override tri-state controls
- stock-enabled override:
  - `override_gestione_scorte_attiva`
- stock policy overrides:
  - `override_stock_months`
  - `override_stock_trigger_months`
  - `capacity_override_qty`
- read-only effective planning policy values
- read-only effective stock-enabled value:
  - `effective_gestione_scorte_attiva`
- explicit planning-mode wording in UI:
  - `by_article`
  - `by_customer_order_line`

### 4. Produzione - Catalogo Famiglie Articolo

Purpose:

- manage internal family catalog
- configure planning-policy defaults

Current note:

- family UI now also exposes stock-policy defaults:
  - `gestione_scorte_attiva`
  - `stock_months`
  - `stock_trigger_months`

### 5. Produzioni

Purpose:

- browse active and historical productions
- inspect computed production state
- use `forza_completata`

### 6. Produzione - Planning Candidates

Purpose:

- show customer-driven planning candidates
- answer whether a production need still exists after considering current availability and incoming supply
- support both:
  - `by_article`
  - `by_customer_order_line`

Current behavior:

- code search with normalization
- description search without normalization
- family filter
- toggle `solo_in_produzione` based on effective article policy
- refresh button wired to full semantic refresh of the article surface
- incoming supply excludes productions already completed, including `forza_completata`
- planning logic clamps stock with `stock_effective = max(stock_calculated, 0)`
- candidates expose explicit `reason_code` / `reason_text`
- by-customer-order-line rows expose `misura` and primary order-line description
- by-article rows already expose stock-driven breakdown:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `required_qty_total`
- planning now also exposes first temporal semantics:
  - `is_within_customer_horizon`
  - stock-driven cap on commitments within stock horizon

### 7. Produzione - Warnings

Purpose:

- expose canonical operational anomalies explicitly
- avoid forcing operators to infer anomalies only from secondary modules

Current behavior:

- dedicated `Warnings` surface exists
- first warning types are:
  - `NEGATIVE_STOCK`
  - `INVALID_STOCK_CAPACITY`
- config uses `visible_to_areas`
- operational users only see warnings matching their current area
- `admin` sees the transversal full list

### 8. Produzione - Criticita Articoli

Purpose:

- legacy first criticality surface based on `availability_qty < 0`

Current note:

- still available technically
- no longer the primary operational stream
- formally deprecated / legacy

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
- planning uses `stock_effective = max(stock_calculated, 0)` rather than raw negative stock

### Warnings

Status:

- Core slice implemented
- UI surface implemented

Current shape:

- canonical warning object
- first type `NEGATIVE_STOCK`
- warning identity is unique, not duplicated per reparto
- admin config exists and uses `visible_to_areas`

## Canonical Facts Already Available

### Inventory

Meaning:

- net physical stock per article

Source:

- `MAG_REALE`

### Commitments

Meaning:

- open operational demand still requiring coverage

Current sources:

- customer orders
- production

### Customer Set Aside

Meaning:

- quantity already set aside / boxed for customer
- still physically present in stock flow, but no longer free

### Availability

Meaning:

- currently free quantity after subtracting set-aside and commitments

Formula:

- `availability_qty = inventory_qty - customer_set_aside_qty - committed_qty`

Negative values are allowed and are meaningful.

## Planning Policy Model Already Available

### Family Defaults

Available at family level:

- `considera_in_produzione`
- `aggrega_codice_in_produzione`

### Article Overrides

Articles can hold nullable overrides for the same policy dimensions.

Rule:

- article override wins if set
- otherwise family default is used

### Effective Values

The Core `articoli` exposes:

- `effective_considera_in_produzione`
- `effective_aggrega_codice_in_produzione`
- `effective_gestione_scorte_attiva`
- `planning_mode`

These are the intended contracts for downstream consumers.

## Semantic Refresh Model

The most important semantic refresh already implemented is:

- `refresh_articoli()`

Current chain:

1. sync articoli
2. sync mag_reale
3. sync righe_ordine_cliente
4. sync produzioni_attive
5. rebuild inventory_positions
6. rebuild customer_set_aside
7. rebuild commitments
8. rebuild availability

This matters because UI views should not reconstruct dependency chains themselves.

## Important Data Rules Already Fixed

### Canonical vs Raw Article Code

There is an explicit distinction between:

- raw article key
- canonical article key

Canonical key is produced through `normalize_article_code`.

Rule:

- canonical key is used for cross-source facts, joins, logic, projections
- raw key is kept for source-facing or traceability needs
- direct raw/canonical mixed joins are not allowed

## What The Software Does Not Do Yet

Not implemented yet:

- warning badges in `articoli` and `Planning Candidates`
- production proposals
- production scheduling
- lot sizing / multiples
- machine/resource allocation
- safety stock logic beyond the first stock policy V1 slice
- advanced prioritization logic

## Current Open Tasks

Currently open in the active roadmap:

- no active task at the moment

Deferred in the active roadmap:

- `TASK-V2-079` warning badges in `articoli` and `Planning Candidates`

Operational note:

- `TASK-V2-073` has already completed a full `sync_mag_reale` re-bootstrap and downstream rebuild, restoring exact alignment with Easy for the current dataset
- the long-term architectural issue remains open in `docs/reviews/KNOWN_BUGS.md`

## What Is The Next Logical Reasoning Area

The immediate next reasoning area is deciding whether to open `Production Proposals` on top of the now-complete planning + stock slice, or to refine planning further before that module.

The next meaningful design area is:

- opening `Production Proposals`
- or explicitly deciding a further refinement step on planning before proposals

Explicitly deferred for now:

- warning badges in `articoli` and `Planning Candidates`

## How To Use The Existing Docs

Recommended reading order for another AI agent:

1. this file
2. [SYSTEM_OVERVIEW.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/SYSTEM_OVERVIEW.md#L1)
3. [UI_SURFACES_OVERVIEW.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/UI_SURFACES_OVERVIEW.md#L1)
4. [STATUS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/roadmap/STATUS.md#L1)
5. relevant DLs:
   - `DL-ARCH-V2-022`
   - `DL-ARCH-V2-023`
   - `DL-ARCH-V2-024`
   - `DL-ARCH-V2-025`
   - `DL-ARCH-V2-026`
   - `DL-ARCH-V2-027`
   - `DL-ARCH-V2-028`
   - `DL-ARCH-V2-029`
   - `DL-ARCH-V2-030`
   - `DL-ARCH-V2-031`
6. relevant specs in `docs/specs/`

## Practical Summary

If another AI agent must start reasoning today, the correct mental model is:

- ODE V2 already has solid canonical operational facts
- article detail is the main fact inspection surface
- Planning Candidates is the first real planning-oriented operational surface
- Warnings is the first transversal anomaly module
- semantic refresh and canonical article-key discipline are already established
- stock policy governance, enabled flag and invalid-capacity warning are already active
- first temporal horizons in planning are already active
- the next major evolution is deciding the opening of `Production Proposals`
