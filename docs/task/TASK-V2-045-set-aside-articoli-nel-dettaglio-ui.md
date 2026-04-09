# TASK-V2-045 - Set aside articoli nel dettaglio UI

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-041-core-ordini-cliente.md`
- `docs/task/TASK-V2-044-customer-set-aside.md`

## Goal

Esporre nel dettaglio della surface `articoli` il dato `customer_set_aside` come campo read-only, cosi da verificare visivamente la quota gia appartata per cliente per ogni articolo.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-044`
- `TASK-V2-046` raccomandato, se si vuole che il dato mostrato venga riallineato anche dal refresh della schermata `articoli`

## Context

Con `DL-ARCH-V2-019` la V2 introduce `customer_set_aside` come fact canonico intermedio, derivato da `DOC_QTAP`.

Come gia fatto per la giacenza in `TASK-V2-038`, la surface `articoli` e il punto piu semplice per una prima validazione visiva del nuovo dato:

- l'utente seleziona un articolo
- il pannello di destra mostra la quota gia appartata per cliente

Questo task non introduce ancora una UI dedicata a ordini, impegni o availability. Riusa una surface gia esistente per validare il nuovo building block.

## In Scope

- estendere il contratto Core/API `articoli` per includere `customer_set_aside` o naming equivalente coerente
- esporre nel dettaglio articolo almeno:
  - `set_aside_qty`
  - eventuale `computed_at`, se disponibile e gia esposto dal Core
- rendering read-only del dato nel pannello di destra della surface `articoli`
- presentazione chiara come dato calcolato internamente e distinto da `giacenza`

## Out of Scope

- modifica manuale del set aside
- UI dedicata a ordini o spedizioni
- availability finale
- drill-down sulle righe ordine cliente
- filtri articoli basati sul set aside

## Constraints

- la pagina `articoli` deve leggere il dato dal Core, non direttamente da `customer_order_lines`
- il campo deve essere read-only
- il task non deve comprimere `set_aside` dentro `inventory` o `commitments`
- il naming mostrato in UI deve evitare ambiguita con `giacenza` e `impegni`

## Acceptance Criteria

- il dettaglio articolo mostra il valore `customer_set_aside` calcolato dal Core
- il dato e coerente col contratto del fact intermedio introdotto in `TASK-V2-044`
- la UI rende evidente che il campo e read-only
- il dettaglio continua a funzionare correttamente anche per articoli senza quote appartate
- `npm run build` passa senza errori

## Deliverables

- aggiornamento del contratto Core/API `articoli`
- aggiornamento della surface `articoli`
- eventuali test backend/frontend coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`
  - `docs/task/TASK-V2-046-refresh-sequenziale-articoli-giacenza-e-set-aside.md`

## Verification Commands

Il task deve chiudersi con almeno:

```bash
cd frontend
npm run build
```

e con almeno una verifica backend/frontend combinata coerente col flusso, ad esempio:

```bash
cd backend
python -m pytest tests -q
```

## Completion Output Required

Alla chiusura del task devono essere riportati:

- file creati/modificati
- contratti Core/API estesi
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Implementation Notes

Direzione raccomandata:

- seguire lo stesso pattern gia usato per la giacenza in `TASK-V2-038`
- mantenere il perimetro V1 stretto: solo esposizione read-only nel dettaglio articolo
- evitare per ora qualunque calcolo di `availability`
- lasciare separati in UI:
  - `giacenza`
  - `commitments`
  - `set_aside`

## Completion Notes

### File creati/modificati

**Modificati:**
- `src/nssp_v2/core/articoli/read_models.py`
  - `ArticoloDetail`: aggiunti `customer_set_aside_qty: Decimal | None = None` e `set_aside_computed_at: datetime | None = None`
- `src/nssp_v2/core/articoli/queries.py`
  - `get_articolo_detail`: aggiunto import `CoreCustomerSetAside` e query aggregata per ottenere `sum(set_aside_qty)` e `max(computed_at)` dell'articolo; valori popolati in `ArticoloDetail`
- `frontend/src/types/api.ts`
  - `ArticoloDetail`: aggiunti `customer_set_aside_qty: string | null` e `set_aside_computed_at: string | null`
- `frontend/src/pages/surfaces/ProduzioneHome.tsx`
  - `ColonnaDettaglio`: aggiunta sezione "Quota appartata — sola lettura (ODE)" tra giacenza e dati Easy
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - Aggiunta sezione "Quota appartata - sola lettura (ODE)"

**Creati:**
- `tests/core/test_core_articoli_set_aside.py` — 5 test di integrazione

### Contratti Core/API estesi

**`ArticoloDetail` (backend Pydantic + frontend TypeScript):**
- `customer_set_aside_qty`: somma aggregata dei `set_aside_qty` del fact `core_customer_set_aside` per l'articolo; `null` se nessuna quota appartata
- `set_aside_computed_at`: `max(computed_at)` dei record `core_customer_set_aside` per l'articolo; `null` se nessuna quota

**Nessuna nuova migration**: la query legge da `core_customer_set_aside` (introdotta in TASK-V2-044).

### UI introdotta

Sezione "Quota appartata — sola lettura (ODE)" nel pannello di destra della surface `articoli`:
- mostra la quantità aggregata con unità di misura
- label descrittiva: "Quota già inscatolata o appartata per cliente (DOC_QTAP). Non è ancora evasa e non è più giacenza libera."
- timestamp di calcolo
- fallback testo se nessuna quota per l'articolo

### Test eseguiti

5 test in `tests/core/test_core_articoli_set_aside.py`:
- `customer_set_aside_qty = None` se nessun record set_aside per l'articolo ✓
- `customer_set_aside_qty` uguale al valore del record quando presente ✓
- `set_aside_computed_at` valorizzato quando la quota è presente ✓
- somma di più record set_aside per lo stesso articolo ✓
- isolamento per articolo: set_aside di un articolo non interferisc con un altro ✓

Suite completa: 458/458 passed.
Frontend: `npm run build` — zero errori TypeScript e Vite.

### Test non eseguiti

- Test HTTP su endpoint `/api/produzione/articoli/{codice}`: non inclusi — il contratto API è coperto dal test di integrazione Core.
- Test frontend E2E: non inclusi.
- Test con dati reali Easy: non eseguibili senza connessione.

### Assunzioni

- La query `CoreCustomerSetAside` usa `article_code == art.codice_articolo` senza normalizzazione (strip/upper): coerente con come il fact è costruito in `rebuild_customer_set_aside` che usa `line.article_code` direttamente.
- La sezione è posizionata dopo giacenza e prima dei dati Easy: ordine semantico crescente (stock fisico → quota appartata → dati sorgente).
- Il campo è sempre read-only: nessun controllo di editing aggiunto.

### Limiti noti

- Se i `article_code` in `core_customer_set_aside` e in `sync_articoli` differiscono per casing/spacing, la query restituisce NULL. Questa coerenza è responsabilità dell'upstream (TASK-V2-040 sync righe ordine, normalizzazione EasyJob).
- Nessun aggiornamento automatico della sezione dopo un rebuild `customer_set_aside`: il dato si aggiorna al prossimo caricamento del dettaglio articolo.

### Follow-up suggeriti

- TASK-V2-046: integrare `rebuild_customer_set_aside` nel flusso "Aggiorna dati" della surface articoli.
- Computed fact `availability = inventory - commitments - set_aside` (DL-ARCH-V2-019 §8).

## Completed At

2026-04-09

## Completed By

Claude Code
