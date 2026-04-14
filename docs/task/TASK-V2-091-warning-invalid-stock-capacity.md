# TASK-V2-091 - Warning invalid stock capacity

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

- `docs/specs/WARNINGS_SPEC_V1.md`
- `docs/decisions/ARCH/DL-ARCH-V2-029.md`
- `docs/specs/STOCK_POLICY_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-030.md`

## Goal

Introdurre nel modulo `Warnings` un nuovo tipo di avviso per gli articoli che rientrano nel
perimetro stock policy ma hanno una `capacity` invalida o assente.

## Context

Con l'introduzione della stock policy V1 emerge un nuovo caso di incoerenza:

- articolo nel ramo `planning_mode = by_article`
- stock policy applicabile
- `capacity_effective_qty` nulla, zero o comunque non valida

Questo caso non rappresenta direttamente un fabbisogno produttivo, ma un problema di dato o di
configurazione che deve essere esposto come warning trasversale.

## Scope

- introdurre un nuovo warning type nel modulo `Warnings`
- calcolare il warning per articoli nel perimetro stock policy con `capacity` invalida
- definire payload minimo coerente con il warning:
  - `article_code`
  - `capacity_calculated_qty`
  - `capacity_override_qty`
  - `capacity_effective_qty`
  - `type`
  - `severity`
  - `created_at`
- assegnare audience iniziale coerente con il caso:
  - `produzione`
  - `magazzino`
  - `admin`

## Out of Scope

- badge warning nelle surface operative
- blocchi automatici del planning
- correzione automatica della capacity
- nuovi tipi warning oltre questo caso

## Constraints

- il warning deve nascere nel modulo `Warnings`, non in `Planning Candidates`
- il calcolo deve riusare i dati Core stock gia disponibili
- nessuna duplicazione per reparto: un warning canonico, audience multipla

## Acceptance Criteria

- esiste un nuovo warning type dedicato alla `capacity` stock invalida
- il warning viene generato per articoli stock-driven con `capacity` incoerente
- il warning espone i valori capacity rilevanti per diagnosi
- la visibilita iniziale e coerente con `produzione`, `magazzino`, `admin`

## Verification Level

- `Mirata`

## Environment Bootstrap

N/A

## Verification Commands

Da definire da Claude in base ai test backend introdotti.

## Documentation Handoff

Claude aggiorna solo questo task:

- `Status`
- `Completion Notes`
- `Completed At`
- `Completed By`

## Completion Notes

Implementato il warning `INVALID_STOCK_CAPACITY` nel modulo `Warnings`:

- **`logic.py`**: aggiunta `is_invalid_stock_capacity(capacity_effective_qty)` — True se None o <= 0
- **`config.py`**: aggiunto `INVALID_STOCK_CAPACITY` a `KNOWN_WARNING_TYPES` con default audience `["produzione", "magazzino", "admin"]`
- **`read_models.py`**: aggiunto `capacity_calculated_qty`, `capacity_override_qty`, `capacity_effective_qty` (opzionali); resi opzionali `stock_calculated` e `anomaly_qty`
- **`queries.py`**: `list_warnings_v1` genera entrambi i tipi; `INVALID_STOCK_CAPACITY` usa lazy import `from nssp_v2.core.stock_policy import list_stock_metrics_v1` per evitare circular import; ordinamento per `article_code`
- **`__init__.py`**: esporta `is_invalid_stock_capacity`
- **`stock_policy/read_models.py`**: aggiunto `capacity_override_qty` a `StockMetricsItem`
- **`stock_policy/queries.py`**: aggiunto `capacity_override_qty=capacity_override` alla costruzione di `StockMetricsItem`
- **`tests/core/test_core_warnings.py`**: aggiunti 5 test puri per `is_invalid_stock_capacity` + 8 test di integrazione (genera warning, nessun warning se valido, coesistenza dei due tipi, warning_id unico, articolo non by_article escluso)

Tutti i test (864) passano.

## Completed At

2026-04-13

## Completed By

Claude Code
