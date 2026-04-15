# DL-ARCH-V2-033

## Titolo

`Production Proposals` V1 come workspace temporaneo generato da `Planning Candidates`, con persistenza solo all'export

## Data

2026-04-14

## Stato

Accepted

## Contesto

La prima implementazione di `Production Proposals` come inbox persistente downstream di `Planning Candidates` duplicava troppo il ruolo del planning:

- `Planning Candidates` mostrava gia il need con contesto sufficiente
- `Production Proposals` diventava una seconda lista quasi equivalente
- il workflow umano reale non era chiaro

Serveva un confine piu pulito:

- planning = triage del bisogno
- proposals = preparazione operativa dell'export

## Decisione

La V1 viene rifinita cosi:

- `Planning Candidates` resta l'unica inbox live del need
- l'operatore seleziona candidate direttamente in planning
- l'azione `Genera proposte` crea un `ProposalWorkspace` temporaneo
- il workspace congela lo snapshot dei candidate selezionati
- il workspace e modificabile solo fino all'export o all'abbandono
- chiudere senza export porta il workspace in stato `abandoned`
- la persistenza di lungo periodo inizia solo all'export
- lo storico persistente e composto dagli snapshot esportati
- il reconcile continua a lavorare via `ODE_REF`

## Regole principali

### Planning

- niente auto-generation di proposal da tutti i candidate
- niente stato persistente intermedio di ready queue in V1
- la selezione umana e transiente fino alla creazione del workspace

### Workspace

- stato:
  - `open`
  - `exported`
  - `abandoned`
- snapshot congelato dei candidate selezionati
- nessun drift da refresh planning successivi
- override quantitativi ammessi a livello workspace row

### Persistenza

- nessuna proposal persistente pre-export
- all'export:
  - si genera il CSV
  - si assegna `ODE_REF`
  - si persistono gli snapshot esportati

### Storico esportato

- workflow minimo:
  - `exported`
  - `reconciled`
  - `cancelled` solo come audit future-proof

Sono rimossi dal modello V1:

- `draft` persistente
- `validated` persistente
- auto-refresh proposal da planning
- auto-cancel dovuto alla scomparsa del candidate sorgente

## Conseguenze

### Positive

- sparisce la duplicazione tra planning e proposal
- il workflow umano e piu netto:
  - vedo il need
  - seleziono
  - genero workspace
  - esporto o abbandono
- planning resta la sola vista live del bisogno
- lo storico persistente coincide con il boundary vero di audit: l'export

### Negative

- il lavoro pre-export non e piu un oggetto persistente di lungo periodo
- il multi-user editing dello stesso workspace resta fuori scope
- eventuale rigenerazione da candidate aggiornato richiedera una decisione esplicita futura

## Contratti pubblici introdotti o aggiornati

- `POST /produzione/planning-candidates/generate-proposals-workspace`
- `GET /produzione/proposals/workspaces/{workspace_id}`
- `PATCH /produzione/proposals/workspaces/{workspace_id}/rows/{row_id}/override`
- `POST /produzione/proposals/workspaces/{workspace_id}/export`
- `POST /produzione/proposals/workspaces/{workspace_id}/abandon`
- `GET /produzione/proposals/exported`
- `GET /produzione/proposals/exported/{proposal_id}`
- `POST /produzione/proposals/exported/reconcile`

## Note attuative V1

- logiche proposal ancora governate da:
  - suite globale `admin`
  - assegnazione articolo
- qty base proposal:
  - `required_qty_total`
  - fallback tecnico a `required_qty_minimum` se necessario
- export solo CSV
- reconcile tramite mirror produzioni e `ODE_REF`
