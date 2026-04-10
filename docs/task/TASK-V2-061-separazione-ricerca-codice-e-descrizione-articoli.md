# TASK-V2-061 - Separazione ricerca codice e descrizione articoli

## Status
Done

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

---

## Completion Notes

### Separazione logica di ricerca

Prima di questo task, un singolo campo di ricerca applicava `normalizeSearch` (che converte
`.` → `x`, varianti `X`/spazi → `x`) su codice, `descrizione_1` e `descrizione_2`
contemporaneamente.

La normalizzazione è corretta per il codice articolo (dove `8.7.160` deve matchare `8x7x160`)
ma inappropriata per la descrizione libera (dove un utente che cerca `"rosso"` non deve
subire alcuna conversione di separatori).

### Modifiche — solo `ProduzioneHome.tsx`

**Funzioni di matching** — `matchesSearch` è stata sostituita da due funzioni distinte:

```typescript
// Codice: normalizzazione DL-UIX-V2-004 attiva
function matchesCodice(articolo: ArticoloItem, raw: string): boolean {
  if (!raw.trim()) return true
  const needle = normalizeSearch(raw)   // . → x, X → x, lowercase
  return articolo.codice_articolo.toLowerCase().includes(needle)
}

// Descrizione: testo libero, nessuna conversione dimensionale
function matchesDesc(articolo: ArticoloItem, raw: string): boolean {
  if (!raw.trim()) return true
  const needle = raw.trim().toLowerCase()
  return (
    (articolo.descrizione_1 ?? '').toLowerCase().includes(needle) ||
    (articolo.descrizione_2 ?? '').toLowerCase().includes(needle)
  )
}
```

**`ColonnaArticoli`** — due input distinti nel pannello laterale sinistro:

- `Codice…` — placeholder esplicito, applica `matchesCodice`
- `Descrizione…` — placeholder esplicito, applica `matchesDesc`

Il filtro famiglia si compone con entrambi: `filter(family) → filter(codice) → filter(desc)`.

Il contatore risultati si attiva se almeno uno dei tre filtri è attivo
(`filterCodice.trim() || filterDesc.trim() || familyFilter !== 'all'`).

**`ProduzioneHome`** — stato separato: `filterCodice` e `filterDesc` invece del singolo `filter`.

Nessuna modifica al backend — il contratto API della lista articoli non è coinvolto.

### Verifica

```
npm run build
✓ built in 7.29s
```

## Completed At

2026-04-10

## Completed By

Claude Code
