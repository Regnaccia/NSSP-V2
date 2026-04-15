# TASK-V2-115 - Core proposal export preview contracts

## Status
Completed

## Date
2026-04-14

## Owner
Claude Code

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-033.md`
- `docs/decisions/ARCH/DL-ARCH-V2-034.md`

## Goal

Arricchire il Core `production_proposals` con i campi necessari a mostrare in UI la preview quasi `1:1` del tracciato export EasyJob, prima dell'implementazione del writer `xlsx`.

## Context

Il modulo proposal usa oggi un workspace temporaneo corretto sul flusso, ma la UI espone ancora campi troppo interni (`planning_mode`, `driver`, qty) e non ancora il contratto reale del file EasyJob.

Prima del writer `xlsx` serve un contratto Core/API esplicito che esponga i campi export-preview:

- `cliente`
- `codice`
- `descrizione` export-ready + parti multilinea UI
- `immagine`
- `misura`
- `quantità`
- `materiale`
- `mm_materiale`
- `ordine`
- `note_preview`
- `user_preview`

## Scope

- estendere read model e query di `production_proposals` per workspace e storico esportato
- derivare dai dati articolo / planning i campi preview export
- introdurre validazione semantica di preview per `ordine`
- esporre campi preview tramite API esistenti proposal/workspace
- mantenere invariato il writer export attuale in questo task

## Out of Scope

- writer `xlsx`
- cambio del formato export effettivo
- prima proposal logic con `note_fragment`
- redesign UI della tabella

## Constraints

- nessuna scrittura verso EasyJob
- il task non deve reintrodurre proposal persistenti pre-export
- `ordine` deve risultare vuoto per `stock-only`
- nel ramo customer, `line_reference` mancante deve emergere come errore semantico bloccante per l'export futuro, ma in questo task puo essere esposto come stato/flag diagnostico nel contratto
- `descrizione` deve supportare:
  - serializzazione literal Python-list per export
  - rendering multilinea in UI

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` Si
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` Si
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 10 - Preview operativa allineata al contratto export`
- `Pattern 14 - Configurazione articolo: governance nel modello, visibilita in articoli`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand`

Il task non modifica la chain dei refresh semantici. Le API proposal/workspace continuano a leggere lo stato corrente gia persistito o congelato.

## Acceptance Criteria

- i workspace proposal espongono i campi preview necessari al tracciato EasyJob
- lo storico exported espone gli stessi campi preview rilevanti
- il contratto distingue chiaramente tra:
  - `description_parts`
  - descrizione export serializzata
  - descrizione UI multilinea
- il contratto espone la costruibilita di `ordine` senza demandare la semantica al frontend

## Deliverables

- read model aggiornati di `production_proposals`
- query/core enrichment per workspace e storico
- test backend mirati del nuovo contratto

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Verification Commands

```bash
pytest V2/backend/tests/core/test_core_production_proposals.py -q
```

Atteso: exit code `0`.

## Implementation Notes

- usare il dominio `articoli` come sorgente dei campi anagrafici export-preview
- evitare concatenazioni improprie in UI: il Core deve fornire campi gia pronti
- non introdurre ancora `note_fragment` da logica proposal: usare placeholder o campi incompleti solo se strettamente necessario e chiaramente marcati

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Estesi read model e query di `production_proposals` con i campi export-preview EasyJob.

**`alembic/versions/20260414_027_proposal_description_parts.py`**:
- Aggiunta colonna `description_parts_json JSON NOT NULL DEFAULT '[]'` a `core_proposal_workspace_rows` e `core_production_proposals`.

**`core/production_proposals/models.py`**:
- Aggiunto `description_parts_json: Mapped[list]` a `CoreProposalWorkspaceRow` e `CoreProductionProposal`.

**`core/production_proposals/read_models.py`**:
- Aggiunti a `ProposalWorkspaceRowItem` e `ProductionProposalItem`:
  - `description_parts: list[str]` — snapshot parti descrittive
  - `export_description: str` — `repr(description_parts)` per colonna EasyJob
  - `codice_immagine: str | None` — COD_IMM da sync_articoli
  - `materiale: str | None` — MAT_COD da sync_articoli
  - `mm_materiale: Decimal | None` — REGN_QT_OCCORR da sync_articoli
  - `ordine: str | None` — order_reference per customer; None per stock-only
  - `ordine_linea_mancante: bool` — True se customer ma line_reference assente (diagnostico semantico)
  - `note_preview: str` — vuoto per workspace, ode_ref per proposal esportate
  - `user_preview: str` — placeholder V1 fisso: `"NSSP"`

**`core/production_proposals/queries.py`**:
- `_ArticoloPreview` dataclass e `_load_articolo_preview_data()` — batch lookup su `sync_articoli` per codice_immagine, materiale, mm_materiale.
- `_export_description()` — `repr(parts)`.
- `_ordine_from_row()` — logica ordine (customer vs stock-only).
- `_ordine_linea_mancante()` — diagnostico semantico.
- `_workspace_row_from_candidate()` — popola `description_parts_json`.
- `_workspace_to_detail()` — batch-load preview e usa `_workspace_row_to_item()`.
- `_proposal_to_item()` — accetta `preview: _ArticoloPreview | None` opzionale.
- `list_production_proposals()`, `get_production_proposal_detail()` — batch-load preview prima di costruire i read model.
- `export_proposal_workspace_csv()` — copia `description_parts_json` in `CoreProductionProposal`.

**`tests/core/test_core_production_proposals.py`**:
- 9 test nuovi sul contratto export-preview: description_parts snapshot, preview da sync_articoli, articolo non trovato, ordine customer/stock, ordine_linea_mancante, note_preview workspace/exported, propagazione attraverso export.
- Suite completa: 933 test passati.

## Completed At

2026-04-14

## Completed By

Claude Code
