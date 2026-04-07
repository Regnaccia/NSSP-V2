# TASK-V2-010 - Sync clienti reale

## Status
Todo

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
- `docs/task/TASK-V2-008-hardening-backend-verifica-and-sync-scaffolding.md`
- `docs/task/TASK-V2-009-easy-schema-explorer-and-catalog.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/catalog/ANACLI.json`

## Goal

Implementare la sync reale di `clienti` da Easy `ANACLI` verso il target interno V2, sostituendo l'uso della sorgente fake del bootstrap con un adapter read-only verso Easy.

## Context

`TASK-V2-007` ha validato il bootstrap tecnico del modello sync con una sorgente fake controllata.

Il prossimo passo corretto e introdurre la prima sync reale verso Easy:

- mantenendo il contratto per-entita
- rispettando il vincolo read-only assoluto
- allineando il target `sync_clienti` ai campi documentati in `EASY_CLIENTI.md`

Questo task non deve ancora costruire il Core clienti.
Deve solo produrre un mirror sync interno affidabile e verificabile.

## Scope

### In Scope

- implementazione di un adapter read-only reale per `ANACLI`
- lettura dei campi selezionati in `EASY_CLIENTI.md`
- allineamento del target interno `sync_clienti`
- aggiornamento di modelli, migration e sync unit `clienti` se necessario per includere i campi mappati
- mantenimento di run metadata e freshness anchor
- esecuzione on demand della sync `clienti` con sorgente Easy reale
- verifica tecnica su idempotenza, allineamento e rispetto del contratto read-only
- aggiornamento documentazione minima se cambiano comandi o prerequisiti

### Out of Scope

- sync `destinazioni`
- orchestrazione multi-entita
- scheduler reale
- Core slice clienti
- surface UI dati-dipendente
- scrittura verso Easy

## Constraints

- accesso a Easy solo read-only, senza eccezioni
- rispettare `EASY_CLIENTI.md` come mapping tecnico di riferimento
- il target sync resta vicino alla sorgente e non diventa modello Core
- la sync deve restare idempotente
- il task deve essere verificabile in ambiente pulito secondo `DL-ARCH-V2-002`

## Acceptance Criteria

- esiste un adapter reale read-only per `ANACLI`
- la sync `clienti` legge da Easy i campi documentati e li allinea nel target interno
- il target `sync_clienti` contiene i campi previsti dal mapping `EASY_CLIENTI.md`
- la sync `clienti` resta idempotente su doppia esecuzione
- run metadata e freshness anchor continuano a essere aggiornati correttamente
- la verifica documenta esplicitamente che non avviene alcuna write verso Easy

## Deliverables

- adapter Easy reale per `clienti`
- aggiornamenti a modelli e migration del target `sync_clienti`
- aggiornamenti alla sync unit `clienti`
- test coerenti col nuovo perimetro
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/integrations/easy/EASY_CLIENTI.md` se il mapping cambia

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

Easy:

- configurare `EASY_CONNECTION_STRING` in `.env`
- usare solo connessione read-only

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd backend
python -m pytest tests -q
```

e con almeno una verifica esplicita:

```bash
cd backend
python scripts/sync_clienti.py
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- evidenza che la connessione verso Easy e solo read-only

## Implementation Notes

Direzione raccomandata:

- mantenere l'adapter Easy separato dalla logica della sync unit
- usare il catalogo `ANACLI.json` come riferimento tecnico completo
- usare `EASY_CLIENTI.md` come selezione curata dei campi realmente usati
- non introdurre deduzioni business nel layer `sync`

---

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

### Summary

Cosa e stato fatto.

### Files Changed

- `path/to/file.py` - descrizione modifica

### Dependencies Introduced

- `package>=version` - motivo

### Verification Provenance

Indicare per ogni verifica dichiarata:

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python -m pytest tests -q` | Claude Code (agente) | backend V2 locale | OK |

Valori ammessi per "Eseguita da":
- `Claude Code (agente)` - eseguita dall'agente durante il task
- `Revisore esterno` - eseguita da persona in ambiente separato
- `Non eseguita` - con motivazione obbligatoria

### Assumptions

Assunzioni fatte durante l'implementazione.

### Known Limits

Limiti noti o aspetti non coperti.

### Follow-ups

- suggerimento per task successivo

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
