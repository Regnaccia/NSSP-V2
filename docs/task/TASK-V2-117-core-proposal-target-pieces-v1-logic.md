# TASK-V2-117 - Core proposal target pieces v1 logic

## Status
Completed

## Date
2026-04-14

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-033.md`
- `docs/decisions/ARCH/DL-ARCH-V2-034.md`

## Goal

Introdurre la prima logica proposal V1 `proposal_target_pieces_v1`, che proponga esattamente i pezzi mancanti al target e non produca alcun contributo testuale alla `note`.

## Context

La spec proposal ora fissa una prima logica volutamente minima:

- `proposed_qty = required_qty_total`
- `note_fragment = null`

Questa logica deve diventare il comportamento reale del Core proposal/workspace e il fallback di base per scenari futuri piu ricchi.

## Scope

- introdurre nel Core la logica `proposal_target_pieces_v1`
- riallineare il registry/config proposal al nuovo `logic_key`
- applicare la logica alla generazione delle righe workspace proposal
- esporre in modo esplicito l'assenza di `note_fragment` quando la logica non produce testo
- mantenere il fallback tecnico a `required_qty_minimum` solo per slice legacy che non valorizzano `required_qty_total`
- aggiornare i test Core proposal relativi alla qty proposta e al `logic_key`

## Out of Scope

- preview export EasyJob in tabella proposal
- writer `xlsx`
- logiche proposal piu ricche o produzione-aware
- formattazione finale della `note` export
- redesign UI delle proposal

## Constraints

- il naming canonico V1 e `proposal_target_pieces_v1`
- la logica deve restare deterministicamente spiegabile
- `note_fragment` deve risultare `null`, non stringa vuota o placeholder
- il fallback a `required_qty_minimum` e solo compatibilita tecnica, non la semantica primaria della logica

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

- il Core riconosce `proposal_target_pieces_v1` come prima logica proposal V1
- la qty proposta e `required_qty_total`, con fallback tecnico a `required_qty_minimum` solo per candidate legacy
- il `proposal_logic_key` salvato nelle righe workspace usa il nuovo nome canonico
- l'output testuale della logica verso `note_fragment` e `null`
- i test Core proposal coprono la nuova semantica

## Deliverables

- registry/config logic proposal aggiornata
- implementazione Core della logica `proposal_target_pieces_v1`
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

- se esiste gia una logica legacy con nome diverso, valutarne il mantenimento come alias compatibile solo se necessario; il contratto canonico deve comunque esporre `proposal_target_pieces_v1`
- evitare di introdurre testo sintetico in `note_fragment`: il primo frammento logica verra aggiunto in task successivi
- tenere separata la semantica `base_qty` dalla futura composizione della `note` export

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Introdotta la logica canonale V1 `proposal_target_pieces_v1` nel Core production proposals.

**`core/production_proposals/config.py`**:
- `KNOWN_PROPOSAL_LOGICS` aggiornato: `proposal_target_pieces_v1` (primo) + `proposal_required_qty_total_v1` (alias legacy compatibile).
- `_DEFAULT_LOGIC_KEY` aggiornato a `"proposal_target_pieces_v1"`.
- `_DEFAULT_PARAMS_BY_KEY` include entrambe le chiavi con params vuoti.

**`core/production_proposals/logic.py`**:
- `compute_proposed_qty`: branch esteso per coprire sia `proposal_target_pieces_v1` che alias legacy — stessa semantica (`proposed_qty = required_qty_total`).
- `compute_note_fragment(logic_key, params_snapshot) -> str | None`: nuova funzione che restituisce `None` per entrambe le chiavi (V1 non produce frammento testuale).

**`tests/core/test_core_proposal_logic_config.py`**:
- `test_default_proposal_logic_config`: aggiornato — attende `proposal_target_pieces_v1` come default.
- `test_legacy_alias_still_known`: nuovo — verifica che l'alias legacy sia ancora in `KNOWN_PROPOSAL_LOGICS`.
- `test_set_and_get_proposal_logic_config`: aggiornato al nuovo nome canonico.
- `test_compute_proposed_qty_target_pieces_v1`: nuovo — verifica `proposed_qty = required_qty_total`.
- `test_compute_proposed_qty_legacy_alias`: nuovo — verifica compatibilità alias.
- `test_compute_note_fragment_is_none`: nuovo — verifica `note_fragment = None` per V1.
- `test_compute_note_fragment_legacy_alias_is_none`: nuovo.

**Verification**: 23 test passati (test_core_production_proposals + test_core_proposal_logic_config).

## Completed At

2026-04-15

## Completed By

Claude Code
