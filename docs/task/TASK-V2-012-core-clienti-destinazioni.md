# TASK-V2-012 - Core clienti + destinazioni

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
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
- `docs/task/TASK-V2-010-sync-clienti-reale.md`
- `docs/task/TASK-V2-011-sync-destinazioni.md`

## Goal

Implementare il primo slice Core `clienti + destinazioni` come ponte tra i target sync interni e la futura surface logistica.

## Context

La V2 dispone gia dei mirror interni:

- `sync_clienti`
- `sync_destinazioni`

Questi target sono pero ancora modelli tecnici di sync e non devono essere esposti direttamente alla UI.

Serve ora un primo slice Core che:

- legga solo dai target sync interni
- costruisca la relazione `cliente -> destinazioni`
- introduca il primo dato interno configurabile `nickname_destinazione`
- esponga un read model stabile per backend e UI

Questo task non deve ancora implementare la surface UI a 3 colonne.
Deve preparare il modello applicativo che quella surface potra consumare.

## Scope

### In Scope

- struttura Core dedicata al slice `clienti + destinazioni`
- persistenza interna minima per `nickname_destinazione`
- read model Core per:
  - lista clienti
  - lista destinazioni per cliente
  - dettaglio destinazione
- query/backend contract coerente con `DL-ARCH-V2-010`
- test backend sul comportamento del Core slice
- aggiornamento documentazione tecnica se necessario

### Out of Scope

- implementazione UI della surface logistica
- scheduler e orchestrazione runtime
- estensione dei mapping Easy oltre i campi gia sincronizzati
- nuove sync unit
- configurazioni logistiche oltre `nickname_destinazione`

## Constraints

- il Core legge solo da `sync_clienti` e `sync_destinazioni`
- il Core non scrive mai nei target `sync_*`
- `nickname_destinazione` vive nel Core, non nel layer `sync`
- il primo slice non introduce campi Easy non ancora presenti nei target sync correnti
- la distinzione tra dati Easy read-only e dati interni configurabili deve restare esplicita
- la UI non deve essere costretta a ricostruire join o fallback sui dati nel client

## Acceptance Criteria

- esiste una persistenza Core dedicata per `nickname_destinazione`
- esiste un read model Core per la lista clienti
- esiste un read model Core per la lista destinazioni di un cliente
- esiste un read model Core per il dettaglio di una destinazione
- il Core espone `display_label` o equivalente come campo sintetico di lettura per la destinazione
- il Core non richiede campi Easy non presenti nel mapping attivo
- i test backend verificano almeno:
  - join clienti/destinazioni
  - fallback di `display_label`
  - separazione tra campi read-only Easy e `nickname_destinazione`

## Deliverables

- moduli Core per il slice `clienti + destinazioni`
- migration e modello persistente per `nickname_destinazione` o configurazione equivalente
- test backend del Core slice
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/decisions/UIX/DL-UIX-V2-002.md` se vengono chiariti i campi realmente supportati dal primo slice

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
python scripts/seed_initial.py
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
python -c "from nssp_v2.core.clienti_destinazioni import ...; print('core slice OK')"
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il Core come layer di composizione e significato, non come mirror sync
- usare `codice_destinazione` come identita tecnica della destinazione nel primo slice
- esporre un `display_label` deterministico con fallback:
  1. `nickname_destinazione`
  2. `indirizzo`
  3. `codice_destinazione`
- se serve un endpoint backend, mantenerlo stretto e orientato ai read model, non alla UI finale completa

---

## Completion Notes

### Summary

Implementato il primo slice Core `clienti + destinazioni`. Il Core legge da `sync_clienti` e `sync_destinazioni` (mai modifica), introduce la persistenza interna `core_destinazione_config` per `nickname_destinazione`, e espone tre read model applicativi (`ClienteItem`, `DestinazioneItem`, `DestinazioneDetail`) con campo sintetico `display_label` (fallback: nickname → indirizzo → codice). La separazione tra dati Easy read-only e dati interni configurabili è esplicita nella struttura dei modelli.

### Files Changed

- `src/nssp_v2/core/clienti_destinazioni/__init__.py` — package con re-export API pubblica
- `src/nssp_v2/core/clienti_destinazioni/models.py` — `CoreDestinazioneConfig` (ORM, PK=codice_destinazione, no FK hard verso sync)
- `src/nssp_v2/core/clienti_destinazioni/read_models.py` — `ClienteItem`, `DestinazioneItem`, `DestinazioneDetail` (Pydantic frozen, distinzione esplicita dati Easy / interni)
- `src/nssp_v2/core/clienti_destinazioni/queries.py` — `list_clienti`, `list_destinazioni_per_cliente`, `get_destinazione_detail`, `set_nickname_destinazione`, `_compute_display_label`
- `alembic/versions/20260407_005_core_destinazione_config.py` — migration `core_destinazione_config` (down_revision=20260407004)
- `tests/unit/test_core_read_models.py` — 14 test su read model, display_label fallback, frozen, separazione (senza DB)
- `tests/core/__init__.py` — package marker
- `tests/core/test_core_queries.py` — 20 test di integrazione SQLite in-memory (join, display_label, set_nickname, separazione Easy/interno)

### Dependencies Introduced

Nessuna nuova dipendenza. Pydantic già presente.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 124 passed, 4 failed (pre-esistenti in test_admin_policy) |
| `python -c "from nssp_v2.core.clienti_destinazioni import ...; print('core slice OK')"` | Claude Code (agente) | backend V2 locale (sys.path=src) | core slice OK — CoreDestinazioneConfig tablename: core_destinazione_config |
| `alembic upgrade head` (migration 005) | Non eseguita | PostgreSQL non disponibile nell'ambiente agente | Da eseguire con Docker DB attivo |

### Assumptions

- `codice_destinazione` usato come PK in `CoreDestinazioneConfig` senza surrogate int: la source identity del layer sync è già stabile e unica (DL-ARCH-V2-010 §5).
- Nessuna FK hard da `core_destinazione_config` verso `sync_destinazioni`: il decoupling è intenzionale e consente di impostare nickname anche prima della sync o dopo una mark_inactive.
- `DestinazioneItem` e `DestinazioneDetail` sono Pydantic frozen — la UI non può modificarli lato client; le modifiche passano solo attraverso `set_nickname_destinazione`.
- `list_destinazioni_per_cliente` filtra solo `attivo=True`: le destinazioni inattive non sono esposte alla surface.
- `get_destinazione_detail` non filtra per `attivo`: il dettaglio è accessibile anche per destinazioni inattive (navigazione diretta per codice).

### Known Limits

- Nessun endpoint HTTP esposto in questo task: il Core slice è pronto ma non ancora collegato a un router FastAPI. Il task successivo può aggiungere il router.
- `CAP` assente nel read model: non presente nei target sync correnti (DL-ARCH-V2-010 §7). Entra in uno slice successivo dopo estensione del mapping.
- `ragione_sociale_cliente` nel dettaglio è il nome del cliente dalla sync, non un campo dedicato destinazione.

### Follow-ups

- **TASK-V2-013**: Router FastAPI `core/clienti_destinazioni` — GET `/clienti`, GET `/clienti/{codice_cli}/destinazioni`, GET `/destinazioni/{codice_destinazione}`, PATCH `/destinazioni/{codice_destinazione}/nickname`
- Aggiungere indice su `sync_destinazioni.codice_cli` (migration) per migliorare performance della query `list_destinazioni_per_cliente`

## Completed At

2026-04-07

## Completed By

Claude Code
