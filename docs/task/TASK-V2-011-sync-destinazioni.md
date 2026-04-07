# TASK-V2-011 - Sync destinazioni

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
- `docs/task/TASK-V2-010-sync-clienti-reale.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
- `docs/integrations/easy/catalog/POT_DESTDIV.json`

## Goal

Implementare la sync reale di `destinazioni` da Easy `POT_DESTDIV` verso il target interno V2, in dipendenza esplicita dalla sync `clienti`.

## Context

Dopo la sync reale `clienti`, la seconda entita naturale e `destinazioni`.

Questo task deve introdurre:

- una nuova sync unit per entita
- una dependency declaration non vuota verso `clienti`
- un target interno `sync_destinazioni` coerente col mapping documentato

Il task non deve ancora creare il Core slice clienti + destinazioni.
Deve solo costruire il secondo mirror sync interno e la sua relazione tecnica col cliente.

## Scope

### In Scope

- implementazione adapter read-only reale per `POT_DESTDIV`
- lettura dei campi selezionati in `EASY_DESTINAZIONI.md`
- target interno `sync_destinazioni`
- source identity tecnica `PDES_COD`
- mantenimento nel target di `CLI_COD` e `NUM_PROGR_CLIENTE`
- dependency declaration esplicita verso `clienti`
- run metadata e freshness anchor coerenti col modello sync condiviso
- verifica di idempotenza e allineamento

### Out of Scope

- Core slice clienti + destinazioni
- orchestrazione completa multi-entita
- scheduler reale
- surface UI dati-dipendente
- scrittura verso Easy

## Constraints

- accesso a Easy solo read-only, senza eccezioni
- rispettare `EASY_DESTINAZIONI.md` come mapping tecnico di riferimento
- `destinazioni` deve dichiarare dipendenza da `clienti`
- il target sync resta vicino alla sorgente e non diventa modello Core
- la sync deve restare idempotente

## Acceptance Criteria

- esiste un adapter reale read-only per `POT_DESTDIV`
- esiste una sync unit `destinazioni` implementata nel layer `sync`
- il target `sync_destinazioni` contiene i campi previsti da `EASY_DESTINAZIONI.md`
- la sync `destinazioni` dichiara e rispetta la dipendenza da `clienti`
- la sync `destinazioni` resta idempotente
- run metadata e freshness anchor vengono aggiornati correttamente

## Deliverables

- adapter Easy reale per `destinazioni`
- modelli e migration per `sync_destinazioni`
- sync unit `destinazioni`
- test coerenti con il perimetro
- eventuale aggiornamento di:
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/integrations/easy/EASY_DESTINAZIONI.md` se il mapping cambia

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
python scripts/<sync_destinazioni>.py
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- evidenza che la connessione verso Easy e solo read-only

## Implementation Notes

Direzione raccomandata:

- costruire `destinazioni` come seconda sync unit autonoma, non come estensione opaca di `clienti`
- usare `PDES_COD` come source identity tecnica
- mantenere `CLI_COD` e `NUM_PROGR_CLIENTE` come campi relazionali importanti
- non introdurre ancora logica Core di unione clienti + destinazioni

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
