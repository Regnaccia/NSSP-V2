# TASK-V2-056 - Refinement UI criticita articoli

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`
- `docs/task/TASK-V2-055-criticita-articoli-v1.md`

## Goal

Raffinare la vista `criticita articoli` introducendo:

- perimetro operativo basato su `famiglia.considera_in_produzione = true`
- filtro UI per famiglia
- ordinamento sulla lista per:
  - `Famiglia`
  - `Giacenza`
  - `Appartata`
  - `Impegnata`
  - `Disponibilita`

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-055`

## Context

La V1 di `criticita articoli` introduce una prima vista minima degli articoli con `availability_qty < 0`.

Il refinement successivo non deve ancora cambiare la logica di criticita, ma deve migliorare il perimetro operativo e la leggibilita della lista:

- non mostrare indiscriminatamente tutti gli articoli
- appoggiarsi al dato di dominio `considera_in_produzione`
- permettere lettura e ordinamento piu efficaci

Questa scelta evita hardcode sui nomi famiglia e mantiene la regola nel modello di dominio.

## Scope

### In Scope

- limitare la vista critica agli articoli la cui famiglia ha `considera_in_produzione = true`
- introdurre filtro UI per famiglia nella vista `criticita articoli`
- introdurre ordinamento sulla lista/tabella per:
  - `Famiglia`
  - `Giacenza`
  - `Appartata`
  - `Impegnata`
  - `Disponibilita`
- aggiornare il contratto/query/read model solo per supportare il refinement UI richiesto
- aggiornare la documentazione minima della vista

### Out of Scope

- modifica della logica V1 di criticita (`availability_qty < 0`)
- safety stock
- policy diverse per famiglia
- slice temporali
- aggregazioni per orizzonte temporale
- suggerimenti automatici operativi

## Constraints

- la logica di criticita resta invariata in questo task
- il perimetro operativo deve dipendere da `considera_in_produzione`, non da nomi famiglia hardcoded
- il filtro famiglia e un refinement UI, non una nuova logica di dominio
- l'ordinamento deve restare coerente e leggibile sulla stessa lista critica

## Acceptance Criteria

- la vista `criticita articoli` mostra solo articoli con famiglia `considera_in_produzione = true`
- l'utente puo filtrare la lista per famiglia
- l'utente puo ordinare la lista per `Famiglia`, `Giacenza`, `Appartata`, `Impegnata`, `Disponibilita`
- la logica di criticita V1 resta invariata
- `npm run build` passa

## Deliverables

- refinement query/read model se necessario
- refinement UI della vista `criticita articoli`
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Questo task e un refinement UI/applicativo della vista critica gia esistente.

Quindi:

- test mirati su query/read model e comportamento UI coinvolto
- build frontend obbligatoria
- niente full suite obbligatoria

## Verification Commands

```bash
cd backend
python -m pytest tests/core tests/app -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- trattare `considera_in_produzione` come filtro di perimetro operativo
- non cambiare ancora la formula di criticita
- mantenere il refinement semplice e leggibile
- preparare il terreno a futuri passaggi su:
  - scorte
  - policy per famiglia
  - slice temporali

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Perimetro operativo — backend

`core/criticita/queries.py` — `list_criticita_v1` riscritta:

- rimosso il caricamento preventivo della mappa famiglie (non più necessario)
- `OUTERJOIN SyncArticolo` mantenuto (descrizione opzionale)
- `INNER JOIN CoreArticoloConfig` — articoli senza famiglia assegnata esclusi
- `INNER JOIN ArticoloFamiglia` con filtri `considera_in_produzione = True` e `is_active = True`
- il campo `famiglia_code` e `famiglia_label` vengono ora dal join diretto (non dal lookup)

Il perimetro è gestito interamente in SQL: nessuna logica Python aggiuntiva, nessuna modifica
alla formula V1 `is_critical_v1`.

### Test backend

`tests/core/test_core_criticita.py` — aggiornato e ampliato (20 test totali):

- helper `_famiglia` aggiornato con parametro `considera_in_produzione` (default `False`)
- 4 nuovi test dedicati al perimetro (TASK-V2-056):
  - `test_list_criticita_v1_esclude_senza_famiglia`
  - `test_list_criticita_v1_esclude_famiglia_non_in_produzione`
  - `test_list_criticita_v1_esclude_famiglia_inattiva`
  - `test_list_criticita_v1_include_famiglia_in_produzione`
  - `test_list_criticita_v1_mix_perimetro`
- test precedenti aggiornati per includere famiglia con `considera_in_produzione=True`
- rimosso `test_list_criticita_v1_famiglia_none_se_non_assegnata` (comportamento ora cambiato:
  articoli senza famiglia sono esclusi, non inclusi con `famiglia_code = None`)

### Filtro famiglia e ordinamento colonne — frontend

`CriticitaPage.tsx` — raffinato:

- `FiltriBar`: dropdown "Tutte le famiglie" + voci uniche da `famiglia_label` degli item caricati;
  appare solo se ci sono item (non nel caso di lista vuota)
- `famigliaFilter` state: stringa vuota = tutti; client-side su `items`
- `sortKey` / `sortDir` state: default `availability_qty` asc (peggiori sopra)
- `Th` componente: header colonna cliccabile con icona ↑ / ↓ / ↕; toggle `asc↔desc` se già
  attivo, altrimenti `asc` come default su nuova colonna
- Colonne ordinabili: `Famiglia`, `Giacenza`, `Appartata`, `Impegnata`, `Disponibilita`
- `sorted = [...filtered].sort(cmpItems)` — derivato da `useMemo`; immutabile
- Badge header: `X / Y articoli critici` (shown / total) quando c'è un filtro famiglia attivo
- Messaggio `TabellaFiltroVuota` se il filtro non produce risultati (ma ci sono item in totale)

### Verifica

```
python -m pytest tests/core tests/app -q
284 passed in 4.69s

npm run build
✓ built in 7.36s
```

## Completed At

2026-04-10

## Completed By

Claude Code
