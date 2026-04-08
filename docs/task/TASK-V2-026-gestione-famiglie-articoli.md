# TASK-V2-026 - Gestione famiglie articoli

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
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-025-ui-tabella-famiglia-articoli.md`

## Goal

Consentire la gestione minima del catalogo `famiglie articolo`:

- inserimento di nuove famiglie
- modifica dello stato `attivo/disattivo`

## Context

La V2 ha gia introdotto:

- il catalogo interno `famiglie articolo`
- l'associazione articolo -> famiglia
- la futura vista dedicata alla tabella famiglie

Serve ora rendere il catalogo effettivamente gestibile nel sistema, senza fermarsi ai soli valori seedati.

Questo task deve restare stretto: non e ancora il CRUD completo del catalogo, ma il primo slice operativo per governarne l'evoluzione.

## Scope

### In Scope

- endpoint backend minimi per:
  - creare una nuova famiglia
  - aggiornare `is_active` di una famiglia esistente
- UI minima nella vista `famiglie articolo` per:
  - inserire una nuova famiglia
  - attivare/disattivare una famiglia esistente
- validazioni minime sul backend, ad esempio:
  - `code` univoco
  - `label` obbligatoria
- aggiornamento del catalogo mostrato nella UI dopo create/update

### Out of Scope

- delete fisica delle famiglie
- modifica arbitraria di tutti i campi
- bulk update massivo
- migrazioni o automazioni sugli articoli gia associati
- nuove classificazioni diverse dalla famiglia

## Constraints

- la gestione del catalogo deve restare separata dalla configurazione del singolo articolo
- il sistema deve poter distinguere chiaramente famiglie attive e inattive
- la disattivazione non deve cancellare lo storico ne rompere le associazioni esistenti
- il task non deve introdurre un nuovo DL salvo emerga un concetto strutturale nuovo

## Acceptance Criteria

- esiste un flusso backend per creare una nuova famiglia
- esiste un flusso backend per attivare/disattivare una famiglia
- la UI dedicata consente di creare una nuova famiglia
- la UI dedicata consente di cambiare lo stato attivo/inattivo
- il catalogo visualizzato si aggiorna coerentemente dopo le operazioni
- `npm run build` passa senza errori
- i test backend coprono almeno create e toggle attivo/disattivo

## Deliverables

- estensione backend per gestione minima del catalogo famiglie
- estensione UI della vista `famiglie articolo`
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

- mantenere il flusso semplice e amministrativo
- privilegiare `create + toggle active` rispetto a un CRUD largo
- mostrare chiaramente in UI se una famiglia e attiva o inattiva
- evitare che le famiglie inattive spariscano del tutto se sono gia usate da articoli esistenti

---

## Completion Notes

### Summary

Introdotta la gestione minima del catalogo famiglie: creazione e toggle is_active.
Backend con due nuovi comandi (`create_famiglia`, `toggle_famiglia_active`) con validazioni
e due nuovi endpoint REST. UI aggiornata con form di creazione inline e pulsante toggle
per riga. La lista si aggiorna localmente dopo ogni operazione senza reload.

### Files Changed

**Backend (modificati):**
- `src/nssp_v2/core/articoli/queries.py` — aggiunti `create_famiglia` (validazioni: code univoco, label non vuota, code non vuoto/blank) e `toggle_famiglia_active` (con count articoli nel risultato)
- `src/nssp_v2/core/articoli/__init__.py` — esportati `create_famiglia`, `toggle_famiglia_active`
- `src/nssp_v2/app/api/produzione.py` — aggiunti `CreateFamigliaRequest`, `POST /famiglie` (201), `PATCH /famiglie/{code}/active`

**Backend (nuovi):**
- `tests/core/test_core_gestione_famiglie.py` — 14 test: create (happy path, sort_order, persist, duplicato, label vuota, code vuoto, trimming), toggle (disattiva, riattiva, doppio, not found, n_articoli), catalog post-operazione

**Frontend (modificati):**
- `src/pages/surfaces/FamigliePage.tsx` — aggiunto `FormCreaFamiglia` (code, label, sort_order opzionale, validazione client lato submit), `RigaFamiglia` con stato toggling locale; aggiornamento lista ottimistico in `handleCreated` (con sort) e `handleToggled` (replace by code)

### Dependencies Introduced

Nessuna.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests/core/test_core_gestione_famiglie.py -q` | Claude Code | Windows / .venv | 14 passed |
| `python -m pytest tests -q` | Claude Code | Windows / .venv | 258 passed |
| `npm run build` | Claude Code | Windows / Node | verde, 97 moduli, 278 kB JS |

### Assumptions

- La disattivazione di una famiglia non rimuove le associazioni esistenti in `core_articolo_config` — la famiglia rimane visibile (con opacity ridotta) ma il picker articoli la esclude (filtra solo `is_active=True`).
- Il sort ottimistico in `handleCreated` usa `sort_order` nullo-last, poi `code` alfabetico — coerente con la query backend.
- `HTTP_422_UNPROCESSABLE_ENTITY` usato nel router per errori di validazione (starlette lo supporta ancora come alias).

### Known Limits

- Non c'è modifica della `label` o del `sort_order` di famiglie esistenti (out of scope).
- Il form non mostra un campo obbligatorio con asterisco — solo il comportamento (submit bloccato se vuoti).

### Follow-ups

- Modifica label/sort_order di famiglia esistente.
- Feedback visivo sulle righe inattive nel picker articoli (oggi spariscono — potrebbe confondere).

## Completed At

2026-04-07

## Completed By

Claude Code
