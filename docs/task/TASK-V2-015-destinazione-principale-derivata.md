# TASK-V2-015 - Destinazione principale derivata

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
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`
- `docs/task/TASK-V2-012-core-clienti-destinazioni.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`

## Goal

Integrare nella logica applicativa la regola per cui ogni cliente espone una destinazione principale derivata dai propri dati anagrafici, unificata alle destinazioni aggiuntive nel modello Core e nella surface clienti/destinazioni.

## Context

Il progetto ha gia introdotto:

- `sync_clienti`
- `sync_destinazioni`
- il primo slice Core clienti/destinazioni
- la prima surface browser clienti/destinazioni

Successivamente e stato approvato `DL-ARCH-V2-012`, che chiarisce una regola di dominio non ancora esplicitata nel primo slice:

- il cliente stesso deve essere trattato come destinazione principale esplicita
- le righe di `POT_DESTDIV` restano destinazioni aggiuntive

`TASK-V2-012` resta chiuso e non va riaperto.
Questo task serve a integrare la nuova regola nella logica esistente, senza riscrivere retroattivamente il task storico.

## Scope

### In Scope

- aggiornamento del Core clienti/destinazioni per generare la destinazione principale derivata
- identita Core stabile per la destinazione principale
- inclusione della principale nei read model di elenco e dettaglio
- supporto a `nickname_destinazione` anche per la principale
- aggiornamento della UI clienti/destinazioni per mostrare la principale come voce reale
- eventuale aggiornamento documentale collegato alla nuova logica

### Out of Scope

- modifiche al layer `sync`
- modifica dei mapping Easy sorgente
- scheduler
- trigger `sync on demand`
- configurazioni logistiche oltre `nickname_destinazione`

## Constraints

- `sync_clienti` e `sync_destinazioni` non devono essere alterati per accomodare questa regola
- la promozione della principale avviene solo nel Core
- la UI non deve dedurre la principale da sola
- la principale deve avere identita Core deterministica e distinta dalle destinazioni aggiuntive
- l’elenco destinazioni del cliente deve risultare unificato e con la principale in posizione coerente

## Acceptance Criteria

- il Core espone sempre una destinazione principale per ogni cliente
- la destinazione principale e inclusa nell’elenco destinazioni del cliente anche se `POT_DESTDIV` e vuota
- il read model espone un attributo esplicito tipo `is_primary` o equivalente
- `nickname_destinazione` puo essere persistito e letto anche per la principale
- la UI mostra la principale come voce esplicita e distinta dalle destinazioni aggiuntive
- la UI non richiede logica client-side per ricostruire la principale
- i test backend coprono almeno:
  - cliente senza destinazioni aggiuntive
  - cliente con principale + aggiuntive
  - nickname sulla principale

## Deliverables

- aggiornamenti Core relativi a lista/dettaglio destinazioni
- eventuali migration o adattamenti della persistenza nickname, se necessari
- aggiornamenti frontend della surface clienti/destinazioni
- test backend e, se utili, test frontend/smoke
- eventuale aggiornamento di:
  - `docs/decisions/UIX/DL-UIX-V2-002.md`
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
python scripts/seed_initial.py
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

Se vengono introdotti test mirati, riportare anche il comando piu specifico.

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- trattare la principale come promozione Core dei dati cliente, non come record artificiale nel layer sync
- mantenere l’identita tecnica delle destinazioni aggiuntive invariata
- preferire una rappresentazione esplicita della principale nel read model, invece di affidarci a convenzioni implicite
- se necessario, aggiornare il dettaglio UI per rendere visibile che la voce selezionata e la destinazione principale

---

## Completion Notes

### Summary

Integrata la destinazione principale derivata (DL-ARCH-V2-012) nel Core slice clienti/destinazioni. Identità tecnica: `"MAIN:{codice_cli}"` — unica, stabile, distinguibile per prefisso. Il read model `DestinazioneItem` e `DestinazioneDetail` ora includono `is_primary: bool`. La query `list_destinazioni_per_cliente` costruisce la principale da `sync_clienti` e la antepone alle aggiuntive da `sync_destinazioni`. `get_destinazione_detail` gestisce sia principale (`MAIN:*`) sia aggiuntive. Il nickname è configurabile su entrambi i tipi. Il layer `sync` non è stato modificato. La UI mostra un badge "Principale" / "Destinazione principale" nelle colonne centrale e destra.

### Files Changed

- `src/nssp_v2/core/clienti_destinazioni/read_models.py` — aggiunto `is_primary: bool` a `DestinazioneItem` e `DestinazioneDetail`
- `src/nssp_v2/core/clienti_destinazioni/queries.py` — aggiunto `PRIMARY_PREFIX`, `_primary_codice`, `_is_primary_codice`, `_codice_cli_from_primary`, `_compute_primary_display_label`; aggiornate `list_destinazioni_per_cliente` e `get_destinazione_detail`; aggiunto `_get_primary_detail` e `_get_aggiuntiva_detail`
- `frontend/src/types/api.ts` — aggiunto `is_primary: boolean` a `DestinazioneItem` e `DestinazioneDetail`
- `frontend/src/pages/surfaces/LogisticaHome.tsx` — badge "Principale" nella riga destinazione (colonna centrale) e badge "Destinazione principale" nell'intestazione del dettaglio (colonna destra)
- `tests/unit/test_core_read_models.py` — aggiunti `is_primary` a tutti i costruttori + 6 nuovi test su identità principale e display_label principale
- `tests/core/test_core_primary.py` — 18 nuovi test: cliente senza aggiuntive, lista unificata, ordinamento, nickname, dettaglio MAIN, display_label fallback

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale, Python 3.11.9, pytest 8.3.5 | 162 passed, 4 failed pre-esistenti (test_admin_policy) |
| `npm run build` | Claude Code (agente) | frontend V2 locale, TypeScript 5.7, Vite 6.4 | ✓ built in 4.13s — 0 errori TypeScript |

### Assumptions

- L'identità `"MAIN:{codice_cli}"` è il formato scelto per il task implementativo (DL-ARCH-V2-012 §4 lascia libertà al task). È stabile, unica per cliente, non cade in conflitto con codici `POT_DESTDIV` (che hanno formato diverso: es. `D001`, `BRD001`).
- La principale appare solo se il cliente è `attivo=True` in `sync_clienti`. Clienti inattivi non generano principale (semantica conservativa).
- `citta` è `None` nella principale perché non presente in `sync_clienti` (ANACLI). Campo disponibile solo per le aggiuntive (PDES_CITTA in POT_DESTDIV).
- `display_label` della principale usa `ragione_sociale` come fallback (non `indirizzo`), perché la principale rappresenta il cliente stesso e il nome è più significativo.

### Known Limits

- Nessuna migration: `CoreDestinazioneConfig` è già keyed su stringa, quindi `"MAIN:C001"` funziona senza schema changes.
- Il trigger sync on demand (`POST /api/sync/surface/logistica`) non richiede aggiornamenti: produce solo `sync_clienti` e `sync_destinazioni`, la principale è computata on-the-fly dal Core.

### Follow-ups

- **TASK-V2-016**: UI scroll colonne clienti/destinazioni (già schedulato)
- Eventuale migrazione futura verso un indice su `core_destinazione_config` per ricerche per `codice_cli`

## Completed At

2026-04-07

## Completed By

Claude Code
