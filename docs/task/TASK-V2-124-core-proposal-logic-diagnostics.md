# TASK-V2-124 - Core proposal logic diagnostics

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-036.md`

## Goal

Esporre nel Core/API di `Production Proposals` la diagnostica locale necessaria a capire quale logica e stata richiesta, quale logica e stata effettivamente usata e perche e avvenuto un eventuale fallback.

## Context

Con `proposal_target_pieces_v1` e `proposal_full_bar_v1`, il solo valore finale di `proposed_qty` non basta piu a capire il comportamento del sistema. Serve un contratto esplicito per distinguere:

- logica configurata sull'articolo
- logica effettivamente applicata alla riga workspace
- motivo del fallback quando la logica richiesta non e applicabile

## Scope

- aggiungere ai workspace row:
  - `requested_proposal_logic_key`
  - `effective_proposal_logic_key`
  - `proposal_fallback_reason`
- valorizzare i nuovi campi nel path di generazione workspace
- rendere deterministico il vocabolario iniziale di `proposal_fallback_reason`
- aggiungere test backend mirati sui casi di fallback della `proposal_full_bar_v1`

## Out of Scope

- redesign della UI proposal
- warning canonici nel modulo `Warnings`
- nuovi fallback reason oltre il vocabolario iniziale

## Constraints

- `requested_proposal_logic_key` riflette la configurazione articolo
- `effective_proposal_logic_key` riflette la logica realmente usata
- `proposal_fallback_reason` e `null` quando non c'e fallback
- la diagnostica e locale a `Production Proposals`, non va promossa a warning globale

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 09 - Warning canonico separato dal modulo che lo consuma`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La diagnostica viene valorizzata nel normale flusso di generazione del workspace proposal.

## Acceptance Criteria

- ogni workspace row espone `requested_proposal_logic_key`
- ogni workspace row espone `effective_proposal_logic_key`
- i fallback da `proposal_full_bar_v1` valorizzano `proposal_fallback_reason`
- il vocabolario iniziale include almeno:
  - `missing_raw_bar_length`
  - `invalid_usable_mm_per_piece`
  - `pieces_per_bar_le_zero`
  - `capacity_overflow`
  - `customer_undercoverage`
- i test backend coprono almeno un fallback per ciascuna categoria rilevante

## Deliverables

- read model / schema API proposal aggiornati
- path Core di generazione workspace aggiornato
- test backend mirati

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd backend
pip install -e .[dev]
```

## Verification Commands

```bash
python -m pytest V2/backend/tests/core/test_core_production_proposals.py V2/backend/tests/core/test_core_proposal_full_bar_v1.py -q
```

Atteso: exit code `0`.

## Implementation Notes

- la riga proposal deve poter mostrare sia il requested sia l'effective logic key
- il fallback reason va pensato come dato stabile di audit locale, non come messaggio UI free-form

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

## Implementation Log

### Migrazione DB

- `alembic/versions/20260415_029_proposal_logic_diagnostics.py` — aggiunge 3 colonne nullable VARCHAR(64) a `core_proposal_workspace_rows`: `requested_proposal_logic_key`, `effective_proposal_logic_key`, `proposal_fallback_reason`.

### ORM

- `core/production_proposals/models.py` — `CoreProposalWorkspaceRow` esteso con i 3 nuovi campi mapped.

### Read model

- `core/production_proposals/read_models.py` — `ProposalWorkspaceRowItem` esteso con i 3 nuovi campi opzionali (`str | None = None`).

### Logic

- `core/production_proposals/logic.py` — `FullBarResult` esteso con `fallback_reason: str | None = None`; `compute_full_bar_qty` chiama `_fallback(reason)` con codice vocabolario per ciascuna guardia di fallback.

### Queries

- `core/production_proposals/queries.py`:
  - `_resolve_full_bar_proposed_qty` restituisce 4-tuple `(Decimal, dict, bool, str | None)` (aggiunto `fallback_reason`).
  - `_workspace_row_from_candidate` spacchetta il 4-tuple, calcola `effective_logic_key`, popola i 3 nuovi campi nel costruttore `CoreProposalWorkspaceRow`.
  - `_workspace_row_to_item` passa i 3 campi diagnostici da ORM a `ProposalWorkspaceRowItem`.

### Test

- `tests/core/test_core_production_proposals.py` — 3 nuovi test: logica non-bar (nessun fallback), full-bar fallback `missing_raw_bar_length`, full-bar successo senza fallback.

### Verifica

```
85 passed
```
