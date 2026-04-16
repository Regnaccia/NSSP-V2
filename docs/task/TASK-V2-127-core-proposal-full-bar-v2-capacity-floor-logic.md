# TASK-V2-127 - Core proposal full bar v2 capacity floor logic

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-038.md`

## Goal

Introdurre la nuova logica `proposal_full_bar_v2_capacity_floor`, che mantiene la proposta a barre intere ma, se il `ceil` sfora la capienza, tenta un `floor` compatibile prima di ricadere a pezzi.

## Context

La `proposal_full_bar_v1` attuale usa una policy `strict_capacity` troppo rigida in alcuni casi:

- `qty_ceil` sfora la capienza
- `qty_floor` starebbe sotto capienza
- ma il sistema oggi ricade subito a `proposal_target_pieces_v1`

Serve una variante esplicita di logica che provi `floor` solo quando e ancora coerente con il vincolo cliente.

## Scope

- aggiungere `proposal_full_bar_v2_capacity_floor` al registry proposal
- implementare il calcolo `ceil -> floor -> fallback`
- mantenere la risoluzione barra sul materiale grezzo associato
- generare `note_fragment = BAR xN` con il numero di barre effettivamente usato
- aggiungere test backend mirati

## Out of Scope

- rimozione o modifica semantica di `proposal_full_bar_v1`
- redesign UI proposal
- nuove policy di overflow oltre `strict_capacity`

## Constraints

- prima si tenta `qty_ceil`
- `qty_floor` e ammesso solo se:
  - `bars_floor > 0`
  - resta sotto `capacity_effective_qty`
  - non sotto-copre `customer_shortage_qty`
- se `floor` non e ammissibile, il fallback resta `proposal_target_pieces_v1`
- la logica resta distinta e selezionabile separatamente dalla `v1`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` Si
- `Introduce configurazione che deve essere visibile in articoli?` Si
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 05 - Configurazione articolo + valore effettivo/contratto Core`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La nuova logica si applica al normale path di generazione del workspace proposal.

## Acceptance Criteria

- la nuova logica `proposal_full_bar_v2_capacity_floor` e registrata e selezionabile
- se `qty_ceil` entra in capienza, viene usata
- se `qty_ceil` sfora e `qty_floor` e ammissibile, viene usata `qty_floor`
- se `qty_floor` sotto-copre il cliente o non entra in capienza, fallback a `proposal_target_pieces_v1`
- i test backend coprono almeno:
  - caso `ceil` ammesso
  - caso `ceil` overflow + `floor` ammesso
  - caso `floor` non ammesso per sotto-copertura cliente
  - caso `floor` non ammesso e fallback a pezzi

## Deliverables

- registry proposal aggiornato
- implementazione Core della nuova logica
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

- la UI potra continuare a usare la diagnostica requested/effective logic gia prevista
- il numero di barre in nota deve riflettere il ramo davvero usato (`ceil` o `floor`)

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

## Implementation Log

### Registry

- `core/production_proposals/config.py` — aggiunto `"proposal_full_bar_v2_capacity_floor"` a `KNOWN_PROPOSAL_LOGICS` e `_DEFAULT_PARAMS_BY_KEY`.

### Logic

- `core/production_proposals/logic.py`:
  - Introdotto `_FULL_BAR_LOGIC_KEYS` (frozenset) per raggruppare le chiavi bar-rounding.
  - `compute_proposed_qty` e `compute_note_fragment` aggiornati per gestire entrambe le logiche tramite `_FULL_BAR_LOGIC_KEYS`.
  - Aggiunta `compute_full_bar_qty_v2_capacity_floor`: stesse pre-guardie di v1 (missing_raw_bar_length, invalid_usable_mm_per_piece, pieces_per_bar_le_zero, customer_undercoverage su ceil), poi:
    - Se `qty_ceil <= capacity` → usa ceil.
    - Se `qty_ceil > capacity` → tenta `bars_floor = floor(required / pieces_per_bar)`:
      - `bars_floor <= 0` → fallback `capacity_overflow`
      - `qty_floor < customer_shortage_qty` → fallback `customer_undercoverage`
      - `qty_floor > capacity` → fallback `capacity_overflow`
      - else → usa floor.

### Queries

- `core/production_proposals/queries.py`:
  - Importata `compute_full_bar_qty_v2_capacity_floor`.
  - `_resolve_full_bar_proposed_qty` aggiunta signature `logic_key: str = "proposal_full_bar_v1"`; dispatch interno su `_bar_fn` in base al `logic_key`.
  - `_workspace_row_from_candidate`: condizione estesa a `in ("proposal_full_bar_v1", "proposal_full_bar_v2_capacity_floor")`; passa `logic_key=requested_logic_key` a `_resolve_full_bar_proposed_qty`.

### Test

- `tests/core/test_core_proposal_full_bar_v1.py` — 9 nuovi test: registry, ceil ammesso, ceil overflow + floor ammesso, floor non ammesso per sotto-copertura cliente, floor non ammesso per overflow (divisione esatta), capacity None, note_fragment, note_fragment fallback, pre-guardia missing_raw_bar_length.

### Verifica

```
49 passed
```
