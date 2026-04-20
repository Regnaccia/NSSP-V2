# TASK-V2-154 - UI planning right column `Proposal` layout refinement

## Status
Completed

## Date
2026-04-20

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/task/TASK-V2-152-ui-planning-right-column-proposal-v1.md`

## Goal

Riallineare il layout della colonna destra `Proposal` a una lettura piu operativa e meno tecnica.

## Scope

- sostituire il blocco dominante `Quantita proposta + misura` con:
  - `quantita + note`
- mostrare `display_description` e `codice_immagine` subito dopo
- introdurre il blocco `Materiale + mm necessari`
- spostare `Logica proposal` sotto il contesto materiale
- unificare `Stato export` dentro `Warnings / Diagnostica locale`

## Out of Scope

- fix semantico di `proposal_status`
- override proposal
- batch editor

## Acceptance Criteria

- la colonna destra segue l'ordine blocchi aggiornato in spec
- la quantita proposta e leggibile insieme alla nota export
- descrizione e immagine/codice immagine compaiono prima della logica
- il vecchio blocco `Stato export` separato non e piu dominante

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-20

TypeScript pulito.

**`PannelloProposal`** — nuovo ordine blocchi (TASK-V2-154):
1. **Quantità + Note**: `proposal_qty_computed` grande + misura + `note_fragment` (bold, lot description) + `proposal_reason_summary` (secondario, compatto)
2. **Articolo**: griglia 2-col — `display_description` + `codice_immagine` da `ArticoloDetail`
3. **Materiale**: griglia 2-col — `materiale_grezzo_codice` + `raw_bar_length_mm` da `ArticoloDetail` (entrambi `—` se non configurati)
4. **Logica proposal**: invariata (spostata dopo il contesto materiale)
5. **Warnings / Diagnostica (unificato)**: `proposal_status` badge (se non `Valid for export`) + `proposal_local_warnings` — blocco condizionale (nascosto se tutto OK)

**Blocco "Stato export" separato rimosso**: assorbito nel blocco unificato Warnings/Diagnostica.

**Fonte campi articolo**: `ArticoloDetail` già presente nel workspace (`selectedDetail`); passato come prop `detail: ArticoloDetail | null` a `PannelloProposal`. I campi `codice_immagine`, `materiale_grezzo_codice`, `raw_bar_length_mm` sono tutti su `ArticoloDetail` (`api.ts` line 138, 134, 191).
