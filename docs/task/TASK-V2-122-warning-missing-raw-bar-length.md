# TASK-V2-122 - Warning missing raw bar length

## Status
Completed

## Date
2026-04-15

## Owner
Codex

## Source Documents

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-035.md`

## Goal

Introdurre nel modulo `Warnings` il nuovo warning `MISSING_RAW_BAR_LENGTH` per gli articoli la cui famiglia richiede `raw_bar_length_mm` ma il valore articolo non e configurato correttamente.

## Context

La logica `proposal_full_bar_v1` richiede il dato `raw_bar_length_mm` a livello articolo. Dal momento in cui la famiglia abilita quel dato come pertinente/richiesto, la sua assenza deve diventare una incoerenza visibile nel modulo canonico `Warnings`.

## Scope

- aggiungere `MISSING_RAW_BAR_LENGTH` al catalogo warning
- generare il warning quando:
  - `raw_bar_length_mm_enabled = true`
  - `raw_bar_length_mm is null` oppure `<= 0`
- esporre il warning nei read model warning con payload diagnostico minimo
- assegnare audience iniziale:
  - `produzione`
  - `admin`
- aggiungere test Core mirati sul modulo `Warnings`

## Out of Scope

- visualizzazione dedicata del warning in `articoli` o `proposal`
- blocchi automatici proposal
- warning sul motivo di fallback della logica `proposal_full_bar_v1`

## Constraints

- il warning appartiene al modulo `Warnings`, non alla logica proposal
- il warning deve scattare anche se l'articolo non usa ancora `proposal_full_bar_v1`
- la semantica del warning e configurativa, non di bisogno produttivo

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
- `Richiede warnings dedicati o impatta warning esistenti?` Si
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 09 - Warning canonico separato dal modulo che lo consuma`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

Il warning viene valutato nel normale flusso del modulo `Warnings`.

## Acceptance Criteria

- esiste il nuovo warning type `MISSING_RAW_BAR_LENGTH`
- il warning scatta per famiglia con `raw_bar_length_mm_enabled = true` e articolo con valore mancante o `<= 0`
- audience iniziale corretta:
  - `produzione`
  - `admin`
- il payload warning espone i dati minimi per diagnosi
- i test Core warning coprono i casi base

## Deliverables

- config warning aggiornata
- query/read model warning aggiornati
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
python -m pytest V2/backend/tests/core -k "warning" -q
```

Atteso: exit code `0`.

## Implementation Notes

- il warning deve usare i dati Core articolo/famiglia, non ricalcolare logiche proposal
- nessun coupling con il fallback di `proposal_full_bar_v1`: il warning segnala config mancante, la proposal logic decide comunque il fallback a pezzi

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Introdotto `MISSING_RAW_BAR_LENGTH` nel modulo canonico `Warnings`.

**`core/warnings/logic.py`**:
- `is_missing_raw_bar_length(raw_bar_length_mm: Decimal | None) -> bool`
  - True se None o <= 0; False altrimenti

**`core/warnings/config.py`**:
- `KNOWN_WARNING_TYPES`: aggiunto `"MISSING_RAW_BAR_LENGTH"` (lista ordinata alfabeticamente)
- `_AREA_DEFAULTS`: `"MISSING_RAW_BAR_LENGTH": ["produzione", "admin"]`

**`core/warnings/read_models.py`**:
- `WarningItem`: aggiunto sezione specifici MISSING_RAW_BAR_LENGTH:
  - `famiglia_code: str | None = None`
  - `raw_bar_length_mm_enabled: bool | None = None`
  - `raw_bar_length_mm: Decimal | None = None`

**`core/warnings/queries.py`**:
- Import `ArticoloFamiglia`, `CoreArticoloConfig`, `is_missing_raw_bar_length`
- `list_warnings_v1`: nuovo blocco MISSING_RAW_BAR_LENGTH
  - JOIN `CoreArticoloConfig` → `ArticoloFamiglia` (su `famiglia_code`)
  - JOIN → `SyncArticolo` (UPPER match, `attivo=True`)
  - Filter `raw_bar_length_mm_enabled=True`
  - Per ogni riga: `is_missing_raw_bar_length(cfg.raw_bar_length_mm)` → genera `WarningItem`
  - `created_at = art.synced_at`

**`core/warnings/__init__.py`**:
- Export `is_missing_raw_bar_length`

**`tests/core/test_core_warnings.py`**:
- 5 test logica pura: None, zero, negativo, valido, piccolo positivo
- 10 test integrazione: genera warning (None, zero), nessun warning (valido, flag=False),
  audience corretta, piu articoli, warning_id unici, campi stock None, coesistenza 3 tipi

**Verification**: 69/69 test warning passati.

## Completed At

2026-04-15

## Completed By

Claude Code
