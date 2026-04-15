# TASK-V2-121 - Core proposal full bar v1 logic

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-035.md`

## Goal

Implementare la seconda logica proposal V1 `proposal_full_bar_v1`, con calcolo a barre intere, `note_fragment = "BAR xN"` e fallback obbligatorio a `proposal_target_pieces_v1` quando la logica non e applicabile o non e compatibile con la capienza.

## Context

La logica `proposal_target_pieces_v1` resta la baseline/fallback. `proposal_full_bar_v1` aggiunge una proposta arrotondata a barre intere, usando lunghezza barra, materiale occorrente, scarto e vincolo di capienza.

## Scope

- aggiungere `proposal_full_bar_v1` al registry proposal
- implementare la formula:
  - `usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto`
  - `pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)`
  - `bars_required = ceil(required_qty_total / pieces_per_bar)`
  - `proposed_qty = bars_required * pieces_per_bar`
- generare `note_fragment = "BAR xN"`
- applicare il controllo:
  - `availability_qty + proposed_qty <= capacity_effective_qty`
- applicare fallback a `proposal_target_pieces_v1` nei casi fissati in spec
- aggiornare test Core proposal e config catalog

## Out of Scope

- nuovi warning cross-module dedicati al fallback
- UI preview export
- writer `xlsx`
- logiche barra piu ricche con kerf o sfrido fisso per barra

## Constraints

- `proposal_full_bar_v1` non deve mai proporre meno di `customer_shortage_qty`
- in V1 non e ammesso overflow di capienza
- config mancante o non valida non blocca la proposta: fa fallback a pezzi
- `note_fragment` della logica barra e solo `BAR xN`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` Si
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 07 - Strategy/config esplicita per logiche di dominio`
- `Pattern 13 - Prima logica minima e fallback chiaro`

## Refresh / Sync Behavior

- `La logica viene applicata durante la generazione del ProposalWorkspace`

Non introduce:

- nuovi refresh semantici
- auto-generation proposal da planning

## Acceptance Criteria

- `proposal_full_bar_v1` e registrata e selezionabile
- la formula usa `raw_bar_length_mm / (occorrente + scarto)` con `floor`
- `bars_required = ceil(required_qty_total / pieces_per_bar)`
- `note_fragment = BAR xN`
- fallback a `proposal_target_pieces_v1` per:
  - config mancante
  - `usable_mm_per_piece <= 0`
  - `pieces_per_bar <= 0`
  - overflow capacity
  - rischio di sotto-copertura cliente
- i test Core coprono i casi obbligatori

## Deliverables

- registry/config logic proposal aggiornato
- implementazione Core di `proposal_full_bar_v1`
- test backend mirati aggiornati

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd backend
pip install -e .[dev]
```

## Verification Commands

```bash
python -m pytest V2/backend/tests/core/test_core_production_proposals.py V2/backend/tests/core/test_core_proposal_logic_config.py -q
```

Atteso: exit code `0`.

## Implementation Notes

- il check capienza va fatto su:
  - `availability_qty + proposed_qty`
  - confrontato con `capacity_effective_qty`
- se `capacity_effective_qty` non consente la proposta a barre, in V1 si fa fallback a pezzi anziche blocco o overflow
- nessun messaggio di warning dedicato e richiesto in questo slice

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Implementata la logica `proposal_full_bar_v1` con formula barre intere, note fragment `BAR xN` e fallback a pezzi.

**`core/production_proposals/logic.py`**:
- `FullBarResult` dataclass (frozen): `proposed_qty`, `bars_required: int | None`, `used_fallback: bool`
- `compute_full_bar_qty(required_qty_total, customer_shortage_qty, availability_qty, capacity_effective_qty, raw_bar_length_mm, occorrente, scarto) -> FullBarResult`
  - Formula: `usable_mm = occorrente + (scarto or 0)`, `pieces_per_bar = floor(bar/usable_mm)`, `bars_required = ceil(required/pieces_per_bar)`, `proposed = bars_required * pieces_per_bar`
  - Fallback obbligatorio per: config mancante, usable<=0, pieces_per_bar<=0, overflow capienza, sotto-copertura cliente
- `compute_note_fragment` aggiornato: per `proposal_full_bar_v1` restituisce `"BAR x{N}"` se `_bars_required` e nel params_snapshot, altrimenti `None`

**`core/production_proposals/queries.py`**:
- Import `compute_full_bar_qty`, `compute_note_fragment`
- `_resolve_full_bar_proposed_qty`: carica `raw_bar_length_mm` da `CoreArticoloConfig`, `occorrente/scarto` da `SyncArticolo`, `capacity_effective_qty` da `list_stock_metrics_v1`; chiama `compute_full_bar_qty`; se non fallback, arricchisce `params_snapshot` con `_bars_required`
- `_workspace_row_from_candidate`: intercetta `logic_key == "proposal_full_bar_v1"` e chiama `_resolve_full_bar_proposed_qty` anziche `compute_proposed_qty`
- `_workspace_row_to_item`: `note_preview` ora usa `compute_note_fragment(row.proposal_logic_key, params_snapshot)` anziche stringa vuota

**`tests/core/test_core_proposal_full_bar_v1.py`** (nuovo):
- 18 test: formula base, con scarto, fit esatto, floor pz/barra, note fragment con/senza bars_required, tutti i casi di fallback obbligatori

**`tests/core/test_core_proposal_logic_config.py`**:
- 3 nuovi test: `test_full_bar_v1_in_known_logics`, `test_compute_note_fragment_full_bar_with_bars`, `test_compute_note_fragment_full_bar_fallback_is_none`

**Verification**: 44/44 test passati.

## Completed At

2026-04-15

## Completed By

Claude Code
