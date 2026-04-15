# TASK-V2-119 - UI famiglie raw bar length enable

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

Aggiungere in UI `famiglie` il toggle `raw_bar_length_mm_enabled`, con semantica esplicita: abilita la configurazione del campo barra, non la scelta della logica proposal.

## Context

La logica `proposal_full_bar_v1` richiede un dato articolo-specifico `raw_bar_length_mm`, ma quel dato ha senso solo per alcune famiglie. La famiglia governa la pertinenza/configurabilita del dato, non l'assegnazione della logica.

## Scope

- aggiungere il toggle `raw_bar_length_mm_enabled` nella tabella/configurazione famiglie
- collegarlo agli endpoint/backend gia estesi dal task modello
- rendere la UI semanticamente chiara

## Out of Scope

- campo articolo `raw_bar_length_mm`
- scelta proposal logic in `articoli`
- implementazione Core della logica barra

## Constraints

- il testo UI deve evitare l'ambiguita tra:
  - abilitare il campo barra
  - usare la logica full bar
- il flag resta un semplice booleano di configurabilita

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` Si
- `Introduce override articolo o default famiglia?` Si
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 03 - Config famiglia separata da config articolo`
- `Pattern 10 - Toggle UI con semantica univoca`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand dedicato`

Resta il comportamento corrente della surface `famiglie`.

## Acceptance Criteria

- il flag `raw_bar_length_mm_enabled` e visibile in `famiglie`
- il flag e modificabile e persistente
- la UI spiega che il flag abilita il campo barra, non la proposal logic

## Deliverables

- aggiornamento UI `famiglie`
- test/build frontend mirati

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
npm run build
```

Atteso: exit code `0`.

## Implementation Notes

- evitare label come `usa barra intera` o simili: sarebbero semanticamente sbagliate a livello famiglia
- il naming UI deve restare vicino al concetto di "campo barra disponibile/configurabile"

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Aggiunto il toggle `raw_bar_length_mm_enabled` alla superficie UI famiglie.

**`frontend/src/types/api.ts`**:
- `FamigliaRow.raw_bar_length_mm_enabled: boolean`

**`frontend/src/pages/surfaces/FamigliePage.tsx`**:
- Stato `togglingBarLength` + handler `handleToggleBarLength` → `PATCH /famiglie/{code}/raw-bar-length-enabled`
- Colonna intestazione `Campo barra` con tooltip esplicito (abilita configurazione dato, non scelta logica proposal)
- Cella checkbox con `title` che disambigua la semantica (campo barra configurabile / non configurabile)
- Nota testuale aggiornata: il flag abilita il dato `raw_bar_length_mm` per gli articoli, non determina la proposal logic

**Verification**: `npm run build` — exit code 0.

## Completed At

2026-04-15

## Completed By

Claude Code
