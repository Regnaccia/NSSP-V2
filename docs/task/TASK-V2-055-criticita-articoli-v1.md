# TASK-V2-055 - Criticita articoli V1

## Status
Done

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-049-core-availability.md`
- `docs/task/TASK-V2-050-availability-e-commitments-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-054-refresh-semantici-backend.md`

## Goal

Introdurre la prima vista operativa minima di `criticita articoli`, basata su una logica V1 semplice: articolo critico se `availability_qty < 0`.

## Context

La V2 ha ormai chiuso il primo modello quantitativo canonico:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

Con `DL-ARCH-V2-023` il progetto fissa che le logiche di dominio devono essere modellate come funzioni intercambiabili sui fact canonici, non come formule hardcoded sparse.

La prima applicazione naturale di questo principio e una vista operativa minima che renda immediatamente visibili gli articoli con disponibilita negativa.

Questa V1 deve restare volutamente semplice:

- nessuna logica di safety stock
- nessuna policy per famiglia
- nessuna aggregazione temporale
- nessuna distinzione avanzata per scenario

Serve prima di tutto a:

- validare il pattern `fact -> logic -> projection -> UI`
- dare una prima vista operativa utile
- creare una base su cui raffinare in seguito le logiche

## Scope

### In Scope

- introdurre una prima logica applicativa `criticita_articoli_v1`
- criterio V1:
  - articolo critico se `availability_qty < 0`
- introdurre un read model / query / projection dedicato alla lista degli articoli critici
- esporre una vista UI minima che mostri gli articoli critici
- campi minimi consigliati in lista:
  - `article_code`
  - `descrizione`
  - `famiglia` se disponibile
  - `inventory_qty`
  - `customer_set_aside_qty`
  - `committed_qty`
  - `availability_qty`
- ordinamento consigliato:
  - disponibilita crescente (i peggiori sopra)
- aggiornare la documentazione minima della nuova vista

### Out of Scope

- safety stock / scorta minima
- policy per famiglia
- uso del flag `considera_in_produzione`
- slice temporali
- aggregazioni per orizzonte temporale
- suggerimenti automatici di acquisto o produzione
- ATP
- dashboard complessa o KPI aggregati

## Constraints

- la logica V1 deve vivere come funzione o livello separato dai fact canonici
- la UI non deve ricalcolare localmente la criticita
- il modello deve poter evolvere in futuro cambiando la logica senza rompere i fact
- la vista puo essere minimale e consultiva
- evitare da subito hardcode della logica in componenti UI o router API

## Acceptance Criteria

- esiste una prima logica V1 di criticita articoli basata su `availability_qty < 0`
- la lista mostra solo articoli con disponibilita negativa
- la lista e ordinata con i casi peggiori in cima
- il contratto usato dalla UI non hardcoda la formula nel frontend
- la nuova vista e navigabile dalla surface appropriata
- la documentazione minima della vista e aggiornata

## Deliverables

- logica V1 `criticita articoli`
- projection/read model per la lista critica
- vista UI minimale per articoli critici
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Questo task introduce la prima logica operativa vera ma resta una V1 stretta e verticale.

Quindi:

- test mirati sul read model / logica di criticita
- build frontend se viene toccata la navigazione o la nuova vista
- niente full suite obbligatoria in questo task

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- tenere la logica V1 volutamente banale e difendibile
- privilegiare una vista consultiva semplice
- non anticipare ancora policy future
- preparare il terreno a una futura evoluzione verso:
  - safety stock
  - policy per famiglia
  - filtri per dominio o famiglia
  - slice temporali

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Struttura implementata

Il task introduce il pattern `fact -> logic -> projection -> UI` (DL-ARCH-V2-023) completo:

**Backend — Core layer (`core/criticita/`)**

- `logic.py` (già creato nella sessione precedente): `ArticleLogicContext` frozen dataclass +
  `is_critical_v1(ctx)` pura e intercambiabile — V1 = `availability_qty < 0`
- `read_models.py` (nuovo): `CriticitaItem` frozen Pydantic model con tutti i campi quantitativi
  (`inventory_qty`, `customer_set_aside_qty`, `committed_qty`, `availability_qty`) e campi di
  presentazione (`display_label`, `famiglia_label`)
- `queries.py` (nuovo): `list_criticita_v1(session)` — SQL filtra i candidati con
  `availability_qty < 0` (JOIN `sync_articoli` per descrizioni, `core_articolo_config` +
  `articolo_famiglie` per famiglia), Python applica `is_critical_v1` come validazione del criterio,
  ordinamento `availability_qty ASC` (i peggiori sopra)
- `__init__.py` (aggiornato): espone `ArticleLogicContext`, `CriticitaItem`, `is_critical_v1`,
  `list_criticita_v1`

**Backend — App layer**

- `app/api/produzione.py`: aggiunto `GET /api/produzione/criticita -> list[CriticitaItem]` —
  endpoint thin, chiama `list_criticita_v1(session)` direttamente

**Frontend**

- `types/api.ts`: aggiunto `CriticitaItem` interface con tutti i campi (quantitativi come `string`,
  consistent con il contratto Pydantic/JSON decimali)
- `pages/surfaces/CriticitaPage.tsx` (nuovo): vista tabellare a larghezza piena — header con badge
  conteggio critico/verde e pulsante "Aggiorna", tabella sticky con colonne codice / descrizione /
  famiglia / giacenza / appartata / impegnata / disponibilita (in rosso se negativa)
- `App.tsx`: aggiunto route `/produzione/criticita` con `ProtectedRoute roles=['produzione']`
- `components/AppShell.tsx`: aggiunto `{ path: '/produzione/criticita', label: 'Criticità' }` in
  `SURFACE_FUNCTIONS.produzione`

### Scelte implementative

- **SQL + Python per la logica**: il filtro SQL `availability_qty < 0` riduce il dataset a DB;
  `is_critical_v1` applicata in Python è il punto di intercambio (DL-ARCH-V2-023 §Regola 3) —
  passare a una logica più ricca (safety stock, policy famiglia) richiede solo sostituire la funzione
- **Nessuna riutilizzazione di `_compute_display_label` dall'articoli**: la helper interna è
  privata; copiata minimalmente in `queries.py` per mantenere l'indipendenza del slice
- **Vista tabellare flat**: non c'è un "dettaglio" da aprire per un articolo critico; la 2-colonna
  sarebbe sovrabbondante; layout tabella sticky a tutta altezza è più leggibile per scanning rapido
- **`CriticitaItem.availability_qty` in rosso**: unica colorazione semantica nella UI — il dato
  più urgente va evidenziato senza serve tutta una dashboard

### Verifica

```
python -m pytest tests/core tests/app -q
280 passed in 4.60s

npm run build
✓ built in 7.33s
```

Test aggiunto: `tests/core/test_core_criticita.py` — 16 test che coprono:
- `is_critical_v1`: negativo, zero, positivo, None, molto negativo
- `list_criticita_v1`: tabella vuota, solo non critici, articolo critico, ordinamento crescente,
  mix critici/non, arricchimento descrizione e display_label, famiglia, campi quantitativi

## Completed At

2026-04-10

## Completed By

Claude Code
