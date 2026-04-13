# TASK-V2-082 - Warnings surface filter by current area

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/task/TASK-V2-081-realign-warning-visibility-by-area.md`

## Goal

Correggere la surface `Warnings` affinche mostri solo i warning di competenza
dell'area/reparto corrente, invece di mostrare sempre tutti i warning canonici.

## Context

`TASK-V2-081` ha chiuso il riallineamento del modello di visibilita:

- `visible_in_surfaces` -> `visible_to_areas`
- aree V1:
  - `magazzino`
  - `produzione`
  - `logistica`

La semantica corretta pero e questa:

- il modulo `Warnings` e trasversale e accessibile ai reparti
- ogni reparto vede solo i warning della propria competenza
- la competenza e definita da `admin` tramite `visible_to_areas`

Oggi la surface `/produzione/warnings` continua invece a mostrare tutti i warning canonici.

## Scope

- filtrare il contenuto della surface `Warnings` sull'area/reparto corrente
- applicare `visible_to_areas` anche alla lista warning della surface dedicata
- mantenere la configurazione `admin` come sorgente unica della visibilita
- chiarire il contratto API/backend della surface `Warnings`

## Out of Scope

- nuovi tipi warning
- badge warning nelle altre surface
- workflow warning avanzato
- redesign della warning visibility

## Constraints

- `TASK-V2-081` resta chiuso: questo task e solo un follow-up di correzione comportamento
- non duplicare warning per reparto
- la surface `Warnings` deve restare modulo trasversale, ma con contenuto filtrato per area corrente

## Acceptance Criteria

- la surface `Warnings` non mostra piu sempre tutti i warning
- un utente vede solo i warning visibili alla propria area/reparto
- la configurazione `admin` tramite `visible_to_areas` ha effetto anche sulla lista warning
- il comportamento e coerente con la semantica desiderata del modulo

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati su filtro warning per area corrente
- build frontend
- smoke UI su surface `Warnings` con configurazioni area diverse

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Approccio**: filtro lato backend derivando le aree utente dai ruoli JWT. Nessun cambiamento frontend.

**Core — `queries.py`**: aggiunta funzione pura `filter_warnings_by_areas(warnings, user_areas, is_admin)`:
- `is_admin=True` → restituisce tutta la lista senza filtro
- altrimenti → include solo i warning dove `any(area in w.visible_to_areas for area in user_areas)`
- esportata da `__init__.py` con aggiornamento `__all__`

**App — `api/produzione.py`** `GET /produzione/warnings`:
- estratti `roles` dal payload JWT (`payload.get("roles", [])`)
- `is_admin = "admin" in roles`
- `user_areas = [r for r in roles if r in KNOWN_AREAS]` — solo aree operative valide
- applicato `filter_warnings_by_areas(all_warnings, user_areas, is_admin)`

**Mapping role → area**: diretto (ruoli operativi hanno lo stesso nome delle aree). `admin` non e un'area: bypassa il filtro.

**Nessuna modifica frontend**: la logica e interamente backend; il token JWT gia contiene i ruoli.

## Verification Notes

- `pytest tests/core/test_core_warning_filter.py` — 11/11 passed
- `npm run build` — zero errori TypeScript
- Smoke: utente `produzione` su `/produzione/warnings` → vede solo warning con `produzione` in `visible_to_areas`
- Smoke: utente `admin` su `/produzione/warnings` → vede tutti i warning

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`
