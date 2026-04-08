# TASK-V2-030 - Core produzioni con bucket e stato computato

## Status
Completed

## Date
2026-04-08

## Scope

Implementare il primo slice `core produzioni` aggregando i mirror:

- `sync_produzioni_attive`
- `sync_produzioni_storiche`

Il task deve introdurre:

- bucket applicativo `active | historical`
- computed fact `stato_produzione`
- flag interno `forza_completata`

## References

- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`

## Objective

Costruire un `core produzioni` che unifichi le produzioni attive e storiche in un read model applicativo, senza perdere la provenienza del dato e introducendo il primo stato computato utile alla futura UI.

## Prerequisite

Prima di eseguire questo task devono esistere:

- `sync_produzioni_attive`
- `sync_produzioni_storiche`

Il task non deve introdurre la lettura diretta da Easy nel layer `core`.

## Requirements

### Aggregazione Core

- leggere i mirror `sync_produzioni_attive` e `sync_produzioni_storiche`
- esporre un read model unificato `produzioni`
- includere nel read model un campo `bucket`

Valori ammessi del bucket:

- `active`
- `historical`

### Computed Fact

Esporre `stato_produzione` con i soli valori iniziali:

- `attiva`
- `completata`

Regola di base:

- `attiva` se `quantita_ordinata > quantita_prodotta`
- `completata` se `quantita_prodotta >= quantita_ordinata`

### Override Interno

Introdurre persistenza interna del flag:

- `forza_completata`

Regola di precedenza:

1. `forza_completata = true` -> `stato_produzione = completata`
2. altrimenti si applica la regola standard sulle quantita

### Contratto API/Core

Il contratto minimo esposto deve contenere almeno:

- identita tecnica della produzione
- bucket
- cliente destinatario
- codice articolo
- descrizione articolo
- numero documento
- numero riga documento
- quantita ordinata
- quantita prodotta
- stato_produzione
- forza_completata

## Deliverables

- modelli/query/read model `core produzioni`
- persistenza interna per `forza_completata`
- migration necessaria
- endpoint backend minimo per:
  - lista produzioni
  - dettaglio produzione, se necessario al modello scelto
  - update del flag `forza_completata`
- test backend per:
  - bucket corretto
  - stato computato corretto
  - precedenza dell'override

## Out of Scope

- UI `produzioni`
- sync on demand `produzioni`
- scheduler automatico
- stati ulteriori oltre `attiva` / `completata`
- logiche di pianificazione o avanzamento produzione

## Verification

La verifica minima deve dimostrare:

- presenza di dati da entrambi i mirror nel read model aggregato
- valorizzazione corretta di `bucket`
- valorizzazione corretta di `stato_produzione`
- funzionamento del flag `forza_completata`

## Expected Commands

- bootstrap backend come da `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
- command o test backend per verificare il read model `produzioni`

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- migration introdotte
- query/read model introdotti
- endpoint introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Creati:**
- `src/nssp_v2/core/produzioni/__init__.py`
- `src/nssp_v2/core/produzioni/models.py` — `CoreProduzioneOverride` (PK composita id_dettaglio + bucket)
- `src/nssp_v2/core/produzioni/read_models.py` — `ProduzioneItem` (bucket, stato_produzione, forza_completata)
- `src/nssp_v2/core/produzioni/queries.py` — `list_produzioni`, `set_forza_completata`, `_compute_stato`
- `alembic/versions/20260407_011_core_produzioni_override.py`
- `tests/core/test_core_produzioni.py`

**Modificati:**
- `src/nssp_v2/app/api/produzione.py` — aggiunta docstring aggiornata, import Core produzioni, `SetForzaCompletataRequest`, endpoint `GET /produzioni` e `PATCH /produzioni/{id_dettaglio}/forza-completata`

### Migration introdotte

- `20260407_011_core_produzioni_override.py` — crea tabella `core_produzione_override`; applicata con `alembic upgrade head`

### Query/read model introdotti

- `ProduzioneItem`: id_dettaglio, bucket, cliente_ragione_sociale, codice_articolo, descrizione_articolo, numero_documento, numero_riga_documento, quantita_ordinata, quantita_prodotta, stato_produzione, forza_completata
- `list_produzioni(session)`: aggrega attive + storiche (attivo=True); attive prima, poi storiche (per id_dettaglio)
- `set_forza_completata(session, id_dettaglio, bucket, valore)`: upsert override; verifica esistenza nel mirror corretto; raises ValueError se non trovato o bucket non valido
- `_compute_stato(qtor, qtev, forza_completata)`: regola base + precedenza override

### Endpoint introdotti

- `GET  /api/produzione/produzioni` → `list[ProduzioneItem]`
- `PATCH /api/produzione/produzioni/{id_dettaglio}/forza-completata` → `ProduzioneItem` (body: `{bucket, forza_completata}`; 404 se non trovato)

### Test eseguiti

18 test in `tests/core/test_core_produzioni.py`:
- bucket: active, historical, entrambi, ordine ✓
- stato_produzione: attiva (qtev<qtor), completata (qtev=qtor, qtev>qtor), None → attiva, storica completata ✓
- forza_completata: default False, override, precedenza su quantita, reset, su storica ✓
- raises: record inesistente, bucket non valido ✓
- isolamento bucket: stesso id_dettaglio su active e historical indipendenti ✓
- filtro inattivi esclusi dalla lista ✓

Suite completa: 307/307 passed.

### Test non eseguiti

- Test HTTP degli endpoint (integration test con TestClient FastAPI): non inclusi in questo task; il comportamento della query Core e gia coperto dai test unitari.

### Assunzioni

- id_dettaglio non e univoco globalmente tra DPRE_PROD e SDPRE_PROD: la PK di override e (id_dettaglio, bucket) per supportare la coesistenza.
- I record con `attivo=False` nel mirror sono esclusi dalla lista produzioni (non sono "vivi" nel sistema).
- Nessuna FK hard verso i mirror sync: il Core mantiene indipendenza dal layer sync.
- `stato_produzione` con entrambe le quantita `None` → `"attiva"` (caso conservativo).

### Limiti noti

- `list_produzioni` non ha ancora paginazione ne filtri: adeguato per il primo slice UI.
- L'endpoint PATCH verifica l'esistenza nel mirror (attivo=True); se il record viene successivamente inattivato nel mirror, l'override resta in `core_produzione_override` ma non impatta la lista (il record viene escluso).

### Follow-up suggeriti

- UI `produzioni`: surface frontend che consuma `GET /produzioni` con filtri per bucket e stato.
- Sync on demand `produzioni`: endpoint trigger per avviare sync produzioni_attive e storiche.
- Filtri avanzati: per cliente, per articolo, per stato_produzione.
- Paginazione della lista produzioni se il volume lo richiede.
