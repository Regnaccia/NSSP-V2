# TASK-V2-083 - Model stock policy defaults and overrides

## Status

Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Deferred`
- `Completed`

## Date

2026-04-13

## Owner

Claude Code

## Source Documents

- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`

## Goal

Introdurre il modello configurativo minimo della stock policy V1 con default a livello famiglia
e override a livello articolo.

## Context

La stock policy V1 e stata fissata come estensione minima del planning `by_article`.

Serve prima il modello configurativo stabile, separato dalle logiche di calcolo e dal consumo
in `Planning Candidates`.

## Scope

- aggiungere nei default famiglia:
  - `stock_months`
  - `stock_trigger_months`
- aggiungere negli override articolo:
  - `override_stock_months`
  - `override_stock_trigger_months`
  - `capacity_override_qty`
- mantenere la regola:
  - nessun `family capacity default`
- aggiornare Core/API/read model `articoli` per esporre:
  - `effective_stock_months`
  - `effective_stock_trigger_months`

## Out of Scope

- calcolo di `monthly_stock_base_qty`
- calcolo di `capacity_calculated_qty`
- integrazione in `Planning Candidates`
- UI dedicata stock policy

## Constraints

- la stock policy V1 vale solo per `planning_mode = by_article`
- la `capacity` resta proprieta articolo-specifica
- non introdurre flag separato `has_stock_policy`

## Acceptance Criteria

- il modello dati supporta default famiglia e override articolo per la stock policy V1
- il Core `articoli` espone i valori effettivi di `stock_months` e `stock_trigger_months`
- `capacity_override_qty` e disponibile a livello articolo

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base al perimetro backend toccato.

## Completed At

2026-04-13

## Completed By

Claude Code

## Completion Notes

**Alembic migration** `20260413_022_stock_policy_config.py`:
- `articolo_famiglie`: aggiunte colonne `stock_months NUMERIC(10,4)`, `stock_trigger_months NUMERIC(10,4)` (nullable)
- `core_articolo_config`: aggiunte colonne `override_stock_months NUMERIC(10,4)`, `override_stock_trigger_months NUMERIC(10,4)`, `capacity_override_qty NUMERIC(14,4)` (tutte nullable)

**models.py**:
- `ArticoloFamiglia`: campi `stock_months`, `stock_trigger_months` (`Mapped[Decimal | None]`, `Numeric(10,4)`)
- `CoreArticoloConfig`: campi `override_stock_months`, `override_stock_trigger_months`, `capacity_override_qty`

**read_models.py**:
- `ArticoloDetail`: aggiunti `effective_stock_months`, `effective_stock_trigger_months`, `capacity_override_qty` (tutti `Decimal | None = None`)
- `FamigliaRow`: aggiunti `stock_months`, `stock_trigger_months` (`Decimal | None = None`)

**queries.py**:
- `resolve_stock_policy(override, family_default)`: helper puro — stessa regola di `resolve_planning_policy` adattata per Decimal
- `_famiglia_to_row(famiglia, n_articoli)`: helper interno per costruire `FamigliaRow`; tutti e 5 i costruttori (list_famiglie_catalog, create_famiglia, toggle_*) aggiornati a usarlo
- `get_articolo_detail`: legge `stock_months`/`stock_trigger_months` dalla famiglia, `override_*` dal config; calcola `effective_*` via `resolve_stock_policy`

Nessuna logica di calcolo (`monthly_stock_base_qty`, `capacity_calculated_qty`) introdotta — fuori scope.
Nessuna UI dedicata — fuori scope.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

