# TASK-V2-061 - Separazione ricerca codice e descrizione articoli

## Status
Todo

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-024-filtro-famiglia-articoli.md`

## Goal

Raffinare la ricerca nella vista `articoli` separandola in due campi distinti:

- ricerca per `codice articolo`, con normalizzazione dimensionale attiva
- ricerca per `descrizione`, senza conversione automatica dei separatori

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-020`
- `TASK-V2-024`

## Context

Oggi la vista `articoli` usa un solo campo di ricerca che lavora contemporaneamente su:

- codice articolo
- descrizione

applicando la normalizzazione UX dei separatori dimensionali (`.` -> `x`, `X` -> `x`) prevista da `DL-UIX-V2-004`.

Questa scelta e utile per il codice articolo, ma meno corretta per la descrizione libera.

Il refinement richiesto e:

- mantenere la normalizzazione solo per la ricerca per codice
- lasciare la ricerca descrizione come ricerca testuale semplice, senza conversioni automatiche

## Scope

### In Scope

- sostituire il campo unico di ricerca nella vista `articoli` con due campi distinti
- introdurre un campo `codice` con la normalizzazione UX gia in uso per i separatori dimensionali
- introdurre un campo `descrizione` senza conversione `.` -> `x`
- applicare entrambi i filtri in combinazione con il filtro famiglia gia esistente
- aggiornare la resa UI della colonna lista articoli per mantenere leggibilita e chiarezza
- aggiornare documentazione minima della surface

### Out of Scope

- modifica del contratto backend della lista articoli
- introduzione di ricerca server-side
- redesign della surface `articoli`
- modifica della logica di dettaglio o dei fact canonici

## Constraints

- la ricerca per codice deve continuare a rispettare `DL-UIX-V2-004`
- la ricerca per descrizione non deve applicare conversioni dimensionali automatiche
- il comportamento dei due campi deve essere esplicito e leggibile per l'utente
- il filtro famiglia deve continuare a comporsi correttamente con i due nuovi campi

## Refresh / Sync Behavior

La vista `articoli` riusa il refresh semantico backend gia esistente (`refresh_articoli()`).

Questo task non modifica il comportamento di refresh.

## Acceptance Criteria

- la vista `articoli` mostra due campi distinti: `codice` e `descrizione`
- il campo `codice` mantiene la normalizzazione `.` -> `x` / `X` -> `x`
- il campo `descrizione` esegue ricerca testuale senza conversione dei separatori
- i due campi si combinano correttamente con il filtro famiglia
- `npm run build` passa

## Deliverables

- refinement UI della colonna lista articoli
- aggiornamento della logica di filtro client-side
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Questo task e un refinement UI localizzato della surface `articoli`.

Quindi:

- test frontend o app mirati se presenti
- build frontend obbligatoria
- niente full suite obbligatoria

## Verification Commands

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- nominare chiaramente i due campi (`Codice`, `Descrizione`)
- mantenere la ricerca codice ottimizzata per il caso dimensionale
- lasciare la descrizione come testo libero, senza normalizzazione invasiva
- evitare di introdurre altre semantiche implicite nella ricerca

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.
