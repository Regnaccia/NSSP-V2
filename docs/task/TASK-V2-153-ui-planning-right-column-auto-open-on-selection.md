# TASK-V2-153 - UI planning right column auto-open on selection

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

Rendere la terza colonna del workspace planning immediatamente visibile e contestuale alla selezione del candidate.

## Scope

- selezione in colonna sinistra aggiorna direttamente:
  - colonna centrale
  - colonna destra
- stato placeholder della colonna destra quando nessun candidate e selezionato
- le CTA dal centro cambiano focus/tab della colonna destra, non ne governano l'apertura iniziale

## Out of Scope

- nuovi blocchi della scheda `Proposal`
- override
- logica Core proposal

## Constraints

- la colonna destra non deve richiedere un click secondario per apparire
- il comportamento deve restare coerente con il layout a 3 colonne
- il task resta separato da `TASK-V2-152`

## Acceptance Criteria

- selezionando un candidate a sinistra la colonna destra si aggiorna subito
- la colonna destra mostra placeholder solo in assenza di selezione
- le CTA del centro non aprono piu la terza colonna da zero
- il flusso risulta:
  - sinistra = selezione
  - centro = comprensione
  - destra = proposta contestuale immediata

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-20

TypeScript pulito.

**`PlanningWorkspacePage.tsx`**:
- Layout a 3 colonne sempre attivo: centro fisso `w-[46%] shrink-0`, destra `flex-1` sempre renderizzata
- Colonna destra: placeholder se `!selectedItem`, `PannelloProposal` se `rightPanel === 'proposal'`, `PannelloPlanningScorte` se `rightPanel === 'planning_scorte'`
- `handleSelectCandidate`: ora imposta `rightPanel('proposal')` direttamente (non più `'none'`)
- `useEffect` su `selectedItem.article_code`: aggiunge `setRightPanel('proposal')` quando il candidato cambia; mantiene `setRightPanel('none')` per assenza di selezione (→ placeholder)
- `CenterColumn`: prop `onOpenProposal` rinominata in `onSwitchToProposal` (semantica: cambia tab, non apre colonna); il blocco CTA proposta resta ma con label "Vedi proposta →"; visibile solo se `proposal_status` è valorizzato
- `PannelloProposal`: rimosso bottone ✕ e prop `onClose` (proposta è il pannello default, non può essere chiuso); intestazione con solo tabs
- `PannelloPlanningScorte`: ✕ ora chiama `onClose` che nel workspace porta a `setRightPanel('proposal')` (non `'none'`); tooltip aggiornato a "Torna a Proposta"
