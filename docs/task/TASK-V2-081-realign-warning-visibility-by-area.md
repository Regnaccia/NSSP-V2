# TASK-V2-081 - Realign warning visibility by area

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`

## Goal

Riallineare il modello di visibilita dei warning dal livello "singola surface"
al livello corretto "area/reparto operativo".

## Context

`TASK-V2-077` ha introdotto una configurazione warning visibile per surface
applicative (`articoli`, `planning candidates`, `criticita`, `warnings`).

Questo e utile come primo passo tecnico, ma non corrisponde alla semantica desiderata.

Il modello corretto e:

- visibilita per area/reparto:
  - `magazzino`
  - `produzione`
  - `logistica`
- surface `Warnings` visibile di default come punto trasversale unico

## Scope

- sostituire o affiancare `visible_in_surfaces` con un modello `visible_to_areas`
- riallineare Core/API/admin al nuovo vocabolario
- mantenere `Warnings` come surface consultabile di default
- definire una strategia di migrazione dai dati/config gia scritti da `TASK-V2-077`

## Out of Scope

- workflow warning avanzato
- nuovi tipi warning
- badge warning nelle altre surface

## Constraints

- non duplicare warning per reparto
- la configurazione continua a vivere in `admin`
- la surface `Warnings` non deve dipendere da una configurazione warning-by-warning per esistere

## Acceptance Criteria

- la visibilita dei warning e modellata per area/reparto, non per singola surface
- `Warnings` resta disponibile come modulo trasversale di default
- la configurazione `admin` usa il nuovo vocabolario
- la migrazione dal modello precedente e documentata e verificata

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati sulla nuova config warning
- build frontend
- smoke admin sulla configurazione per aree
- verifica che la surface `Warnings` resti raggiungibile di default

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Migrazione semantica**: `visible_in_surfaces` → `visible_to_areas`, vocabolario aree `magazzino / produzione / logistica`.

**Backend core:**
- `config_model.py`: campo ORM rinominato `visible_in_surfaces` → `visible_to_areas`
- `config.py`: `KNOWN_SURFACES` → `KNOWN_AREAS` (`["magazzino", "produzione", "logistica"]`); `get_visible_in_surfaces` → `get_visible_to_areas`; default NEGATIVE_STOCK: `["magazzino", "produzione"]`
- `read_models.py`: campo `WarningItem.visible_in_surfaces` → `visible_to_areas`
- `queries.py`: usa `get_visible_to_areas`, popola `visible_to_areas=areas`
- `__init__.py`: aggiornati export (`KNOWN_AREAS`, `get_visible_to_areas`)

**Backend app:**
- `schemas/admin.py`: `UpdateWarningConfigRequest.visible_in_surfaces` → `visible_to_areas`
- `api/admin.py`: import `KNOWN_AREAS`; endpoint `PUT /warnings/config/{type}` valida le aree contro `KNOWN_AREAS` (HTTP 422 se sconosciuta); chiama `set_warning_config(..., body.visible_to_areas)`
- `api/produzione.py`: rimosso filtro `if "warnings" in w.visible_in_surfaces` — la surface Warnings e trasversale e mostra tutti i warning canonici senza dipendere dalla config per area

**Alembic migration** `20260413_021_visible_to_areas.py`:
- SQLite non supporta `ALTER COLUMN`: tabella ricreata con colonna `visible_to_areas`
- reset semantico: righe esistenti eliminate (valori surface-based non mappabili a aree)

**Frontend:**
- `types/api.ts`: `WarningItem.visible_to_areas`, `WarningTypeConfigItem.visible_to_areas`
- `AdminWarningsPage.tsx`: `KNOWN_AREAS`, `AREA_LABELS`, payload `{ visible_to_areas }`, testo aggiornato; nota inline "Avvertimenti mostra sempre tutti i warning"

## Verification Notes

- `pytest tests/core/test_core_warnings.py tests/core/test_core_warning_config.py` — 29/29 passed
- `npm run build` — zero errori TypeScript
- Smoke: `/admin/warnings` — panel con checkboxes Magazzino / Produzione / Logistica
- Smoke: `/produzione/warnings` — surface mostra tutti i warning senza dipendere dalla config area

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

