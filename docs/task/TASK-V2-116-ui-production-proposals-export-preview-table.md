# TASK-V2-116 - UI production proposals export preview table

## Status
Completed

## Date
2026-04-14

## Owner
Claude Code

## Source Documents

- `docs/specs/PRODUCTION_PROPOSALS_SPEC_V1_0.md`
- `docs/specs/PRODUCTION_PROPOSALS_V1_REDUCED_SPEC.md`
- `docs/decisions/ARCH/DL-ARCH-V2-034.md`

## Goal

Riallineare la tabella `Production Proposals` alla preview quasi `1:1` del tracciato export EasyJob, con descrizione multilinea e focus sui campi realmente usati dall'operatore prima dell'export.

## Context

La vista proposal oggi e ancora centrata su campi interni del dominio proposal (`planning_mode`, driver, qty). Per validare davvero il flusso operativo prima del writer `xlsx`, la UI deve mostrare direttamente i campi export-oriented.

## Scope

- aggiornare la tabella workspace-oriented di `Production Proposals`
- mostrare come colonne principali:
  - `cliente`
  - `codice`
  - `descrizione`
  - `immagine`
  - `misura`
  - `quantità`
  - `materiale`
  - `mm_materiale`
  - `ordine`
  - `note`
  - `user`
  - `warnings`
- rendere `descrizione` come campo multilinea
- declassare o rimuovere dalla tabella principale i campi non strettamente necessari alla preview export
- mantenere le azioni di workspace:
  - override
  - `Esporta`
  - `Chiudi senza esportare`

## Out of Scope

- writer `xlsx`
- prima logica proposal con `note_fragment`
- cambiamenti al reconcile
- redesign della history view oltre l'adattamento minimo se necessario

## Constraints

- la UI non deve ricostruire semantica export da sola: deve consumare il contratto Core del task precedente
- la `descrizione` non deve mostrare la repr literal Python-list
- la tabella puo essere larga; lo scroll orizzontale e ammesso
- `warnings` restano visibili come contesto operativo

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` Si
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` N/A
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` No

## Pattern References

- `Pattern 04 - Core read model prima della UI`
- `Pattern 11 - Tabella operativa come preview del contratto reale`
- `Pattern 12 - Rendere leggibile in UI un formato serializzato usato in export`

## Refresh / Sync Behavior

- `La vista non ha refresh on demand`

La page proposal continua a consumare:

- workspace temporaneo se aperta con `workspace_id`
- storico exported altrimenti

senza modificare la chain di refresh backend.

## Acceptance Criteria

- la tabella workspace-oriented mostra le colonne export-preview principali
- `descrizione` e resa come multilinea leggibile
- i campi interni non strettamente necessari non dominano piu la tabella principale
- la UX resta usabile con tabella larga e scroll orizzontale

## Deliverables

- `ProductionProposalsPage.tsx` aggiornata
- eventuali helper UI collegati
- test/build frontend mirati

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
npm run build
```

Atteso: exit code `0`.

## Implementation Notes

- la workspace view e il focus principale del task
- la history view puo restare piu compatta se non serve all'operatore per la preview pre-export
- tenere `warnings` e `azioni` visibili senza schiacciare la leggibilita delle colonne export

## Documentation Handoff

- Claude aggiorna solo questo task a chiusura
- il riallineamento di overview e indici verra fatto dopo da Codex o revisore documentale

---

## Completion Notes

Riallineata la tabella workspace di `ProductionProposalsPage.tsx` al contratto export-preview EasyJob prodotto da TASK-V2-115.

**`frontend/src/types/api.ts`**:
- Aggiunti campi export-preview a `ProposalWorkspaceRowItem` e `ProductionProposalItem`:
  `description_parts`, `export_description`, `codice_immagine`, `materiale`, `mm_materiale`, `ordine`, `ordine_linea_mancante`, `note_preview`, `user_preview`.

**`frontend/src/pages/surfaces/ProductionProposalsPage.tsx`**:
- Aggiunti helper `fmtMm()` e componente `DescrizioneParts` (rendering multilinea da `description_parts`).
- Rimpiazzata la tabella workspace con colonne export-oriented: Cliente/Dest., Codice, Descrizione, Immagine, Qtà, Materiale, mm Mat., Ordine, Note, User, Warnings, Azioni.
- `descrizione` renderizzata come lista verticale da `description_parts` (prima riga font-medium, righe successive muted) — non viene mostrata la repr Python-list.
- `ordine_linea_mancante=true` esposto come badge diagnostico inline `"riga mancante"` in rosso.
- `override_qty` mostrato come sub-label sulla cella Qtà quando presente.
- Tabella con `minWidth: 1200px` e scroll orizzontale ammesso.
- Colonna `colSpan` aggiornata a 12.
- `HistoryView` non modificata (out of scope per il task).

**Verification**: `npm run build` — exit code 0.

## Completed At

2026-04-14

## Completed By

Claude Code
