# TASK-V2-022 - Famiglia articoli

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
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
- `docs/task/TASK-V2-019-core-articoli.md`
- `docs/task/TASK-V2-020-ui-articoli.md`

## Goal

Introdurre la prima entita interna del dominio `articoli`: `famiglia articolo`, con catalogo controllato V2 e associazione configurabile tra articolo e famiglia.

## Context

Il Core `articoli` e nato come proiezione applicativa dei dati sincronizzati da Easy.

Serve ora il primo passo oltre il read-only puro:

- un catalogo interno di famiglie articolo
- un collegamento tra articolo e famiglia
- esposizione della famiglia nel contratto Core/backend

Questo task non deve ancora introdurre automazioni o modellazioni piu profonde.

## Scope

### In Scope

- tabella interna delle famiglie articolo
- seed iniziale del catalogo con i valori:
  - `materia_prima`
  - `articolo_standard`
  - `speciale`
  - `barre`
  - `conto_lavorazione`
- riferimento di famiglia sugli articoli Core o su tabella di collegamento coerente col modello scelto
- aggiornamento del contratto Core/API per esporre:
  - `famiglia_code`
  - `famiglia_label`
- endpoint backend minimo per leggere il catalogo famiglie
- endpoint backend minimo per associare o aggiornare la famiglia di un articolo
- test backend coerenti con il nuovo perimetro
- aggiornamento documentazione minima se cambiano contratti o bootstrap

### Out of Scope

- editor completo del catalogo famiglie
- cancellazione o CRUD completo delle famiglie
- regole automatiche di assegnazione
- bulk update massivo
- scheduler
- sync on demand `articoli`
- ulteriori dati interni diversi dalla famiglia

## Constraints

- la famiglia e un dato interno V2 e non deve essere scritto nel mirror `sync_articoli`
- il catalogo iniziale e controllato dal sistema
- l'associazione famiglia -> articolo puo essere nullable nel primo slice
- la UI `articoli` puo continuare a funzionare anche senza famiglia assegnata
- il task deve preservare la separazione `sync -> core -> ui`

## Acceptance Criteria

- esiste una persistenza interna dedicata al catalogo `famiglie articolo`
- il catalogo iniziale contiene i 5 valori richiesti
- gli articoli possono essere associati a una famiglia interna
- il contratto Core/API espone la famiglia articolo dove rilevante
- esiste almeno un endpoint backend per leggere il catalogo famiglie
- esiste almeno un endpoint backend per impostare o aggiornare la famiglia di un articolo
- i test backend verificano:
  - presenza seed iniziale
  - associazione articolo -> famiglia
  - esposizione della famiglia nel contratto Core/API
  - nessuna write nel layer `sync`

## Deliverables

- modelli e migration per `famiglia articolo`
- seed del catalogo iniziale
- aggiornamento Core/API `articoli`
- endpoint backend minimi per leggere e associare la famiglia
- test backend
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`

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

e con almeno una verifica backend esplicita del catalogo o dell'associazione, ad esempio:

```bash
cd backend
python -c "from nssp_v2.core.articoli import ...; print('famiglie articoli OK')"
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- privilegiare un modello semplice e stabile rispetto a un design troppo astratto
- usare codici stabili interni per le famiglie
- tenere il catalogo iniziale seedato e controllato
- introdurre la prima modifica UI solo se minima e necessaria a rendere utilizzabile l'associazione

---

## Completion Notes

### Summary

Introdotta la prima entità interna del dominio `articoli`: catalogo `ArticoloFamiglia` con 5 valori seedati,
tabella di collegamento `CoreArticoloConfig` (keyed su `codice_articolo`), query Core aggiornate con LEFT OUTER JOIN,
contratto Core/API esteso con `famiglia_code` + `famiglia_label`, endpoint backend per leggere il catalogo e
associare/rimuovere la famiglia. UI aggiornata minimalmente con select inline nel pannello dettaglio.

### Files Changed

**Backend (nuovi):**
- `src/nssp_v2/core/articoli/models.py` — `ArticoloFamiglia`, `CoreArticoloConfig`
- `alembic/versions/20260407_007_famiglia_articoli.py` — migration + seed 5 famiglie
- `tests/core/test_core_famiglia_articoli.py` — 15 test di integrazione

**Backend (modificati):**
- `src/nssp_v2/core/articoli/read_models.py` — aggiunti `famiglia_code`, `famiglia_label` a `ArticoloItem` e `ArticoloDetail`; aggiunto `FamigliaItem`
- `src/nssp_v2/core/articoli/queries.py` — aggiunti `_load_famiglie_map`, `list_famiglie`, `set_famiglia_articolo`; aggiornati `list_articoli` e `get_articolo_detail` con LEFT JOIN su `CoreArticoloConfig`
- `src/nssp_v2/core/articoli/__init__.py` — esportati `FamigliaItem`, `list_famiglie`, `set_famiglia_articolo`
- `src/nssp_v2/app/api/produzione.py` — aggiunti `GET /famiglie`, `PATCH /articoli/{codice}/famiglia`
- `src/nssp_v2/app/services/admin_policy.py` — fix pre-esistente: `HTTP_422_UNPROCESSABLE_CONTENT` → `HTTP_422_UNPROCESSABLE_ENTITY`
- `tests/unit/test_core_articoli_read_models.py` — aggiornati costruttori con `famiglia_code=None, famiglia_label=None`

**Frontend (modificati):**
- `src/types/api.ts` — aggiunto `FamigliaItem`; aggiunti `famiglia_code`, `famiglia_label` a `ArticoloItem` e `ArticoloDetail`
- `src/pages/surfaces/ProduzioneHome.tsx` — caricamento catalogo famiglie, sezione "Classificazione interna" con select nel pannello dettaglio, handler `handleFamigliaChange` (PATCH → aggiornamento locale stato)

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests/core/test_core_famiglia_articoli.py -q` | Claude Code | Windows / .venv | 15 passed |
| `python -m pytest tests -q` | Claude Code | Windows / .venv | 244 passed |
| `alembic upgrade head` + `alembic current` | Claude Code | Windows / .venv | `20260407007 (head)` |
| `python -c "from nssp_v2.core.articoli import list_famiglie ...; print('famiglie articoli OK')"` | Claude Code | Windows / .venv | OK |
| `npx tsc --noEmit` | Claude Code | Windows / Node | 0 errori |

### Assumptions

- `CoreArticoloConfig` non ha FK hard verso `sync_articoli` — la coerenza è garantita a livello applicativo (stessa scelta di `CoreDestinazioneConfig`).
- Il catalogo famiglie è seedato via migration e non è modificabile dalla UI nel primo slice.
- La select UI mostra `— nessuna —` come prima opzione per rimuovere l'associazione.

### Known Limits

- L'aggiornamento della famiglia non ricarica la lista articoli (non necessario: `famiglia_label` nella lista è aggiornato solo al prossimo caricamento). Nell'uso reale non è un problema perché la lista non mostra la label della famiglia.
- Nessun feedback visivo post-salvataggio famiglia (fuori scope per slice minimo).

### Follow-ups

- Eventuale badge famiglia nella colonna lista articoli (quando il filtro per famiglia sarà utile).
- Validazione backend che `famiglia_code` passato via PATCH sia presente in `articolo_famiglie` (oggi silenziosamente accetta codici inesistenti).

## Completed At

2026-04-07

## Completed By

Claude Code
