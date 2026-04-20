# TASK-V2-147 - UI remove legacy criticality navigation

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/roadmap/CLEANUP_PLAN_2026-04-17.md`
- `docs/task/TASK-V2-080-deprecazione-surface-criticita-articoli.md`
- `docs/decisions/ARCH/DL-ARCH-V2-041.md`

## Goal

Togliere la surface legacy `Criticita Articoli` dalla navigazione primaria dell'applicazione.

## Scope

- rimuovere la voce dalla sidebar / navigation contestuale
- mantenere separata l'eventuale esistenza tecnica della route finche non verra deciso il cleanup del codice
- riallineare overview e docs UI se necessario

## Out of Scope

- eliminazione completa del file `CriticitaPage.tsx`
- refactor di `Planning Candidates`
- changes al Core

## Constraints

- la route puo restare temporaneamente esistente, ma non deve piu essere presentata come surface primaria
- il cleanup di navigazione deve essere coerente con il `Unified Planning Workspace`

## Acceptance Criteria

- `Criticita (legacy)` non compare piu nella navigation primaria
- nessuna altra surface attiva viene impattata
- eventuali riferimenti documentali principali risultano coerenti

## Verification Level

- `Mirata`

## Implementation Log

### 2026-04-19

**`frontend/src/components/AppShell.tsx`**

- Rimossa la voce `{ path: '/produzione/criticita', label: 'Criticità (legacy)' }` da `SURFACE_FUNCTIONS['produzione']`.
- La route `/produzione/criticita` resta tecnicamente accessibile ma non compare piu nella navigazione primaria.
- Nessun altra surface impattata.
