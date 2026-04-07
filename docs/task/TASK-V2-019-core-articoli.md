# TASK-V2-019 - Core articoli

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
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`

## Goal

Implementare il primo Core `articoli` come proiezione applicativa dei dati sincronizzati in `sync_articoli`, cosi da alimentare la futura UI senza esporre direttamente il mirror tecnico.

## Context

Dopo la sync reale `articoli`, il passo corretto e introdurre un Core minimale che:

- legga solo da `sync_articoli`
- esponga lista e dettaglio articolo
- resti inizialmente vicino ai campi sincronizzati
- non introduca ancora dati interni non necessari

Il task non deve ancora implementare la UI `articoli`.
Deve preparare il contratto Core che la UI consumera.

## Scope

### In Scope

- struttura Core dedicata al slice `articoli`
- read model Core per:
  - lista articoli
  - dettaglio articolo
- eventuale campo sintetico `display_label` o equivalente
- query/backend contract coerente con `DL-ARCH-V2-013`
- test backend sul comportamento del Core `articoli`
- aggiornamento documentazione tecnica se necessario

### Out of Scope

- UI `articoli`
- dati interni configurabili dell'articolo
- scheduler
- trigger `sync on demand`
- nuove sync unit

## Constraints

- il Core legge solo da `sync_articoli`
- il Core non scrive mai nel target `sync_articoli`
- il primo slice puo esporre tutti i campi sincronizzati oggi utili alla UI
- la UI futura non deve essere costretta a leggere il mirror sync
- nessun dato interno va introdotto in questo task se non strettamente necessario

## Acceptance Criteria

- esiste un read model Core per la lista articoli
- esiste un read model Core per il dettaglio articolo
- il Core espone un campo sintetico di presentazione tipo `display_label`
- il Core usa `sync_articoli` come unica fonte dati
- i test backend verificano almeno:
  - lista articoli
  - dettaglio articolo
  - fallback di `display_label`
  - separazione tra mirror sync e contratto Core

## Deliverables

- moduli Core per il slice `articoli`
- test backend del Core `articoli`
- eventuale router/backend contract se necessario al solo scopo di esporre i read model
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
```

Database:

```bash
docker compose -f infra/docker/docker-compose.db.yml up -d
cd backend
cp .env.example .env
alembic upgrade head
```

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica strutturale esplicita sui moduli Core introdotti, ad esempio:

```bash
cd backend
python -c "from nssp_v2.core.articoli import ...; print('core articoli OK')"
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il Core come layer di proiezione applicativa, non come secondo mirror opaco
- esporre un `display_label` deterministico basato sulle descrizioni disponibili
- non introdurre ancora entita interne o tabelle di configurazione se non servono davvero
- se serve un endpoint backend, mantenerlo stretto e orientato ai read model, non alla UI finale completa

---

## Completion Notes

### Summary

Introdotto il primo Core slice `articoli` come proiezione applicativa di `sync_articoli` (DL-ARCH-V2-013). Due read model frozen Pydantic: `ArticoloItem` per la lista (con `display_label`) e `ArticoloDetail` per il dettaglio (tutti i campi sincronizzati). Due query Core: `list_articoli` (attivi, ordinati per codice) e `get_articolo_detail` (None se non trovato). `display_label` deterministica: `desc1 + " " + desc2` → `desc1` → `codice_articolo`. Nessun dato interno introdotto (DL-ARCH-V2-013 §8). Il Core non scrive mai in `sync_articoli`.

### Files Changed

- `src/nssp_v2/core/articoli/__init__.py` — package
- `src/nssp_v2/core/articoli/read_models.py` — `ArticoloItem` e `ArticoloDetail` (frozen Pydantic)
- `src/nssp_v2/core/articoli/queries.py` — `_compute_display_label`, `list_articoli`, `get_articolo_detail`
- `tests/unit/test_core_articoli_read_models.py` — 14 test unit: struttura read model, display_label varianti
- `tests/core/test_core_articoli.py` — 16 test integrazione: lista, dettaglio, fallback, separazione Core/sync

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 229 passed in 3.95s |
| `python -c "from nssp_v2.core.articoli.read_models import ...; from nssp_v2.core.articoli.queries import ..."; print('core articoli OK')` | Claude Code (agente) | backend V2 locale | core articoli OK |

### Assumptions

- `get_articolo_detail` ritorna il dettaglio anche per articoli `attivo=False`: il dettaglio è un accesso diretto per codice, la lista invece filtra solo gli attivi. Comportamento coerente con il pattern clienti/destinazioni.
- `display_label` usa `strip()` sui valori prima della composizione: una stringa di soli spazi è trattata come vuota e il fallback scatta correttamente.
- Nessun router HTTP è introdotto in questo task (out of scope — verrà nel task UI/surface articoli).

### Known Limits

- Il Core `articoli` non ha ancora un router HTTP esposto: il contratto esiste ma non è ancora consumabile via API. Il task successivo (UI surface articoli) introduce l'endpoint.
- Nessuna configurazione interna articolo nel primo slice (DL-ARCH-V2-013 §8 esplicito).

### Follow-ups

- Surface UI `articoli` (2 colonne, ricerca normalizzata DL-UIX-V2-004, freshness bar)
- Sync on demand `articoli` (trigger backend + endpoint + UI refresh)
- Eventuale router `/api/produzione/articoli` come contratto HTTP del Core

## Completed At

2026-04-07

## Completed By

Claude Code
