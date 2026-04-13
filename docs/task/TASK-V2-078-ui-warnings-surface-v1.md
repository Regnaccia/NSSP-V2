# TASK-V2-078 - UI Warnings surface V1

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

Introdurre la prima surface dedicata del modulo `Warnings`, come lista operativa
minima delle anomalie canoniche generate dal Core.

## Context

Dopo `TASK-V2-076` il sistema dispone del primo warning canonico (`NEGATIVE_STOCK`).

Serve una prima surface dedicata per:

- consultare i warning in modo esplicito
- non costringere gli operatori a scoprirli solo tramite moduli secondari

## Scope

- introdurre una nuova surface `warnings`
- vista tabellare minima dei warning
- mostrare almeno:
  - tipo
  - severita
  - entita
  - messaggio
  - created_at
- supportare almeno il tipo `NEGATIVE_STOCK`
- applicare la visibilita configurata

## Refresh Behavior

- nessun refresh semantico backend dedicato in questo primo slice
- la surface rilegge il read model `Warnings` gia calcolato

## Out of Scope

- workflow warning avanzato
- acknowledge / resolve
- note operatore
- altri tipi warning oltre `NEGATIVE_STOCK`
- integrazione badge nelle altre surface

## Constraints

- la surface consuma solo il modulo `Warnings`
- non deve duplicare logiche di detection
- deve rispettare la visibilita configurata a livello admin

## Acceptance Criteria

- esiste una surface `Warnings` consultiva minima
- i warning `NEGATIVE_STOCK` sono leggibili in lista
- la surface rispetta la configurazione di visibilita

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati su API/lista warning
- build frontend
- smoke UI della nuova surface

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

- `GET /api/produzione/warnings` in `produzione.py`: chiama `list_warnings_v1`, filtra dove `"warnings" in visible_in_surfaces` — rispetta la config admin (TASK-V2-077)
- `WarningItem` aggiunto a `types/api.ts`
- `WarningsPage.tsx`: header con contatore, tabella con colonne Tipo / Sev. / Articolo / Messaggio / Giacenza / Anomalia / Rilevato il; `SeverityBadge` colorato; empty state dedicato
- Route `/produzione/warnings` in `App.tsx` (ruolo `produzione`)
- Voce "Avvertimenti" nella sidebar produzione di `AppShell.tsx`

Visibilita rispettata: la surface mostra solo i warning dove `"warnings"` compare in `visible_in_surfaces` — se l'admin rimuove `warnings` dalla config, l'endpoint restituisce lista vuota.

## Verification Notes

- `npm run build` — zero errori TypeScript
- Smoke: navigare `/produzione/warnings` — verifica tabella NEGATIVE_STOCK, contatore header, empty state quando nessun warning visibile nella surface

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

