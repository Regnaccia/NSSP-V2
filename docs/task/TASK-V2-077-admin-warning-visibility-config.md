# TASK-V2-077 - Admin warning visibility config

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

Introdurre la configurazione amministrativa della visibilita dei warning, coerente con
la regola che `Warnings` e un modulo trasversale unico governato dalla surface `admin`.

## Context

`TASK-V2-076` introduce il primo slice Core del modulo `Warnings`.

Il `DL-ARCH-V2-029` fissa che:

- i warning non vanno duplicati per reparto
- la visibilita deve essere governata centralmente
- la surface responsabile di questa governance e `admin`

## Scope

- introdurre un modello/config interna V2 per la visibilita dei warning
- supportare almeno:
  - `visible_in_surfaces`
- predisporre l'estensibilita futura per:
  - `visible_to_roles`
  - `domain_tags`
- esporre API/Core per leggere e modificare la configurazione di visibilita
- integrare la gestione nella surface `admin`

## Out of Scope

- UI dedicata del modulo `Warnings`
- badge warning nelle altre surface
- workflow warning `open / acknowledged / resolved`
- tipi warning oltre `NEGATIVE_STOCK`

## Constraints

- la configurazione di visibilita e interna V2
- non devono nascere warning distinti per reparto
- la visibilita deve agire come metadato del warning canonico

## Acceptance Criteria

- esiste una configurazione persistente o equivalente per la visibilita dei warning
- `admin` puo governare almeno le surface in cui un warning e visibile
- il modello resta coerente con `DL-ARCH-V2-029`

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati su config warning
- build frontend
- smoke admin su lettura e modifica della visibilita

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Backend:**
- `core/warnings/config_model.py`: `WarningTypeConfig` ORM — tabella `core_warning_type_config` (warning_type, visible_in_surfaces JSON, updated_at)
- `core/warnings/config.py`: `WarningTypeConfigItem` read model, `KNOWN_WARNING_TYPES`, `KNOWN_SURFACES`, `get_visible_in_surfaces` (default fallback), `list_warning_configs`, `set_warning_config`
- `core/warnings/queries.py`: `list_warnings_v1` ora legge `visible_in_surfaces` dal DB via `get_visible_in_surfaces` invece di hardcoded
- `core/warnings/__init__.py`: esporta tutte le nuove funzioni/costanti
- `app/schemas/admin.py`: `UpdateWarningConfigRequest`
- `app/api/admin.py`: `GET /api/admin/warnings/config`, `PUT /api/admin/warnings/config/{warning_type}`
- Migrazione `20260413_020_core_warning_type_config.py`

**Frontend:**
- `AdminWarningsPage.tsx`: pannelli per ogni tipo warning con checkbox per superficie; save/annulla inline
- Route `/admin/warnings` in `App.tsx`
- Voce "Warning Config" nella sidebar admin di `AppShell.tsx`
- `WarningTypeConfigItem` aggiunto a `types/api.ts`

## Verification Notes

- 29/29 test (`test_core_warning_config.py` + `test_core_warnings.py`) — tutti verdi
- `npm run build` — zero errori TypeScript
- Smoke admin: navigare `/admin/warnings`, modificare `visible_in_surfaces` e verificare persistenza

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

