# TASK-V2-065 - UI Planning Candidates V1

## Status
Todo

## Date
2026-04-10

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/UIX/specs/UIX_SPEC_PLANNING_CANDIDATES.md`
- `docs/decisions/ARCH/DL-ARCH-V2-022.md`
- `docs/decisions/ARCH/DL-ARCH-V2-025.md`
- `docs/decisions/ARCH/DL-ARCH-V2-026.md`
- `docs/task/TASK-V2-062-core-planning-candidates-v1.md`
- `docs/task/TASK-V2-064-core-effective-planning-policy-articoli.md`

## Goal

Introdurre la prima surface UI `Planning Candidates` V1 come vista operativa aggregata per articolo, basata sul Core planning gia disponibile.

## Prerequisite

Prima di eseguire questo task devono risultare completati:

- `TASK-V2-062`
- `TASK-V2-064`

`TASK-V2-063` e fortemente raccomandato a monte, perche prepara il modello policy necessario a `TASK-V2-064`.

## Context

Con `DL-ARCH-V2-025` la V2 ha definito `Planning Candidates` V1 come modulo:

- `customer-driven`
- aggregato per `article`
- basato su `future_availability_qty`

Con `DL-ARCH-V2-026` la V2 ha inoltre definito che le policy operative di planning devono essere lette tramite:

- default di famiglia
- override articolo
- valori effettivi esposti dal Core

Dopo il completamento di `TASK-V2-062` e `TASK-V2-064`, il backend puo esporre:

- candidate planning V1
- valori effettivi di policy utili al perimetro della vista

Serve quindi la prima UI operativa del modulo.

## Scope

### In Scope

- introdurre la surface UI `Planning Candidates` V1
- implementare la vista come tabella operativa a colonna unica, coerente con `UIX_SPEC_PLANNING_CANDIDATES`
- esporre almeno le colonne:
  - `Codice`
  - `Descrizione`
  - `Famiglia`
  - `Domanda aperta`
  - `Disponibilita attuale`
  - `Supply in corso`
  - `Disponibilita futura`
  - `Fabbisogno minimo`
- introdurre toolbar minima con:
  - ricerca per codice articolo
  - filtro famiglia
  - toggle `solo_in_produzione` basato su `effective_considera_in_produzione`
  - pulsante `Aggiorna`
- ordinamento iniziale consigliato:
  - `required_qty_minimum` decrescente
- aggiornare routing/navigation della nuova surface
- aggiornare la documentazione minima della nuova vista

### Out of Scope

- detail panel a destra
- score o ranking composito
- planning horizon
- slice temporali
- raggruppamenti avanzati
- drill-down per riga ordine
- editing di policy dalla vista planning
- introduzione della logica di aggregazione avanzata

## Constraints

- la UI deve consumare il read model Core planning, non ricalcolare la logica lato frontend
- il filtro `solo_in_produzione` deve usare i valori effettivi di policy, non la sola famiglia raw
- la view deve restare semplice e operativa, non una dashboard complessa
- non introdurre ancora logiche di aggregazione oltre la V1 aggregata per articolo
- evitare hardcode futuri su famiglie o comportamenti eccezionali

## Refresh / Sync Behavior

`Il task introduce o modifica un refresh semantico backend dedicato` solo se strettamente necessario.

Direzione preferita:

- riusare un refresh semantico backend gia esistente, se questo garantisce il riallineamento dei fact a monte del modulo
- se la surface richiede un refresh dedicato, questo va modellato come refresh semantico backend e non come chain tecnica ricostruita nella UI

Se la vista espone un pulsante `Aggiorna`, deve dichiarare esplicitamente:

- quale funzione semantica backend chiama
- se al termine ricarica solo la vista corrente
- quali fact risultano riallineati

## Acceptance Criteria

- esiste una nuova surface UI `Planning Candidates` V1
- la vista mostra i candidate aggregati per articolo usando il Core planning
- la toolbar include ricerca, filtro famiglia, toggle `solo_in_produzione` e `Aggiorna`
- il toggle `solo_in_produzione` usa `effective_considera_in_produzione`
- la vista ha almeno un ordinamento iniziale coerente con il fabbisogno planning
- la UI non ricalcola localmente `future_availability_qty` o la regola di candidate
- `npm run build` passa

## Deliverables

- nuova pagina/surface `Planning Candidates`
- aggiornamento routing/navigation
- eventuale wiring refresh coerente
- aggiornamento documentazione minima coerente

## Verification Level

`Mirata`

Questo task introduce una nuova surface UI ma non chiude ancora una milestone architetturale ampia.

Quindi:

- test mirati backend solo se cambia il contratto consumato
- build frontend obbligatoria
- niente full suite obbligatoria

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm install
```

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

- riusare il linguaggio e il livello di complessita della vista `criticita`
- trattare `Planning Candidates` come vista di spiegazione quantitativa semplice
- privilegiare leggibilita della tabella e velocita di scanning
- non introdurre ancora layout a 2 colonne o dettaglio laterale

## Documentation Handoff

Claude aggiorna solo questo task con completion notes ricche.
Il riallineamento di roadmap, overview, indici e guide trasversali viene fatto successivamente da Codex o da un revisore documentale.

---

## Completion Notes

Da compilare a cura di Claude Code quando il task viene chiuso.

## Completed At

YYYY-MM-DD

## Completed By

Claude Code
