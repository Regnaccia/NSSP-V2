# TASK-V2-050 - Availability e commitments articoli nel dettaglio UI

## Status
Completed

## Date
2026-04-09

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-042-commitments-cliente.md`
- `docs/task/TASK-V2-043-commitments-produzione.md`
- `docs/task/TASK-V2-045-set-aside-articoli-nel-dettaglio-ui.md`
- `docs/task/TASK-V2-049-core-availability.md`

## Goal

Esporre nel dettaglio della surface `articoli` due nuovi dati read-only ODE:

- `committed_qty`
- `availability_qty`

cosi da mostrare nel pannello il quadro quantitativo minimo completo:

- giacenza
- quota appartata
- impegni
- disponibilita

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-042`
- `TASK-V2-043`
- `TASK-V2-045`
- `TASK-V2-049`

## Context

Con `TASK-V2-045` la surface `articoli` mostra gia:

- `giacenza`
- `customer_set_aside`

Con `TASK-V2-049` la V2 dispone anche del fact canonico:

- `availability`

Per validare visivamente il modello quantitativo V1, il pannello dettaglio `articoli` deve ora esporre anche:

- il totale `committed_qty`
- il totale `availability_qty`

senza introdurre ancora UI dedicate a allocazioni, ATP o disponibilita datata.

## In Scope

- estendere il contratto Core/API `articoli` per includere:
  - `committed_qty`
  - eventuale `commitments_computed_at`, se disponibile e gia esposto in modo coerente
  - `availability_qty`
  - eventuale `availability_computed_at`, se disponibile e gia esposto in modo coerente
- rendering read-only dei due dati nel pannello di destra della surface `articoli`
- presentazione chiara e separata da:
  - `giacenza`
  - `customer_set_aside`

## Out of Scope

- modifica manuale dei valori
- UI dedicata `availability`
- drill-down sui commitment per sorgente
- ATP
- filtri articoli basati su `availability`
- estensione del refresh sequenziale

## Constraints

- la pagina `articoli` deve leggere i dati dal `core`
- il campo `committed_qty` deve riflettere il fact canonico `commitments`, non una formula locale nel frontend
- il campo `availability_qty` deve riflettere il fact canonico `availability`
- tutti i dati devono restare read-only
- il naming mostrato in UI deve evitare ambiguita tra:
  - impegni
  - appartato
  - disponibilita

## Acceptance Criteria

- il dettaglio articolo mostra `committed_qty`
- il dettaglio articolo mostra `availability_qty`
- i dati sono coerenti con i fact canonici del `core`
- la UI rende evidente che i campi sono read-only
- il dettaglio continua a funzionare correttamente anche quando i fact sono assenti
- `npm run build` passa senza errori

## Deliverables

- aggiornamento del contratto Core/API `articoli`
- aggiornamento della surface `articoli`
- eventuali test backend/frontend coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

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

- seguire lo stesso pattern gia usato per `giacenza` e `customer_set_aside`
- presentare i quattro numeri nello stesso pannello, con semantica distinta
- non comprimere `committed_qty` dentro `availability`
- mantenere il perimetro V1 stretto: sola esposizione read-only

## Completion Notes

### File modificati

**Backend:**

- `src/nssp_v2/core/articoli/read_models.py`
  - `ArticoloDetail`: aggiunti 4 campi opzionali:
    - `committed_qty: Decimal | None = None`
    - `commitments_computed_at: datetime | None = None`
    - `availability_qty: Decimal | None = None`
    - `availability_computed_at: datetime | None = None`

- `src/nssp_v2/core/articoli/queries.py`
  - Aggiunti import `CoreCommitment`, `CoreAvailability`
  - In `get_articolo_detail`:
    - Aggiunta query aggregata su `CoreCommitment` per `article_code` (sum + max computed_at)
    - Aggiunta query su `CoreAvailability` per `article_code`
    - Nuovi campi popolati nel `ArticoloDetail` restituito

**Frontend:**

- `src/types/api.ts`
  - `ArticoloDetail`: aggiunti 4 campi:
    - `committed_qty: string | null`
    - `commitments_computed_at: string | null`
    - `availability_qty: string | null`
    - `availability_computed_at: string | null`

- `src/pages/surfaces/ProduzioneHome.tsx`
  - `ColonnaDettaglio`: aggiunte 2 nuove sezioni tra "Quota appartata" e "Dati anagrafici":
    - **Impegni — sola lettura (ODE)**: mostra `committed_qty` con descrizione; "Nessun impegno attivo" se null
    - **Disponibilita — sola lettura (ODE)**: mostra `availability_qty` con colorazione rossa se negativa; "Disponibilita non ancora calcolata" se null

### Contratti Core/API estesi

- `ArticoloDetail` (backend read model + frontend type): 4 nuovi campi opzionali
- Endpoint `GET /api/produzione/articoli/{codice}`: risposta estesa con i nuovi campi (nessuna breaking change — i campi sono opzionali e backward-compatible)

### Nessuna migration

Nessuna modifica al DB. I fact sorgente (`core_commitments`, `core_availability`) erano gia presenti.

### Test eseguiti

Suite completa: 482/482 passed.
Frontend: `npm run build` — zero errori.

### Test non eseguiti

- Test HTTP end-to-end per il nuovo contratto: non inclusi (pattern coerente con le altre surface)

### Assunzioni

- `committed_qty` e `availability_qty` vengono esposti come `None` se i fact canonici non sono ancora stati calcolati (prima esecuzione o rebuild non ancora effettuato). Questo e il comportamento corretto: il pannello mostra un messaggio "non ancora calcolato" invece di un valore errato.
- La colorazione rossa per `availability_qty < 0` e accettabile nel V1: segnala visivamente il sovra-impegno senza bloccare l'utente.
- `committed_qty` aggrega tutte le provenienze (`customer_order` + `production`) — comportamento canonico del fact.

### Limiti noti

- Il pannello non mostra il dettaglio per provenienza (drill-down su impegni per ordine/produzione) — fuori scope V1.
- `availability_computed_at` riflette il timestamp dell'ultimo rebuild `availability`, non necessariamente allineato con `giacenza_computed_at` o `set_aside_computed_at`.

### Follow-up suggeriti

- TASK-V2-051: estensione del refresh sequenziale `articoli` per includere `rebuild_availability` come step 6

## Completed At

2026-04-09

## Completed By

Claude Code
