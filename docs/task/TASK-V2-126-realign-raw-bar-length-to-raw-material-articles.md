# TASK-V2-126 - Realign raw bar length to raw-material articles

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-037.md`

## Goal

Correggere il modello implementativo di `raw_bar_length_mm` affinche il dato barra sia letto sull'articolo materiale grezzo associato e non sull'articolo finito della proposal.

## Context

La validazione operativa ha mostrato che:

- la proposal `full bar` parte dal finito
- il finito espone `materiale_grezzo_codice`
- `raw_bar_length_mm` e configurato sul materiale grezzo

L'implementazione attuale legge invece `raw_bar_length_mm` sul finito e produce fallback errati tipo `missing_raw_bar_length` anche quando la barra del materiale e correttamente configurata.

## Scope

- correggere `proposal_full_bar_v1` per risolvere `materiale_grezzo_codice` dal finito
- leggere `raw_bar_length_mm` sul materiale grezzo associato
- riallineare il fallback `missing_raw_bar_length` a questa risoluzione
- riallineare il warning `MISSING_RAW_BAR_LENGTH` alla semantica materiale grezzo
- aggiungere test backend mirati sul caso finito -> materiale grezzo

## Out of Scope

- redesign UI proposal
- nuove logiche proposal
- nuovi warning diversi da `MISSING_RAW_BAR_LENGTH`

## Constraints

- `usable_mm_per_piece` continua a essere calcolato sul finito
- `raw_bar_length_mm` viene letto sul materiale grezzo associato
- se `materiale_grezzo_codice` manca o non risolve un articolo valido, la logica fa fallback a pezzi
- il warning `MISSING_RAW_BAR_LENGTH` resta nel modulo `Warnings`, ma riferito al materiale grezzo

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` Si
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` Si
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 01 - Entita governata in admin, consumata nelle surface operative`
- `Pattern 04 - Core read model prima della UI`
- `Pattern 09 - Warning canonico separato dal modulo che lo consuma`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La correzione si applica ai normali path Core di proposal e warnings.

## Acceptance Criteria

- `proposal_full_bar_v1` legge `raw_bar_length_mm` sul materiale grezzo associato
- il caso finito con materiale grezzo configurato non ricade piu in `missing_raw_bar_length`
- `MISSING_RAW_BAR_LENGTH` segnala il materiale grezzo non configurato, non il finito
- i test backend coprono il path finito -> materiale grezzo

## Deliverables

- correzione Core proposal
- correzione Core warnings
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
python -m pytest V2/backend/tests/core/test_core_production_proposals.py V2/backend/tests/core/test_core_proposal_full_bar_v1.py V2/backend/tests/core/test_core_warnings.py -q
```

Atteso: exit code `0`.

## Implementation Notes

- il dato barra resta fisicamente su `CoreArticoloConfig`, ma la proposal logic deve risolverlo sul codice materiale associato
- se il finito non ha materiale valido, il fallback resta a pezzi

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

## Implementation Log

### Core proposal — `_resolve_full_bar_proposed_qty`

- `core/production_proposals/queries.py`: rimossa la lettura di `raw_bar_length_mm` da `CoreArticoloConfig` del finito.
- Nuova catena di risoluzione:
  1. `sync_art.materiale_grezzo_codice` → codice del materiale grezzo
  2. `_resolve_sync_articolo_code` sul codice materiale (normalizzazione casing)
  3. `CoreArticoloConfig` del materiale grezzo → `raw_bar_length_mm`
- Se `materiale_grezzo_codice` è assente o il materiale non ha config, `raw_bar_length_mm = None` → fallback `missing_raw_bar_length` (invariato).
- `occorrente` e `scarto` restano letti dal finito (invariato).

### Warning MISSING_RAW_BAR_LENGTH

- `core/warnings/queries.py`: aggiunto `select` agli import.
- Blocco MISSING_RAW_BAR_LENGTH riscritto: per ogni finito in famiglia con `raw_bar_length_mm_enabled=True`, risolve `materiale_grezzo_codice`, carica `CoreArticoloConfig` del grezzo, controlla `raw_bar_length_mm`.
- `entity_key` / `article_code` del warning è ora il codice materiale grezzo (non il finito).
- Deduplicazione via `seen_raw_material_keys`: se più finiti condividono lo stesso grezzo, viene emesso un solo warning.
- Finiti senza `materiale_grezzo_codice` vengono saltati silenziosamente.

### Test

- `tests/core/test_core_warnings.py`: helper `_art_bar` / `_config_bar` sostituiti con `_art_finito_bar` / `_art_grezzo_bar` con semantica finito→grezzo. Tutti i test MISSING_RAW_BAR_LENGTH aggiornati. Aggiunto `test_missing_bar_nessun_warning_quando_materiale_grezzo_assente` e `test_missing_bar_piu_finiti_stesso_materiale_deduplicato`.
- `tests/core/test_core_production_proposals.py`: `test_diagnostics_full_bar_success_no_fallback` aggiornato per usare `materiale_grezzo_codice="MAT001"` su SyncArticolo del finito e `raw_bar_length_mm=3000` su `CoreArticoloConfig` di MAT001.

### Verifica

```
85 passed
```
