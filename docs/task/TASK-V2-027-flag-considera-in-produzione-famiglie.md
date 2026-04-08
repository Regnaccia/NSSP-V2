# TASK-V2-027 - Flag considera in produzione famiglie

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
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/task/TASK-V2-025-ui-tabella-famiglia-articoli.md`
- `docs/task/TASK-V2-026-gestione-famiglie-articoli.md`

## Goal

Aggiungere al catalogo `famiglie articolo` un flag booleano `considera_in_produzione` (`si/no`) e renderlo modificabile dalla UI dedicata.

## Context

La V2 sta consolidando il catalogo interno delle famiglie articolo come primo livello di classificazione operativa.

Serve introdurre un attributo semplice ma utile per gli step successivi:

- `considera_in_produzione`

Questo flag verra usato piu avanti come criterio di filtro e comportamento nella surface `produzione`, ma va introdotto gia ora nel modello e nella gestione UI del catalogo famiglie.

## Scope

### In Scope

- estensione backend del modello `famiglie articolo` con flag booleano `considera_in_produzione`
- migration o adeguamento persistence coerente
- default iniziale esplicito del flag
- esposizione del flag nei contratti backend rilevanti
- visualizzazione del flag nella UI tabella famiglie
- possibilita di modificare il flag dalla UI dedicata
- test backend minimi sul nuovo campo

### Out of Scope

- uso del flag come filtro nella lista articoli
- logiche automatiche di produzione
- nuovi flag o nuove classificazioni
- redesign della UI famiglie

## Constraints

- il flag appartiene al catalogo famiglie, non al singolo articolo
- il valore deve essere chiaramente visibile e modificabile nella UI
- il task non deve introdurre un nuovo DL salvo emerga un concetto strutturale nuovo
- la semantica del flag resta semplice: `si/no`, senza stati intermedi

## Acceptance Criteria

- esiste il campo `considera_in_produzione` nel catalogo famiglie
- il backend espone il flag nei contratti rilevanti
- la UI tabella famiglie mostra il flag
- la UI consente di modificarlo
- `npm run build` passa senza errori
- i test backend coprono almeno persistenza e aggiornamento del flag

## Deliverables

- estensione modello/backend famiglie
- migration o aggiornamento persistence
- aggiornamento UI della tabella famiglie
- test backend e, se sensato, smoke/frontend tests
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/roadmap/TASK_LOG.md`

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
cd backend
python -m pytest tests -q
```

e:

```bash
cd frontend
npm run build
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il nome del campo esplicito e coerente tra backend e UI
- scegliere un default semplice e documentarlo nelle `Completion Notes`
- usare un controllo UI chiaro, ad esempio toggle o checkbox
- non anticipare ancora il consumo del flag nelle query `articoli`

---

## Completion Notes

### Summary

Aggiunto il flag `considera_in_produzione` (boolean, default `False`) al modello `ArticoloFamiglia`.
Migration applicata. Il flag è esposto in `FamigliaRow`, modificabile via `PATCH /famiglie/{code}/considera-produzione`
(toggle) e visualizzato nella tabella famiglie come checkbox cliccabile.

### Files Changed

**Backend:**
- `src/nssp_v2/core/articoli/models.py` — aggiunta colonna `considera_in_produzione: Mapped[bool]`, default `False`
- `alembic/versions/20260407_008_famiglia_considera_produzione.py` — migration: `ALTER TABLE articolo_famiglie ADD COLUMN considera_in_produzione BOOLEAN NOT NULL DEFAULT FALSE`
- `src/nssp_v2/core/articoli/read_models.py` — aggiunto `considera_in_produzione: bool` a `FamigliaRow`
- `src/nssp_v2/core/articoli/queries.py` — aggiunta `toggle_famiglia_considera_produzione`; aggiornate `list_famiglie_catalog`, `create_famiglia`, `toggle_famiglia_active` per includere il campo
- `src/nssp_v2/core/articoli/__init__.py` — esportata `toggle_famiglia_considera_produzione`
- `src/nssp_v2/app/api/produzione.py` — aggiunto `PATCH /famiglie/{code}/considera-produzione`
- `tests/core/test_core_gestione_famiglie.py` — 6 nuovi test: default False, toggle on/off, doppio idempotente, not found, esposizione in catalog

**Frontend:**
- `src/types/api.ts` — aggiunto `considera_in_produzione: boolean` a `FamigliaRow`
- `src/pages/surfaces/FamigliePage.tsx` — colonna "In produzione" con checkbox; handler `handleToggleProd`; stato `togglingProd` locale

### Dependencies Introduced

Nessuna.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `alembic upgrade head` | Claude Code | Windows / .venv | migration 20260407008 applicata |
| `python -m pytest tests -q` | Claude Code | Windows / .venv | 267 passed |
| `npm run build` | Claude Code | Windows / Node | verde, 97 moduli, 279 kB JS |

### Assumptions

- Default `False`: per prudenza, nessuna famiglia è considerata in produzione finché non esplicitamente abilitata.
- Il flag viene esposto in `FamigliaRow` (vista gestione) ma non in `FamigliaItem` (picker articoli) — non necessario lì.
- Il consumo del flag nelle query articoli (filtro) è out of scope per questo task.

### Known Limits

- Il toggle non ha feedback testuale inline (solo cursor wait durante il salvataggio) — la checkbox si aggiorna visivamente all'arrivo della risposta.

### Follow-ups

- Filtrare la lista articoli o le commesse in base a `considera_in_produzione` della famiglia assegnata.

## Completed At

2026-04-07

## Completed By

Claude Code
