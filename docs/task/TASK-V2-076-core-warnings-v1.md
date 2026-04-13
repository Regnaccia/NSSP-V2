# TASK-V2-076 - Core Warnings V1

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/decisions/ARCH/DL-ARCH-V2-028.md`

## Goal

Introdurre il primo slice Core del modulo `Warnings` come modulo trasversale canonico,
separato dai moduli che consumano i warning.

## Context

`Planning Candidates` ha gia fissato la regola che lo stock negativo:

- non genera automaticamente un need produttivo
- non deve comparire come `reason` del candidate

Serve quindi un primo modulo warning che prenda in carico questa anomalia in modo
canonico e riusabile.

## Scope

- introdurre il primo oggetto canonico `Warning`
- introdurre il primo tipo warning:
  - `NEGATIVE_STOCK`
- generare warning per articoli con `stock_calculated < 0`
- esporre nel Core una shape minima con:
  - identificativo warning
  - tipo
  - severita
  - entita colpita
  - messaggio
  - metadati minimi di visibilita
  - timestamp
- centralizzare ownership e generazione nel modulo `Warnings`

## Out of Scope

- UI dedicata `Warnings`
- badge warning nelle altre surface
- workflow warning completo:
  - `open`
  - `acknowledged`
  - `resolved`
- configurazione amministrativa della visibilita da `admin`
- altri tipi warning oltre `NEGATIVE_STOCK`

## Constraints

- il warning deve esistere una sola volta come oggetto canonico
- i moduli operativi non devono duplicare la logica di generazione del warning
- `Planning Candidates` continua a usare `stock_effective = max(stock_calculated, 0)`
- la visibilita puo partire in forma minima, per esempio `visible_in_surfaces`, senza aprire ancora la UI di governance

## Acceptance Criteria

- esiste il primo slice Core `Warnings`
- `NEGATIVE_STOCK` viene generato per articoli con `stock_calculated < 0`
- la shape Core warning espone almeno:
  - `warning_id`
  - `type`
  - `severity`
  - `entity_type`
  - `entity_key`
  - `message`
  - `source_module`
  - `visible_in_surfaces`
  - `created_at`
- `Warnings` e separato da `Planning Candidates`
- nessun modulo operativo possiede una copia separata dello stesso warning

## Verification Level

- `Mirata`

Verifiche minime:

- test backend mirati sul modulo `Warnings`
- caso con articolo a stock negativo
- caso con articolo non negativo
- verifica che il warning sia unico e non duplicato

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

Nuovo slice `nssp_v2.core.warnings`:

- `logic.py`: `is_negative_stock(inventory_qty) -> bool` — condizione pura, None-safe
- `read_models.py`: `WarningItem` frozen — shape canonica completa (warning_id, type, severity, entity_type, entity_key, message, source_module, visible_in_surfaces, created_at) + campi specifici NEGATIVE_STOCK (article_code, stock_calculated, anomaly_qty)
- `queries.py`: `list_warnings_v1(session)` — INNER JOIN CoreAvailability × SyncArticolo (attivo=True), filtra inventory_qty < 0, ordina per inventory_qty crescente (peggiori prima)
- `__init__.py`: esporta is_negative_stock, WarningItem, list_warnings_v1

Principi rispettati:
- `warning_id = "NEGATIVE_STOCK:{article_code}"` — unico per articolo, no duplicati
- `visible_in_surfaces = ["articoli"]` — hardcoded V1, espandibile via admin
- `source_module = "warnings"` — ownership esplicita centralizzata
- Separato da Planning Candidates: PC usa stock_effective = max(0, stock_calculated), Warnings segnala lo stock negativo come anomalia

## Verification Notes

- 16/16 test `tests/core/test_core_warnings.py` — tutti verdi
- Casi coperti: stock negativo, stock zero, stock positivo, articolo non attivo, articolo non in sync, piu articoli senza duplicati, ordinamento peggiori-prima, warning_id univoci, mix attivi/inattivi

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completed At`
- `Completed By`
- `Completion Notes`
- `Verification Notes`

