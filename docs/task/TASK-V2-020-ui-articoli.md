# TASK-V2-020 - UI articoli

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-019-core-articoli.md`

## Goal

Implementare la prima surface browser `articoli` usando lo schema a `2 colonne`: lista articoli a sinistra e pannello di dettaglio read-only a destra.

## Context

Con `TASK-V2-019` la V2 introduce il primo Core `articoli`, che espone:

- lista articoli
- dettaglio articolo
- `display_label` o equivalente

Questo task deve tradurre quel modello applicativo nella prima surface browser coerente con la spec UIX `articoli`.

Nel primo slice UI:

- la colonna sinistra mostra codice articolo e descrizione
- la colonna destra mostra gli altri dati importati da Easy
- tutti i dati nel pannello di destra sono read-only

Il task non deve ancora introdurre:

- dati interni configurabili
- sync on demand dedicato

## Scope

### In Scope

- route/surface browser `articoli`
- layout persistente a `2 colonne` coerente con `UIX_SPEC_ARTICOLI`
- consumo dei read model Core introdotti da `TASK-V2-019`
- campo ricerca articolo
- normalizzazione della ricerca articolo coerente con `DL-UIX-V2-004`
- lista articoli a sinistra con:
  - `codice_articolo`
  - `descrizione_1`
- selezione articolo -> caricamento dettaglio a destra
- pannello di dettaglio read-only con gli altri dati importati da Easy

### Out of Scope

- dati interni configurabili dell'articolo
- sync on demand
- scheduler
- accesso diretto ai target `sync_*`
- nuovi campi Easy non presenti nel Core slice

## Constraints

- la UI deve consumare solo contratti backend/Core, non mirror sync
- la colonna sinistra deve essere scrollabile in modo indipendente
- il campo ricerca deve accettare anche varianti come `8.7.40` e normalizzarle verso `8x7x40`
- i dati Easy nel pannello di destra devono essere mostrati come read-only
- il task non deve introdurre logica di dominio o join nel frontend

## Acceptance Criteria

- esiste una route/surface browser `articoli` integrata nel layout applicativo
- la colonna sinistra mostra lista articoli con `codice_articolo` e `descrizione_1`
- la ricerca articolo funziona su codice e descrizione
- la ricerca normalizza input tipo `8.7.40` in modo coerente con `DL-UIX-V2-004`
- la colonna sinistra resta scrollabile indipendentemente
- la colonna destra mostra il dettaglio read-only dell'articolo selezionato
- la UI gestisce correttamente gli stati vuoti guidati:
  - nessun articolo selezionato
- `npm run build` passa senza errori

## Deliverables

- componenti frontend della surface `articoli`
- integrazione route/navigation nel layout esistente
- eventuali test frontend o smoke test coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
docker compose -f ../infra/docker/docker-compose.db.yml up -d
cp .env.example .env
alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
```

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- trattare `UIX_SPEC_ARTICOLI.md` come target UI del primo slice
- mantenere la colonna sinistra molto leggibile e orientata alla scansione rapida
- non riempire il pannello di destra di controlli editabili: in questo slice e solo dettaglio read-only
- separare chiaramente logica di normalizzazione ricerca e rendering del dettaglio

---

## Completion Notes

### Summary

Implementata la prima surface browser `articoli` a 2 colonne (UIX_SPEC_ARTICOLI.md). Backend: router `/api/produzione/articoli` e `/api/produzione/articoli/{codice}` che espone il Core `articoli` (TASK-V2-019). Frontend: `ProduzioneHome.tsx` con `ColonnaArticoli` (lista scrollabile, ricerca normalizzata DL-UIX-V2-004) e `ColonnaDettaglio` (pannello read-only). La normalizzazione ricerca trasforma `.` in `x`, normalizza spazi intorno a separatori dimensionali e usa confronto case-insensitive. Navigazione contestuale `produzione → Articoli` aggiunta in `SURFACE_FUNCTIONS` (AppShell) e route `/produzione/articoli` + redirect da `/produzione` in `App.tsx`.

### Files Changed

- `src/nssp_v2/core/articoli/__init__.py` — aggiunta API pubblica package (era vuoto)
- `src/nssp_v2/app/api/produzione.py` — router FastAPI: `GET /api/produzione/articoli`, `GET /api/produzione/articoli/{codice}`
- `src/nssp_v2/app/main.py` — incluso `produzione.router`
- `frontend/src/types/api.ts` — aggiunto `ArticoloItem` e `ArticoloDetail`
- `frontend/src/pages/surfaces/ProduzioneHome.tsx` — surface 2 colonne: `ColonnaArticoli` + `ColonnaDettaglio`, funzione `normalizeSearch` (DL-UIX-V2-004)
- `frontend/src/components/AppShell.tsx` — aggiunta voce `produzione: [{ path: '/produzione/articoli', label: 'Articoli' }]` in `SURFACE_FUNCTIONS`
- `frontend/src/App.tsx` — route `/produzione/articoli` + redirect da `/produzione`

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 8.01s — 0 errori TypeScript |
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 229 passed in 3.77s |

### Assumptions

- La ricerca è locale (client-side), coerente con DL-UIX-V2-004 §4 che ammette normalizzazione nel frontend quando il filtro è UI-driven. Se in futuro la ricerca verrà delegata al backend, la stessa logica `normalizeSearch` dovrà essere replicata nel contratto di query.
- `get_articolo_detail` ritorna anche articoli `attivo=False` (navigazione diretta per codice). Se necessario restringere al solo attivo, sarà un adeguamento futuro.
- I campi numerici (`peso_grammi`, `quantita_*`) sono esposti come `string | null` nel tipo TypeScript perché Pydantic serializza `Decimal` come stringa JSON. La visualizzazione è testuale, non richiede parsing numerico.
- Nessun sync on demand in questo task (out of scope — TASK-V2-019/sync on demand separato).

### Known Limits

- Nessuna freshness bar nella surface articoli: il sync on demand `articoli` verrà in un task successivo.
- La colonna destra mostra tutti i campi sincronizzati; una selezione curata per la UI finale avverrà nei task successivi del Core/produzione.

### Follow-ups

- Sync on demand `articoli` (trigger backend + freshness bar in ProduzioneHome)
- Dati interni configurabili articolo (secondo DL-ARCH-V2-013 §8, solo quando emergerà logica reale)
- Eventuale aggiornamento UIX_SPEC_ARTICOLI.md da `Draft` a `In Use` dopo validazione

## Completed At

2026-04-07

## Completed By

Claude Code
