# TASK-V2-033 - Gestione forza completata produzioni

## Status
Completed

## Date
2026-04-08

## Scope

Implementare la prima gestione operativa del flag interno `forza_completata`
nella surface `produzioni`.

Il task deve permettere di forzare lo stato `completata` su una produzione selezionata,
senza modificare i dati sorgente Easy e senza alterare i mirror sync.

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
- `docs/task/TASK-V2-030-core-produzioni-bucket-e-stato.md`
- `docs/task/TASK-V2-031-ui-produzioni.md`
- `docs/task/TASK-V2-032-sync-on-demand-produzioni.md`

## Goal

Tradurre nella UI il primo override operativo del dominio `produzioni`, rendendo visibile e modificabile il flag `forza_completata` sulla produzione selezionata.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-030`
- `TASK-V2-031`

`TASK-V2-032` e raccomandato ma non strettamente bloccante.

## Context

`DL-ARCH-V2-015` ha introdotto:

- computed fact `stato_produzione`
- override interno `forza_completata`

Il primo slice UI `produzioni` nasce consultivo. Questo task introduce la prima azione operativa
mirata sul pannello di dettaglio della produzione selezionata.

## In Scope

- visualizzazione esplicita del flag `forza_completata`
- azione UI per attivare/disattivare il flag
- update del dato tramite backend/Core
- refresh coerente del pannello di dettaglio e della lista, se necessario
- evidenza chiara dell'impatto sullo `stato_produzione`

## Out of Scope

- workflow avanzati di chiusura produzione
- stati intermedi diversi da `attiva` / `completata`
- azioni batch
- modifica diretta di `quantita_ordinata` o `quantita_prodotta`

## Constraints

- il flag vive solo nel `core`
- nessuna modifica ai mirror sync o a Easy
- la UI non ricalcola la logica di stato: legge `stato_produzione` dal backend
- la UX deve rendere evidente che si tratta di un override interno

## Acceptance Criteria

- la surface `produzioni` mostra il valore corrente di `forza_completata`
- esiste un'azione UI per modificarlo sulla produzione selezionata
- il backend aggiorna il flag nel `core`
- dopo l'update la UI mostra correttamente:
  - `forza_completata`
  - `stato_produzione`
- `npm run build` passa senza errori
- le verifiche backend del comportamento passano

## Deliverables

- endpoint/command backend per update del flag
- integrazione UI nella surface `produzioni`
- eventuali test backend o smoke test coerenti
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_PRODUZIONI.md`
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
- endpoint/command introdotti
- test eseguiti
- test non eseguiti con motivazione
- assunzioni
- limiti noti
- follow-up suggeriti

## Completion Notes

### File creati/modificati

**Modificati:**
- `frontend/src/pages/surfaces/ProduzioniPage.tsx` — aggiunta callback `onToggleForzaCompletata`, sezione "Override interno V2" con pulsante toggle in `ColonnaDettaglio`, aggiornamento ottimistico della lista (`setProduzioni` con replace by key), `SaveStatus` locale con auto-reset

### Endpoint/command introdotti

Nessuno: l'endpoint `PATCH /api/produzione/produzioni/{id_dettaglio}/forza-completata` era già disponibile da TASK-V2-030. Questo task ha solo integrato la UI.

### Comportamento implementato

- Il pulsante mostra "Forza completata" se `forza_completata=false`, "Rimuovi override" se `true`
- Il colore del pulsante cambia (arancione se override attivo, neutro altrimenti)
- Dopo il PATCH il backend restituisce `ProduzioneItem` aggiornato con nuovo `stato_produzione` — il frontend lo sostituisce nella lista senza ricaricare tutto
- Badge "Override attivo" visibile nella sezione stato quando `forza_completata=true`
- Feedback saving/saved/error con auto-reset (2.5s/3.5s)
- `saveStatus` resettato al cambio di produzione selezionata

### Test eseguiti

- `npm run build` → ✓
- `python -m pytest tests -q` → 307/307 passed

### Test non eseguiti

- Test E2E frontend: fuori scope.

### Assunzioni

- Il backend restituisce `ProduzioneItem` con `stato_produzione` già ricalcolato: il frontend non ricalcola mai la logica di stato.
- L'aggiornamento della lista è replace-by-key (`toKey(updated)`): se il backend cambia `bucket` (scenario non previsto) il record non verrebbe trovato — ma questo non accade per design.

### Limiti noti

- Nessuna azione batch (fuori scope).

### Follow-up suggeriti

- Filtri per bucket/stato nella colonna lista.
- Conferma modale opzionale prima di rimuovere un override (UX).
- Test HTTP per il PATCH forza_completata.
