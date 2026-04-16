# TASK-V2-131 - Core proposal multi bar v1 logic

## Status
Completed

## Date
2026-04-16

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-038.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`

## Goal

Introdurre una nuova logica proposal basata sulla stessa policy di `proposal_full_bar_v2_capacity_floor`, ma con resa per barra moltiplicata da un `multiplo` articolo-specifico.

## Context

Esistono articoli in cui una barra di materiale non produce solo:

- `floor(raw_bar_length_mm / usable_mm_per_piece)` pezzi

ma un multiplo fisso di quel numero.

Esempio:

- `raw_bar_length_mm = 3900`
- `usable_mm_per_piece = 43`
- `multiplo = 10`

Formula:

```text
base_pieces_per_bar = floor(3900 / 43) = 90
pieces_per_bar = base_pieces_per_bar * 10 = 900
```

La policy di capienza richiesta e la stessa della logica:

- `proposal_full_bar_v2_capacity_floor`

quindi:

- prova `ceil`
- se `ceil` sfora, prova `floor`
- se `floor` non e ammissibile, fallback a pezzi

## Scope

- introdurre una nuova logic key dedicata, separata dalle logiche full-bar esistenti
- aggiungere il nuovo parametro articolo-specifico obbligatorio:
  - `proposal_logic_article_params.bar_multiple`
- implementare il calcolo:
  - `base_pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)`
  - `pieces_per_bar = base_pieces_per_bar * bar_multiple`
- riusare la stessa policy `capacity_floor` della `proposal_full_bar_v2_capacity_floor`
- aggiungere test backend mirati

## Out of Scope

- redesign UI proposal
- modifica semantica delle logiche full-bar esistenti
- introduzione di nuove policy di overflow diverse da `capacity_floor`

## Constraints

Nuova logica attesa:

- nome suggerito:
  - `proposal_multi_bar_v1_capacity_floor`

Nuovo dato richiesto:

- `proposal_logic_article_params.bar_multiple`
  - intero positivo
  - articolo-specifico
  - obbligatorio solo quando la logic key selezionata e `proposal_multi_bar_v1_capacity_floor`

Formule:

```text
usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto
base_pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
pieces_per_bar = base_pieces_per_bar * bar_multiple
bars_ceil = ceil(required_qty_total / pieces_per_bar)
qty_ceil = bars_ceil * pieces_per_bar
bars_floor = floor(required_qty_total / pieces_per_bar)
qty_floor = bars_floor * pieces_per_bar
```

Guardrail:

- `bar_multiple > 0`
- se `base_pieces_per_bar <= 0`, fallback a pezzi
- se `pieces_per_bar <= 0`, fallback a pezzi
- `floor` e ammesso solo se:
  - `bars_floor > 0`
  - `availability_qty + qty_floor <= capacity_effective_qty`
  - `qty_floor >= customer_shortage_qty` quando esiste componente customer

Se uno dei prerequisiti manca o non e valido:

- fallback a `proposal_target_pieces_v1`

Diagnostica locale attesa:

- se la logic key selezionata e `proposal_multi_bar_v1_capacity_floor`
- e `proposal_logic_article_params.bar_multiple` manca o non e valido
- il caso va modellato come diagnostica locale proposal, non come warning canonico globale

Fallback reason iniziale atteso:

- `missing_bar_multiple`

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
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 05 - Configurazione articolo + valore effettivo/contratto Core`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La nuova logica si applica nel normale path di generazione del workspace proposal.

## Acceptance Criteria

- la nuova logica e registrata e selezionabile
- il nuovo parametro `proposal_logic_article_params.bar_multiple` e letto dal path Core corretto
- `pieces_per_bar` usa il moltiplicatore articolo-specifico
- se `qty_ceil` entra in capienza, viene usata
- se `qty_ceil` sfora e `qty_floor` e ammissibile, viene usata `qty_floor`
- se `qty_floor` non e ammissibile, fallback a `proposal_target_pieces_v1`
- i test backend coprono almeno:
  - esempio `3900 / 43 * 10 = 900`
  - caso `ceil` ammesso
  - caso `ceil` overflow + `floor` ammesso
  - caso fallback a pezzi
  - caso `missing_bar_multiple` con fallback reason locale coerente

## Deliverables

- registry proposal aggiornato
- implementazione Core della nuova logica
- validazione del nuovo parametro `bar_multiple` nel contratto logica articolo-specifica
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

## Implementation Log

### `core/production_proposals/config.py`

Aggiunta `"proposal_multi_bar_v1_capacity_floor"` a `KNOWN_PROPOSAL_LOGICS` e `_DEFAULT_PARAMS_BY_KEY`.

### `core/production_proposals/logic.py`

- `_FULL_BAR_LOGIC_KEYS` esteso con `"proposal_multi_bar_v1_capacity_floor"`
- Nuova funzione `compute_multi_bar_qty_v1_capacity_floor(...)`:

  Algoritmo identico a `compute_full_bar_qty_v2_capacity_floor` ma con:
  ```
  base_pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
  pieces_per_bar      = base_pieces_per_bar * bar_multiple
  ```
  Pre-guardie aggiuntive:
  - `missing_bar_multiple` — `bar_multiple` è None o <= 0
  - `pieces_per_bar_le_zero` — `base_pieces_per_bar <= 0`

  Policy capacity: stessa di v2 (ceil → floor → fallback).

### `core/production_proposals/queries.py`

- Import aggiunto: `compute_multi_bar_qty_v1_capacity_floor`
- `_resolve_full_bar_proposed_qty` esteso: quando `logic_key == "proposal_multi_bar_v1_capacity_floor"`, legge `bar_multiple` da `params_snapshot["bar_multiple"]` e chiama `compute_multi_bar_qty_v1_capacity_floor`
- `_workspace_row_from_candidate`: condizione di dispatch estesa con `"proposal_multi_bar_v1_capacity_floor"`

  `bar_multiple` viene da `proposal_logic_article_params` articolo-specifici, uniti nel `params_snapshot` tramite `merge_logic_params`.

### Test — `tests/core/test_core_proposal_full_bar_v1.py`

10 nuovi test per `compute_multi_bar_qty_v1_capacity_floor`:

| Test | Scenario |
|---|---|
| `test_multi_bar_in_known_logics` | registry |
| `test_multi_bar_formula_esempio_task` | 3900/43×10=900 (esempio task) |
| `test_multi_bar_ceil_admitted` | ceil dentro capienza |
| `test_multi_bar_ceil_overflow_floor_admitted` | ceil overflow + floor ammesso |
| `test_multi_bar_fallback_a_pezzi_capacity_overflow` | entrambi sforano → capacity_overflow |
| `test_multi_bar_missing_bar_multiple_none` | bar_multiple=None → missing_bar_multiple |
| `test_multi_bar_missing_bar_multiple_zero` | bar_multiple=0 → missing_bar_multiple |
| `test_multi_bar_note_fragment` | BAR xN |
| `test_multi_bar_note_fragment_fallback` | None se fallback |
| `test_multi_bar_pre_guard_missing_raw_bar_length` | pre-guardia raw_bar_length_mm=None |

**Esito:** `59 passed` in 1.47s.
