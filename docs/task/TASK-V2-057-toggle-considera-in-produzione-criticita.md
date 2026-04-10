# TASK-V2-057 - Toggle considera_in_produzione nella vista criticita

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
- `docs/task/TASK-V2-027-flag-considera-in-produzione-famiglie.md`
- `docs/task/TASK-V2-056-refinement-ui-criticita-articoli.md`

## Goal

Rendere il filtro di perimetro `famiglia.considera_in_produzione = true` attivabile/disattivabile nella vista `criticita articoli`, con default attivo.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-056`

## Context

La vista `criticita articoli` ha introdotto il perimetro operativo basato su `famiglia.considera_in_produzione = true`.

Questa scelta e corretta come default di dominio, ma in fase di test e popolamento dati non tutte le famiglie possono essere gia configurate in modo coerente.

Serve quindi un refinement di debug/operativita:

- default: mostra solo articoli con `considera_in_produzione = true`
- opzione esplicita: disattivare il filtro per vedere tutti gli articoli critici

In questo modo:

- il comportamento di dominio corretto resta il default
- il debug e il popolamento delle famiglie restano possibili

## Scope

### In Scope

- introdurre nella vista `criticita articoli` un toggle del filtro `considera_in_produzione`
- default del toggle:
  - attivo
- con toggle attivo:
  - mostra solo articoli la cui famiglia ha `considera_in_produzione = true`
- con toggle disattivo:
  - mostra tutti gli articoli critici, indipendentemente dal flag famiglia
- mantenere il filtro famiglia gia introdotto in `TASK-V2-056`
- aggiornare il read model / query se necessario per supportare il toggle
- aggiornare la documentazione minima della vista

### Out of Scope

- modifica della logica V1 di criticita (`availability_qty < 0`)
- nuove policy di criticita
- safety stock
- slice temporali
- nuovi ordinamenti oltre a quelli gia introdotti

## Constraints

- il default deve restare coerente con il dominio: filtro `considera_in_produzione` attivo
- il toggle serve come refinement operativo/debug, non come cambio della logica di criticita
- la UI non deve duplicare logiche incoerenti tra filtro attivo e filtro disattivo

## Acceptance Criteria

- la vista `criticita articoli` mostra di default solo articoli con `considera_in_produzione = true`
- l'utente puo disattivare il filtro e vedere tutti gli articoli critici
- il filtro famiglia continua a funzionare anche con il toggle
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

- trattare `considera_in_produzione` come perimetro di default, non come vincolo assoluto
- mantenere l'esperienza semplice:
  - toggle chiaro
  - default attivo
- preparare il terreno a futuri refinement su:
  - famiglie non ancora configurate
  - policy diverse di visibilita

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Backend — query e endpoint

`core/criticita/queries.py` — `list_criticita_v1` estesa con parametro keyword-only
`solo_in_produzione: bool = True`:

- `True` (default): INNER JOIN su `CoreArticoloConfig` + `ArticoloFamiglia` con filtri
  `considera_in_produzione = True` e `is_active = True` — comportamento identico a TASK-V2-056
- `False`: tutti gli OUTER JOIN — articoli senza famiglia, con famiglia non-produzione, o con
  famiglia inattiva sono inclusi. `famiglia_code` / `famiglia_label` restano `None` se assenti

Il parametro è keyword-only (`*`) per prevenire errori posizionali nelle chiamate.

`app/api/produzione.py` — `GET /api/produzione/criticita`:

- aggiunto query param `solo_in_produzione: bool = True` — FastAPI lo legge da querystring
- pass-through a `list_criticita_v1(session, solo_in_produzione=solo_in_produzione)`

### Test backend

`tests/core/test_core_criticita.py` — 26 test totali (6 nuovi per TASK-V2-057):

- `test_toggle_false_include_senza_famiglia`
- `test_toggle_false_include_famiglia_non_in_produzione`
- `test_toggle_false_include_famiglia_inattiva`
- `test_toggle_false_include_tutti_i_critici` — mix prod/non-prod/no-fam
- `test_toggle_true_vs_false_stessa_logica_criticita` — zero e positivi esclusi in entrambe le modalita
- `test_toggle_default_e_true` — conferma che il default corrisponde a `solo_in_produzione=True`

### Frontend

`CriticitaPage.tsx` — aggiornamenti:

- `soloInProduzione` state (`bool`, default `true`)
- `handleSoloInProduzioneChange(v)`: aggiorna lo state, chiama `load(v)`, reset `famigliaFilter`
- `load(sip)`: parametrizzata — passa `?solo_in_produzione=true/false` all'API
- `FiltriBar`: checkbox "Solo perimetro produzione" sempre visibile (non condizionato alla presenza
  di items); filtro famiglia separato da divisore verticale, visibile solo se ci sono famiglie
- `TabellaVuota`: messaggio contestuale diverso se `soloInProduzione` o no
- `onRefresh` nel `PageHeader`: `() => load(soloInProduzione)` — rispetta il toggle corrente

### Verifica

```
python -m pytest tests/core tests/app -q
290 passed in 4.83s

npm run build
✓ built in 3.52s
```

## Completed At

2026-04-10

## Completed By

Claude Code
