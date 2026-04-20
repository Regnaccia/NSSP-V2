# TASK-V2-151 - Core/API contracts per la colonna destra `Proposal`

## Status
Completed

## Date
2026-04-20

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PLANNING_CANDIDATES_SPEC_V1_1.md`

## Goal

Definire ed esporre il contratto Core/API minimo necessario alla scheda destra `Proposal` del workspace planning.

## Scope

- contratti read-only per:
  - `proposal_status`
  - `proposal_qty_computed`
  - `requested_proposal_logic_key`
  - `effective_proposal_logic_key`
  - `proposal_fallback_reason`
  - `proposal_reason_summary`
  - `proposal_local_warnings`
  - `note_fragment`
- allineamento con i campi planning gia presenti:
  - `required_qty_eventual`
  - `release_qty_now_max`

## Out of Scope

- override proposal
- editing logica manuale
- export diretto dal pannello
- batch editor multi-riga

## Acceptance Criteria

- esiste un contratto API leggibile per alimentare la colonna destra `Proposal`
- `proposal_status` usa il vocabolario:
  - `Error`
  - `Need review`
  - `Valid for export`
- il contratto distingue campi proposal locali da warning planning canonici

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-20

126 test passati. TypeScript pulito.

**Read model** (`core/planning_candidates/read_models.py`):
- Aggiunti 8 campi proposal preview a `PlanningCandidateItem`:
  - `proposal_status: Literal["Error", "Need review", "Valid for export"] | None`
  - `proposal_qty_computed: Decimal | None`
  - `requested_proposal_logic_key: str | None`
  - `effective_proposal_logic_key: str | None`
  - `proposal_fallback_reason: str | None`
  - `proposal_reason_summary: str | None`
  - `proposal_local_warnings: list[str]`
  - `note_fragment: str | None`

**Core** (`core/planning_candidates/queries.py`):
- `_ArticoloInfo` estesa con `proposal_logic_key` e `proposal_logic_article_params`
  (popolati dal join esistente con `CoreArticoloConfig` in `_load_articoli_info`).
- Aggiunti helper batch-load:
  - `_load_sync_articolo_proposal_data` — 1 query per occorrente/scarto/raw_material_code
  - `_load_raw_material_bar_lengths` — 1 query per raw_bar_length_mm dai materiali grezzi
- Aggiunto `_compute_proposal_preview_v1`:
  - logica `target_pieces`: triviale, nessuna query extra
  - logica full-bar/multi-bar: usa dati pre-caricati; fallback a target_pieces se mancano
  - `capacity_effective_qty` ricostruita da `stock_effective_qty + capacity_headroom_now_qty`
  - `proposal_status` derivato: `Error` se riga ordine mancante (blocco export XLSX), `Need review` se fallback o local_warning, `Valid for export` altrimenti
  - `proposal_reason_summary` leggibile con label logica, note_fragment e qty
- Injection in `list_planning_candidates_v1`: 2 query batch aggiuntive pre-loop + `model_copy` esteso
- Import lazy di `production_proposals.config` e `production_proposals.logic` per evitare circular import

**Frontend** (`types/api.ts`):
- Aggiunti 8 campi proposal preview a `PlanningCandidateItem`
