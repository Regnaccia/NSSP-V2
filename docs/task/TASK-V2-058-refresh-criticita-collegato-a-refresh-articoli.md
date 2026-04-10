# TASK-V2-058 - Refresh criticita collegato a refresh articoli

## Status
Done

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-023.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/task/TASK-V2-054-refresh-semantici-backend.md`
- `docs/task/TASK-V2-055-criticita-articoli-v1.md`
- `docs/task/TASK-V2-056-refinement-ui-criticita-articoli.md`
- `docs/task/TASK-V2-057-toggle-considera-in-produzione-criticita.md`

## Goal

Collegare il pulsante `Aggiorna` della vista `criticita articoli` al refresh semantico backend con tutte le dipendenze necessarie, invece di limitarsi a ricaricare la lista gia materializzata.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-054`
- `TASK-V2-055`
- `TASK-V2-056`

## Context

La vista `criticita articoli` dipende dai fact canonici:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

Questi fact vengono oggi riallineati correttamente dal refresh semantico `refresh_articoli()`, introdotto con `TASK-V2-054`.

Il pulsante `Aggiorna` della vista `criticita` deve quindi usare quel refresh semantico, non un semplice reload del solo endpoint lista.

Al termine del refresh semantico, la UI deve ricaricare l'endpoint `criticita` per mostrare i nuovi dati.

Poiche la vista `criticita` deve essere trattata come dipendente dalla surface `articoli`, il refresh corretto e proprio il refresh completo di `articoli/produzione`, non un refresh parziale della sola lista critica.

## Scope

### In Scope

- collegare il pulsante `Aggiorna` della vista `criticita articoli` al refresh semantico backend della surface `produzione`
- usare il trigger backend-controlled gia esistente per `refresh_articoli()`
- al completamento del refresh, ricaricare la lista `criticita articoli`
- gestire in UI stato `loading`, errore e completamento coerenti con l'azione utente
- aggiornare il testo o il comportamento del pulsante se necessario per chiarire che non e un semplice reload locale
- aggiornare documentazione minima della vista

### Out of Scope

- nuovo refresh semantico dedicato esclusivamente alla vista `criticita`
- modifica della logica di criticita
- modifica della formula di `availability`
- nuova freshness bar dedicata alla vista `criticita`
- refactor generale della UX di tutte le surface

## Constraints

- la vista `criticita` non deve conoscere o replicare localmente la chain tecnica dei singoli step
- il refresh deve appoggiarsi alla funzione semantica backend gia esistente per la surface `articoli/produzione`
- la lista `criticita` va ricaricata solo dopo il refresh oppure dopo il suo esito finale gestito
- evitare duplicazione di orchestrazione lato frontend
- il task deve rendere esplicito che aggiornare `criticita` significa aggiornare anche la surface `articoli` da cui eredita il perimetro operativo

## Acceptance Criteria

- cliccando `Aggiorna` in vista `criticita`, la UI triggera il refresh semantico backend della surface `produzione`
- il refresh esegue quindi tutte le dipendenze gia incapsulate in `refresh_articoli()`
- al termine del refresh la lista `criticita` viene ricaricata
- la vista non si limita piu a fare solo `GET /produzione/criticita`
- in caso di errore nel refresh, la UI mostra un esito coerente e non lascia stato ambiguo
- la documentazione del task rende esplicito che il refresh della vista `criticita` dipende dal refresh completo della surface `articoli`

## Deliverables

- wiring UI del pulsante `Aggiorna` verso il refresh semantico corretto
- reload lista `criticita` dopo refresh
- eventuale piccolo refinement UX sullo stato di aggiornamento
- aggiornamento documentazione coerente

## Verification Level

`Mirata`

Questo task e un fix/refinement di wiring applicativo su una surface gia esistente.

Quindi:

- test mirati frontend/app sulla vista `criticita`
- test mirati backend solo se viene toccato il contratto chiamato dalla UI
- build frontend obbligatoria
- niente full suite obbligatoria

## Verification Commands

```bash
cd backend
python -m pytest tests/app tests/core -q
```

```bash
cd frontend
npm run build
```

## Implementation Notes

Direzione raccomandata:

- riusare lo stesso endpoint/contratto di refresh gia usato dalla surface `articoli`
- non introdurre una nuova catena tecnica nella pagina `criticita`
- mantenere la pagina `criticita` come consumer di:
  - refresh semantico gia esistente
  - endpoint read-only della lista critica

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

### Dipendenza architettonica: criticita -> surface articoli

La vista `criticita` non ha un proprio refresh semantico. I fact canonici che determina i suoi
risultati (`inventory`, `customer_set_aside`, `commitments`, `availability`) sono tutti calcolati
dalla chain di `refresh_articoli()`.

Aggiornare la vista `criticita` **significa aggiornare la surface `articoli`**: il refresh
completo di `POST /sync/surface/produzione` (8 step) è l'unica operazione che garantisce
che i valori di `availability_qty` siano freschi rispetto ai dati Easy.

Un semplice reload di `GET /produzione/criticita` senza il refresh semantico mostrerebbe
valori calcolati all'ultimo rebuild precedente — potenzialmente datati.

### Modifiche

Solo `CriticitaPage.tsx` — nessuna modifica backend (il contratto era già corretto).

**`handleRefresh` (nuovo)**

Sostituisce il vecchio `load()` diretto dal pulsante. Sequenza:

1. `setSyncStatus('syncing')` → UI blocca il pulsante, mostra "Aggiornamento dati…"
2. `POST /sync/surface/produzione` — refresh semantico backend completo (8 step:
   sync articoli + mag_reale + righe_ordine_cliente + produzioni_attive + rebuild inventory
   + customer_set_aside + commitments + availability)
3. Esito:
   - tutti `success` → `toast.success` + `setSyncStatus('success')`
   - almeno uno non-success → `toast.error` con lista entity fallite + `setSyncStatus('error')`
   - 409 → "Refresh già in esecuzione"
   - 503 → "Easy non configurato"
   - altri errori → messaggio dal backend o fallback generico
4. In ogni caso: `await loadCriticita(soloInProduzione)` — ricarica la lista con il perimetro corrente

**`loadCriticita(sip)` (rinominata da `load`)**

Separazione esplicita tra caricamento lista (`loadStatus`) e refresh semantico (`syncStatus`).
Il reload post-refresh imposta `loadStatus='loading'` poi `'idle'`, senza toccare `syncStatus`.

**`PageHeader`** — riceve ora `loadStatus` e `syncStatus` separati:

- testo pulsante: "Aggiornamento dati…" durante sync, "Caricamento…" durante load, "Aggiorna dati" a riposo
- `busy = loadStatus === 'loading' || syncStatus === 'syncing'` — disabilita in entrambi i casi
- badge errore sync visibile solo se `syncStatus === 'error'` e `loadStatus !== 'error'`

**Corpo pagina** — condizioni di rendering includono `syncStatus !== 'syncing'` per nascondere
tabella e messaggi durante il refresh, mostrando invece "Aggiornamento dati da Easy…".

### Verifica

```
npm run build
✓ built in 3.11s
```

Backend invariato — nessuna modifica al contratto API.

## Completed At

2026-04-10

## Completed By

Claude Code
