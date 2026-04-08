# TASK-V2-025 - UI tabella famiglia articoli

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
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-023-ui-famiglia-articoli.md`

## Goal

Introdurre una UI dedicata alla tabella `famiglie articolo`, per visualizzare e gestire il catalogo interno delle famiglie usato dalla surface `articoli`.

## Context

La V2 ha gia:

- introdotto il catalogo interno `famiglia articolo`
- collegato la famiglia ai singoli articoli
- reso configurabile la famiglia nel dettaglio articolo

Serve ora una vista dedicata al catalogo stesso, cosi da poter governare le famiglie come tabella interna di riferimento invece di trattarle solo come valori statici nascosti dietro il dettaglio articolo.

Questo task riguarda la UI e l'eventuale contratto backend strettamente necessario a leggere o gestire la tabella famiglie.

## Scope

### In Scope

- route o funzione dedicata per `famiglie articolo`
- lista/tabella delle famiglie esistenti
- visualizzazione almeno dei campi:
  - `code`
  - `label`
  - `description` se presente
  - `is_active`
  - `sort_order` se presente
- eventuale supporto a creazione/modifica se il backend gia lo consente o se viene introdotto in modo minimo e coerente
- integrazione della funzione nella navigazione contestuale della surface `produzione`
- aggiornamento minimo della spec o delle guide se la UI introduce un pattern stabile utile

### Out of Scope

- redesign generale della surface `articoli`
- modifica massiva delle famiglie sugli articoli
- nuove classificazioni interne oltre alla famiglia
- scheduler
- sync on demand

## Constraints

- la UI deve consumare solo contratti backend/Core
- la gestione della tabella famiglie deve restare separata dalla configurazione del singolo articolo
- se il backend non supporta ancora CRUD completo, il task puo fermarsi a una vista read-only o a un sottoinsieme minimo coerente
- il task non deve introdurre un nuovo DL salvo emerga un concetto strutturale nuovo

## Acceptance Criteria

- esiste una vista o funzione dedicata alle `famiglie articolo`
- la UI mostra il catalogo famiglie in forma chiara e leggibile
- la funzione e raggiungibile dalla navigazione `produzione`
- `npm run build` passa senza errori
- se vengono introdotte azioni di modifica, sono coerenti col contratto backend e con il perimetro del task

## Deliverables

- UI dedicata alla tabella `famiglie articolo`
- eventuale adeguamento backend minimo se necessario a supportare la vista
- eventuali test frontend o backend coerenti col task
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

e con almeno una verifica combinata coerente col flusso, ad esempio:

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

- mantenere questa vista come gestione del catalogo, non del singolo articolo
- privilegiare una tabella semplice e leggibile
- se il backend supporta solo lettura, partire da una vista read-only e rinviare CRUD completo
- integrare la funzione nella navigazione `produzione` in modo coerente con il pattern contestuale gia introdotto

---

## Completion Notes

### Summary

Introdotta la vista di gestione del catalogo `famiglie articolo` nella surface produzione.
Nuovo endpoint `GET /api/produzione/famiglie/catalog` che restituisce tutte le famiglie
(attive e inattive) con conteggio articoli assegnati. Nuova pagina `FamigliePage` con
tabella semplice. Voce "Famiglie" aggiunta alla navigazione contestuale produzione.

### Files Changed

**Backend (modificati):**
- `src/nssp_v2/core/articoli/read_models.py` — aggiunto `FamigliaRow` (tutte + `is_active` + `n_articoli`)
- `src/nssp_v2/core/articoli/queries.py` — aggiunta `list_famiglie_catalog` (con COUNT via GROUP BY su `core_articolo_config`)
- `src/nssp_v2/core/articoli/__init__.py` — esportati `FamigliaRow`, `list_famiglie_catalog`
- `src/nssp_v2/app/api/produzione.py` — aggiunto `GET /produzione/famiglie/catalog`
- `src/nssp_v2/app/services/admin_policy.py` — fix warning: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT` (starlette aggiornato)

**Frontend (nuovi):**
- `src/pages/surfaces/FamigliePage.tsx` — tabella read-only con colonne: ordine, codice, label, articoli, stato

**Frontend (modificati):**
- `src/types/api.ts` — aggiunto `FamigliaRow`
- `src/App.tsx` — aggiunta route `/produzione/famiglie` → `FamigliePage`
- `src/components/AppShell.tsx` — aggiunta voce `Famiglie` nella nav contestuale produzione

### Dependencies Introduced

Nessuna.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code | Windows / .venv | 244 passed, 0 warnings |
| `npm run build` | Claude Code | Windows / Node | verde, 97 moduli, 275 kB JS |

### Assumptions

- La vista è read-only nel primo slice; il CRUD famiglie (add/disable) è out of scope.
- L'endpoint `GET /famiglie` (picker) rimane invariato e ritorna solo le attive.
- L'endpoint `GET /famiglie/catalog` ritorna tutte (attive + inattive) per la gestione.
- `n_articoli` conta solo articoli con `famiglia_code` assegnato in `core_articolo_config`
  (non articoli Easy totali per famiglia, che non ha senso senza regola automatica).

### Known Limits

- La tabella non è ordinabile né filtrabile dalla UI (5 famiglie — non necessario).
- Non c'è azione di disattivazione/riattivazione dalla UI.

### Follow-ups

- Azioni di modifica `label` o toggle `is_active` se richieste.
- Eventuale aggiunta famiglia con form minimo.

## Completed At

2026-04-07

## Completed By

Claude Code
