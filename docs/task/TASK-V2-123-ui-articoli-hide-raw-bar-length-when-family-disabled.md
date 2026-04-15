# TASK-V2-123 - UI articoli hide raw bar length when family disabled

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/decisions/ARCH/DL-ARCH-V2-035.md`
- `docs/task/TASK-V2-120-ui-articoli-raw-bar-length-mm-and-proposal-logic.md`

## Goal

Correggere la UI `articoli` affinche il campo `raw_bar_length_mm` sia visibile ed editabile solo quando la famiglia dell'articolo ha `raw_bar_length_mm_enabled = true`.

## Context

Il comportamento implementato in `TASK-V2-120` ha lasciato il campo sempre visibile, limitandosi a de-enfatizzarlo quando la famiglia non abilita il dato barra. Questo non e coerente col requisito reale emerso in validazione operativa:

- famiglie standard senza flag attivo non devono mostrare il campo
- il campo deve comparire solo nei casi in cui e semanticamente pertinente

## Scope

- nascondere in UI `articoli` il blocco/campo `raw_bar_length_mm` quando `raw_bar_length_mm_enabled = false`
- mantenere visibile la scelta `proposal_logic_key` secondo il contratto attuale
- verificare che il salvataggio del campo non sia piu raggiungibile dalla UI quando la famiglia non abilita il dato

## Out of Scope

- cambiamenti al modello backend
- cambiamenti alla logica `proposal_full_bar_v1`
- warning `MISSING_RAW_BAR_LENGTH`
- redesign generale del pannello proposal logic

## Constraints

- il campo deve essere mostrato solo con flag famiglia attivo
- il fix e UI-only: il backend puo continuare a esporre il dato per trasparenza tecnica
- non introdurre logiche di clear automatico del valore salvato quando il campo viene nascosto

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` Si
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 03 - Config famiglia separata da config articolo`
- `Pattern 05 - Configurazione articolo + valore effettivo/contratto Core`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand dedicato`

Resta il comportamento corrente della surface `articoli`.

## Acceptance Criteria

- se `raw_bar_length_mm_enabled = false`, il campo `raw_bar_length_mm` non e visibile in UI
- se `raw_bar_length_mm_enabled = true`, il campo `raw_bar_length_mm` e visibile e modificabile
- il build frontend resta verde

## Deliverables

- fix UI in `articoli`
- eventuale adeguamento del task note/completion context se utile
- build frontend mirata

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

- il fix corregge un'interpretazione errata del requisito nel task `120`
- non serve cambiare il backend: basta usare il flag famiglia gia disponibile nel read model

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Corretto il rendering condizionale del campo `raw_bar_length_mm` nella surface `articoli`.

**`backend/src/nssp_v2/core/articoli/read_models.py`**:
- `FamigliaItem`: aggiunto `raw_bar_length_mm_enabled: bool = False`

**`backend/src/nssp_v2/core/articoli/queries.py`**:
- `list_famiglie`: popola `raw_bar_length_mm_enabled` da `ArticoloFamiglia.raw_bar_length_mm_enabled`

**`frontend/src/types/api.ts`**:
- `FamigliaItem`: aggiunto `raw_bar_length_mm_enabled: boolean`

**`frontend/src/pages/surfaces/ProduzioneHome.tsx`**:
- Il blocco "Lunghezza barra grezza (mm)" e ora avvolto da:
  `{famiglie.find((f) => f.code === detail.famiglia_code)?.raw_bar_length_mm_enabled && (...)}`
- Rimossa la nota ridondante "La famiglia abilita il campo..." (la visibilita condizionale la sostituisce)
- Il salvataggio del campo non e piu raggiungibile dalla UI quando la famiglia ha il flag disabilitato

**Verification**: `npm run build` — exit code 0.

## Completed At

2026-04-15

## Completed By

Claude Code
