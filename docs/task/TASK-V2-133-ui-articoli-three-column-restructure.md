# TASK-V2-133 - UI articoli three-column restructure

## Status
Completed

## Date
2026-04-16

## Owner
Codex

## Source Documents

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/task/TASK-V2-132-ui-articoli-proposal-logic-friendly-labels.md`

## Goal

Ristrutturare la schermata `articoli` da layout a `2 colonne` a layout a `3 colonne`, per separare in modo piu chiaro:

- lista articoli
- stato/read-only dell'articolo
- configurazione dell'articolo

## Context

La schermata `articoli` sta diventando sempre piu densa e oggi accorpa nello stesso pannello:

- anagrafica read-only
- fact quantitativi operativi
- metriche stock
- configurazioni planning
- configurazioni stock
- configurazioni proposal

Questa densita sta riducendo:

- leggibilita
- separazione semantica tra facts e config
- scalabilita della UI per i prossimi stream

## Scope

- passare la schermata `articoli` a un layout a `3 colonne`
- mantenere invariata la colonna sinistra:
  - lista articoli
  - ricerca
  - filtri
- introdurre una colonna centrale read-only, con blocchi compatti
- introdurre una colonna destra dedicata alle configurazioni, organizzata in schede/sezioni

## Proposed UI Structure

### Colonna sinistra

- invariata rispetto al pattern attuale
- elenco articoli
- ricerca e filtri

### Colonna centrale - Stato articolo read-only

Blocchi suggeriti:

- `Anagrafica`
- `Giacenza / Impegni / Disponibilita`
- `Scorte / Capacity / Target`
- `Proposal context` se utile

Questa colonna deve restare orientata ai dati e non alle azioni di configurazione.

### Colonna destra - Configurazione

Schede/sezioni suggerite:

- `Planning`
- `Scorte`
- `Proposal`
- `Materiale / Barra` quando pertinente

Regola:

- la colonna destra governa l'articolo
- la colonna centrale descrive lo stato dell'articolo

## Out of Scope

- modifica del Core `articoli`
- cambi dei contratti backend
- refactor dei singoli task funzionali proposal/planning/stock

## Constraints

Regole minime:

- la colonna centrale deve essere solo read-only
- la colonna destra deve contenere solo configurazione/azioni coerenti
- evitare proliferazione eccessiva di tab secondarie
- il nuovo layout deve mantenere leggibilita anche su viewport piu stretti

Vincolo architetturale:

- facts e config non vanno piu mescolati nello stesso blocco principale

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
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 06 - Multi-colonna standard per catalogo + dettaglio`
- `Pattern 12 - Separare facts read-only da configurazione`

## Refresh / Sync Behavior

- `La vista riusa il refresh semantico backend esistente`

Nessun nuovo refresh on demand.

## Acceptance Criteria

- la schermata `articoli` usa un layout a `3 colonne`
- la colonna centrale rende piu leggibili i dati read-only
- la colonna destra separa la configurazione in sezioni/schede coerenti
- i dati read-only e la configurazione non sono piu mescolati nello stesso blocco
- la build frontend resta verde

## Deliverables

- refactor UI `articoli`
- eventuale aggiornamento della spec UIX del caso `articoli`

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

## Implementation Log

### `frontend/src/pages/surfaces/ProduzioneHome.tsx`

Approccio: tutto lo state e gli handler di `ColonnaDettaglio` restano invariati.
Solo il return JSX viene ristrutturato da un'unica colonna scrollabile a due pannelli affiancati.

**Layout esterno** — invariato:
```
ColonnaArticoli (w-72) | ColonnaDettaglio (flex-1, internamente 2 colonne)
```

**Layout interno di ColonnaDettaglio** — nuovo:
```
div.flex-1.flex.overflow-hidden
  ├── div.w-80.border-r  (centro — read-only)
  └── div.flex-1         (destra — config)
```

**Colonna centrale (w-80, read-only):**
- Header: `display_label` + `codice_articolo` mono
- **Anagrafica**: tutti i dati Easy in `<dl>` compatta
- **Giacenza / Impegni / Disponibilità**: grid 2×2 con card compatte (`rounded border p-2`)
- **Scorte / Capacity / Target**: grid compatta con colori (blue=target, amber=trigger) — solo se `planning_mode === 'by_article'`
- **Proposal context**: logica effettiva con label human-friendly + key mono + raw_bar_length_mm se presente

Helper `fmtQty(v, decimals)` locale per evitare ripetizioni nel formato numeri.

**Colonna destra (flex-1, configurazione):**
- **Planning**: famiglia, perimetro, modalità, gestione scorte — con tutti i select + feedback salvataggio
- **Scorte**: form override (mesi, trigger, capacity) — solo se `planning_mode === 'by_article'`
- **Proposal**: select logica con label, textarea params JSON con auto-populate template, form raw bar length (condizionale a famiglia)

Principio rispettato: facts read-only e configurazione non sono più mescolati nello stesso blocco.

**Esito build:** `✓ built in 3.55s`, exit code `0`.
