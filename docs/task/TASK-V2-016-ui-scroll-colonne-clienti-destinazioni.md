# TASK-V2-016 - UI scroll colonne clienti destinazioni

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
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`

## Goal

Raffinare la surface clienti/destinazioni rendendo le colonne scrollabili in modo indipendente, con priorita alla colonna clienti a sinistra.

## Context

La prima implementazione della surface clienti/destinazioni e stata completata in `TASK-V2-013`.

Nel completion report e gia emerso un limite concreto:

- le colonne non hanno ancora un comportamento di altezza/scroll pienamente robusto
- la colonna clienti a sinistra diventa troppo lunga e penalizza l'uso della schermata

Serve quindi un task UI dedicato di refinement, senza mischiarlo con Core, sync o logiche di dominio.

## Scope

### In Scope

- rendere scrollabile in modo indipendente la colonna clienti
- rendere scrollabili in modo coerente anche colonna destinazioni e dettaglio, se necessario
- migliorare il comportamento di altezza del layout della surface
- mantenere usabile la ricerca clienti anche con liste lunghe
- rifinire overflow, altezze e contenitori della pagina in coerenza con `AppShell`

### Out of Scope

- modifiche al Core
- modifiche al sync
- trigger sync on demand
- cambi di contenuto dei read model
- redesign visivo completo della surface

## Constraints

- il layout a 3 colonne deve restare coerente con `DL-UIX-V2-002`
- il comportamento scroll deve essere prevedibile sia su desktop che su viewport piu basse
- la colonna clienti deve restare navigabile e leggibile anche con molti record
- il task non deve introdurre logica di business nel frontend

## Acceptance Criteria

- la colonna clienti a sinistra e scrollabile indipendentemente
- il layout non forza piu una pagina unica troppo lunga per consultare la lista clienti
- filtro clienti e selezione restano utilizzabili durante lo scroll
- il comportamento della surface resta coerente con il frame applicativo esistente
- `npm run build` passa senza errori

## Deliverables

- aggiornamenti frontend della surface clienti/destinazioni
- eventuali piccoli aggiustamenti del layout condiviso se necessari al solo scopo di supportare scroll corretto
- eventuale aggiornamento di:
  - `docs/decisions/UIX/DL-UIX-V2-002.md`

## Environment Bootstrap

Frontend:

```bash
cd frontend
npm install
```

Backend opzionale per smoke reale:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
docker compose -f ../infra/docker/docker-compose.db.yml up -d
cp .env.example .env
alembic upgrade head
python scripts/seed_initial.py
```

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

Se viene fatta verifica manuale della surface, riportare anche:

- viewport usata
- esito dello scroll sulla colonna clienti

## Implementation Notes

Direzione raccomandata:

- trattare la colonna clienti come lista indipendente con area scroll interna
- evitare di risolvere il problema solo aumentando l'altezza globale della pagina
- se necessario, allineare il container principale a `h-screen` o equivalente, ma senza rompere il frame esistente

---

## Completion Notes

### Summary

Reso il layout a 3 colonne pienamente scrollabile in modo indipendente. Il problema era che `min-h-full` e `overflow-auto` sul contenitore non creavano un contesto di altezza limitata per i figli — le colonne crescevano con il contenuto invece di scrollare. Soluzione: `AppShell` passa da `min-h-screen` a `h-screen` e da `overflow-auto` a `overflow-hidden` sull'area contenuto; `LogisticaHome` usa `h-full` invece di `min-h-full` sul root, `overflow-hidden` sul contenitore delle colonne, e `overflow-hidden` sui container delle singole colonne (mentre le liste interne mantengono `flex-1 overflow-y-auto`).

### Files Changed

- `frontend/src/components/AppShell.tsx` — outer div: `min-h-screen` → `h-screen`; content div: `overflow-auto` → `overflow-hidden`
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — root: `min-h-full` → `h-full`; inner flex: aggiunto `overflow-hidden`; ColonnaClienti e ColonnaDestinazioni container: aggiunto `overflow-hidden`

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 3.38s — 0 errori TypeScript |

### Assumptions

- La sidebar di `AppShell` non necessita di scroll proprio (voci limitate); `overflow-y-auto` già presente sulla `<nav>` garantisce comportamento corretto se le voci crescono.
- `h-screen` è appropriato per un'applicazione desktop-first. Su mobile/viewport molto basse il layout a 3 colonne richiederebbe un redesign separato (fuori scope).

### Known Limits

- Nessuna verifica manuale eseguita (solo build). Il comportamento scroll è corretto per costruzione (pattern `h-screen / flex / overflow-hidden / flex-1 overflow-y-auto` consolidato).
- Su viewport con altezza < 400px le colonne potrebbero risultare molto strette ma non si rompe il layout.

### Follow-ups

- eventuali ulteriori refinement responsive della surface clienti/destinazioni

## Completed At

2026-04-07

## Completed By

Claude Code
