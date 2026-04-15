# TASK-V2-120 - UI articoli raw bar length mm and proposal logic

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

Esporre in `articoli` il campo `raw_bar_length_mm` e la nuova scelta logica `proposal_full_bar_v1`, rendendo chiara la relazione con il flag famiglia `raw_bar_length_mm_enabled`.

## Context

La famiglia abilita la configurabilita del campo barra, ma la scelta della logica resta articolo-specifica. La UI `articoli` e il posto corretto per:

- valorizzare `raw_bar_length_mm`
- scegliere `proposal_logic_key`

## Scope

- mostrare `raw_bar_length_mm` nel dettaglio `articoli`
- renderlo editabile quando pertinente
- mostrare nel catalogo delle proposal logic anche `proposal_full_bar_v1`
- chiarire la relazione:
  - famiglia abilita il campo
  - articolo configura il valore e sceglie la logica

## Out of Scope

- implementazione Core della logica barra
- preview export proposal
- writer `xlsx`

## Constraints

- `raw_bar_length_mm` non sostituisce `proposal_logic_key`
- la UI deve evitare di far intendere che il solo valore barra attiva automaticamente la logica
- la configurazione deve restare coerente con il pattern gia introdotto per proposal logic in `articoli`

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
- `Pattern 05 - Configurazione articolo + valore effettivo/contratto Core`
- `Pattern 07 - Strategy/config esplicita per logiche di dominio`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand dedicato`

Resta il comportamento corrente della surface `articoli`.

## Acceptance Criteria

- `raw_bar_length_mm` e visibile in `articoli`
- la configurazione e editabile quando pertinente
- `proposal_full_bar_v1` compare nel catalogo logiche proposal selezionabili
- la UI rende chiaro che la famiglia abilita il campo ma l'articolo sceglie la logica

## Deliverables

- aggiornamento UI `articoli`
- eventuali adattamenti di type/frontend contract
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

- se la famiglia non abilita il campo, la UI puo de-enfatizzarlo o segnalarne la non pertinenza, ma senza nascondere in modo da perdere trasparenza tecnica
- il catalogo logiche proposal deve allinearsi al registry backend reale

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Esposto `raw_bar_length_mm` e aggiunto `proposal_full_bar_v1` al catalogo logiche articolo.

**`backend/src/nssp_v2/core/production_proposals/config.py`**:
- `"proposal_full_bar_v1"` aggiunto a `KNOWN_PROPOSAL_LOGICS` e `_DEFAULT_PARAMS_BY_KEY`

**`backend/src/nssp_v2/core/production_proposals/logic.py`**:
- `compute_proposed_qty`: gestisce `proposal_full_bar_v1` come stub con comportamento identico a `proposal_target_pieces_v1` (implementazione Core in backlog)
- `compute_note_fragment`: restituisce `None` anche per `proposal_full_bar_v1`

**`frontend/src/types/api.ts`**:
- `ArticoloDetail.raw_bar_length_mm: string | null`

**`frontend/src/pages/surfaces/ProduzioneHome.tsx`**:
- `ColonnaDettaglio`: nuova prop `onRawBarLengthMmChange`
- Stato `rawBarLengthInput` + `rawBarSaveStatus` con reset al cambio articolo
- Handler `handleRawBarLengthSubmit` → `PATCH /produzione/articoli/{codice}/raw-bar-length-mm`
- Sezione UI nel pannello "Proposal logic V1":
  - Nota esplicativa: la famiglia abilita il campo, l'articolo valorizza la lunghezza e sceglie la logica
  - `proposal_full_bar_v1` compare nel `<select>` logiche (da `proposalKnownLogics` backend)
  - Sub-sezione "Lunghezza barra grezza (mm)": valore corrente read-only + input numerico + salva/rimuovi
- `ProduzioneHome`: handler `handleRawBarLengthMmChange` passato a `ColonnaDettaglio`

**Verification**: `npm run build` — exit code 0.

## Completed At

2026-04-15

## Completed By

Claude Code
