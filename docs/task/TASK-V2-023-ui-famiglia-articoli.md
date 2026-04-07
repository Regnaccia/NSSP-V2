# TASK-V2-023 - UI famiglia articoli

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`

## Goal

Aggiungere nella surface `articoli` il primo campo configurabile interno: `famiglia articolo`, mantenendo il layout a `2 colonne` e distinguendo chiaramente dati Easy read-only e dato interno modificabile.

## Context

Con `TASK-V2-020` la V2 ha introdotto la prima UI `articoli` read-only.

Con `TASK-V2-022` il backend introduce:

- catalogo interno delle famiglie articolo
- associazione articolo -> famiglia
- contratto Core/API aggiornato

Serve ora rendere utilizzabile questa prima configurazione direttamente nella surface `articoli`.

## Scope

### In Scope

- caricamento e visualizzazione della famiglia corrente dell'articolo selezionato
- caricamento del catalogo famiglie disponibile
- controllo UI per impostare o aggiornare la famiglia articolo
- integrazione del salvataggio nel pannello di destra della surface `articoli`
- distinzione chiara tra:
  - dati Easy read-only
  - dato interno configurabile `famiglia`
- feedback UI minimo sul salvataggio:
  - idle
  - salvataggio in corso
  - salvato
  - errore

### Out of Scope

- CRUD completo del catalogo famiglie
- bulk update massivo
- altre configurazioni interne articolo
- scheduler
- sync on demand `articoli`

## Constraints

- la UI deve continuare a consumare solo contratti backend/Core
- i campi Easy restano read-only
- `famiglia` e l'unico campo editabile introdotto in questo task
- il layout a `2 colonne` della surface `articoli` deve restare coerente con `UIX_SPEC_ARTICOLI`
- il task non deve introdurre logica di assegnazione automatica della famiglia

## Acceptance Criteria

- la surface `articoli` mostra la famiglia corrente dell'articolo selezionato
- la surface puo leggere il catalogo famiglie disponibile
- la surface permette di impostare o aggiornare la famiglia articolo
- il salvataggio usa solo il contratto backend previsto dal task `TASK-V2-022`
- i dati Easy nel dettaglio restano read-only
- `npm run build` passa senza errori

## Deliverables

- aggiornamento UI della surface `articoli`
- integrazione del campo configurabile `famiglia`
- eventuali test frontend o smoke test coerenti col task
- eventuale aggiornamento di:
  - `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
  - `docs/guides/BACKEND_BOOTSTRAP_AND_VERIFY.md`

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,easy]"
docker compose -f ../infra/docker/docker-compose.db.yml up -d
cp .env.example .env
alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
```

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

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto

## Implementation Notes

Direzione raccomandata:

- mantenere il campo `famiglia` ben separato visivamente dal blocco read-only Easy
- usare un controllo semplice e stabile, ad esempio `select`
- evitare di allargare subito il pannello di destra con altre configurazioni non richieste
- se utile, prevedere anche lo stato "nessuna famiglia assegnata"

---

## Completion Notes

### Summary

Aggiunto il feedback inline di salvataggio al campo `famiglia articolo` nella colonna destra della surface
`articoli`. Il ciclo di stato locale (`idle → saving → saved/error → idle`) è gestito internamente da
`ColonnaDettaglio` senza propagare stato al componente padre. La distinzione visiva tra dato Easy read-only
e dato interno configurabile è mantenuta tramite sezioni separate con heading differenziato.

### Files Changed

- `src/pages/surfaces/ProduzioneHome.tsx`:
  - `handleFamigliaChange` — rimosso try/catch interno, la funzione ora rilancia l'eccezione al chiamante
  - `ColonnaDettaglio` — aggiunto tipo `SaveStatus`, stato locale `saveStatus`, `useEffect` di reset al cambio articolo, `handleFamigliaSelect` asincrono con gestione feedback; select disabilitato durante il salvataggio; testo inline per ogni stato
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md` — portato a `In Use`; documentata sezione "Classificazione interna" con catalogo famiglie e pattern di feedback

### Dependencies Introduced

Nessuna nuova dipendenza.

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `npx tsc --noEmit` | Claude Code | Windows / Node | 0 errori |
| `npm run build` | Claude Code | Windows / Node | build verde, 96 moduli, 272 kB JS |
| `python -m pytest tests -q` (backend invariato) | Claude Code | Windows / .venv | 244 passed |

### Assumptions

- Il timeout del feedback "Salvato" è 2.5 s; "Errore" 3.5 s — valori arbitrari ragionevoli, non configurabili.
- Il reset del `saveStatus` al cambio articolo (via `useEffect` su `codice_articolo`) garantisce che il feedback non rimanga visibile quando si naviga a un altro articolo prima che il timeout scada.

### Known Limits

- Se il salvataggio fallisce, il valore selezionato nel `<select>` resta visivamente aggiornato ma il backend non ha salvato; l'utente deve ri-selezionare. Un rollback ottimistico richiederebbe stato aggiuntivo — fuori scope per questo task.

### Follow-ups

- Validazione backend che `famiglia_code` sia un codice presente in `articolo_famiglie` (attualmente accetta codici arbitrari).
- Eventuale badge famiglia nella colonna lista articoli per filtrare per famiglia.

## Completed At

2026-04-07

## Completed By

Claude Code
