# TASK-V2-118 - Model raw bar length enable and article config

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

Introdurre il flag famiglia `raw_bar_length_mm_enabled` e il campo articolo `raw_bar_length_mm`, rendendoli persistenti, esposti dal Core e configurabili tramite gli endpoint gia esistenti.

## Context

La nuova logica `proposal_full_bar_v1` richiede:

- una famiglia che dichiari la pertinenza del campo barra
- un articolo che valorizzi la lunghezza barra reale

Il flag famiglia non seleziona la logica proposal: abilita solo la configurabilita del dato `raw_bar_length_mm`.

## Scope

- aggiungere `raw_bar_length_mm_enabled` al modello/config famiglie
- aggiungere `raw_bar_length_mm` al modello/config articolo
- esporre i nuovi campi nei read model Core `famiglie` e `articoli`
- estendere gli endpoint PATCH esistenti per salvarli
- aggiornare eventuali migration necessarie

## Out of Scope

- UI famiglie
- UI articoli
- implementazione della logica `proposal_full_bar_v1`
- preview export proposal

## Constraints

- `raw_bar_length_mm_enabled` abilita la configurabilita del campo, non la scelta della logica
- `raw_bar_length_mm` e un campo articolo-specifico opzionale
- nessun default famiglia per il valore numerico di `raw_bar_length_mm`

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
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
- `Pattern 04 - Core read model prima della UI`
- `Pattern 07 - Strategy/config esplicita per logiche di dominio`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

I nuovi campi vengono letti dai normali read model `famiglie` e `articoli`.

## Acceptance Criteria

- famiglia espone `raw_bar_length_mm_enabled`
- articolo espone `raw_bar_length_mm`
- i nuovi campi sono persistiti e letti correttamente
- gli endpoint PATCH esistenti supportano la scrittura dei nuovi valori

## Deliverables

- modello/migration per i nuovi campi
- query/read model Core aggiornati
- endpoint backend aggiornati
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
python -m pytest V2/backend/tests/core -k "articoli or famiglie or proposal" -q
```

Atteso: exit code `0`.

## Implementation Notes

- mantenere `raw_bar_length_mm` separato da ogni logica proposal specifica
- il read model `articoli` deve esporre il campo anche se la famiglia non abilita attualmente la configurazione, per trasparenza tecnica

## Documentation Handoff

- Codex aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Introdotti `raw_bar_length_mm_enabled` (famiglia) e `raw_bar_length_mm` (articolo).

**`alembic/versions/20260415_028_raw_bar_length_mm.py`**:
- `articolo_famiglie.raw_bar_length_mm_enabled BOOLEAN NOT NULL DEFAULT FALSE`
- `core_articolo_config.raw_bar_length_mm NUMERIC(10,4) NULL`

**`core/articoli/models.py`**:
- `ArticoloFamiglia.raw_bar_length_mm_enabled: Mapped[bool]`
- `CoreArticoloConfig.raw_bar_length_mm: Mapped[Decimal | None]`

**`core/articoli/read_models.py`**:
- `FamigliaRow.raw_bar_length_mm_enabled: bool = False`
- `ArticoloDetail.raw_bar_length_mm: Decimal | None = None`

**`core/articoli/queries.py`**:
- `_famiglia_to_row`: espone `raw_bar_length_mm_enabled`
- `get_articolo_detail`: espone `raw_bar_length_mm` (sempre, indipendentemente dal flag famiglia)
- `toggle_famiglia_raw_bar_length_mm_enabled(session, code) -> FamigliaRow`
- `set_articolo_raw_bar_length_mm(session, codice_articolo, raw_bar_length_mm: Decimal | None) -> None`

**`app/api/produzione.py`**:
- `SetRawBarLengthMmRequest` body model
- `PATCH /famiglie/{code}/raw-bar-length-enabled` → toggle flag famiglia
- `PATCH /articoli/{codice}/raw-bar-length-mm` → set/unset valore articolo

**`tests/core/test_core_raw_bar_length_mm.py`**:
- 10 test: default flag False, toggle On/Off/NotFound, default articolo None, set/unset/create-config, indipendenza da flag famiglia.

**Verification**: 114/114 test core articoli/famiglie/proposal passati.

## Completed At

2026-04-15

## Completed By

Claude Code
