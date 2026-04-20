# DL-ARCH-V2-041 - Unified Planning Workspace come surface operativa primaria

## Status
Active

## Date
2026-04-17

## Context

La V2 ha oggi due superfici strettamente collegate:

- `Planning Candidates`
- `Production Proposals`

Il dominio sotto il cofano e gia stato corretto:

- `Planning Candidates` e la inbox live del bisogno
- `Production Proposals` non e piu una seconda inbox persistente, ma un `workspace` temporaneo downstream del planning
- lo storico vero parte all'export e si riconcilia via `ODE_REF`

Tuttavia, lato user experience, le due pagine restano troppo vicine:

- `Planning Candidates` concentra molto contesto, segnali e triage
- `Production Proposals` eredita una parte rilevante dello stesso carico informativo
- il passaggio da una pagina all'altra genera duplicazione percettiva piu che una separazione chiara di workflow

Il rebase V2 ha gia fissato che:

- `need detection`
- `release feasibility now`
- `proposal release/export`

devono restare semanticamente distinti.

La correzione giusta quindi non e collassare il dominio, ma unificare la surface operativa.

## Decision

La surface operativa primaria della V2 diventa un `Unified Planning Workspace`.

Regola:

- `Planning Candidates` resta il nome e il punto di ingresso operativo principale
- la proposal non viene piu presentata come modulo operativo separato primario
- la proposal viene resa come `workspace panel` contestuale al candidate selezionato
- lo storico export/reconcile esce dalla surface operativa primaria e vive in una surface separata

## Contract

### 1. Cosa resta invariato

Restano validi come dominio/backend:

- `Planning Candidates` come inbox live del bisogno
- `ProposalWorkspace` temporaneo come snapshot congelato pre-export
- `Exported Proposal History` come storico persistente
- logiche proposal e relativa diagnostica locale:
  - `requested_proposal_logic_key`
  - `effective_proposal_logic_key`
  - `proposal_fallback_reason`
- export `xlsx`
- reconcile via `ODE_REF`

### 2. Cosa cambia lato surface

La surface operativa primaria diventa composta da tre aree:

- colonna sinistra:
  - inbox sintetica dei candidate
- colonna centrale:
  - dettaglio del candidate selezionato
- colonna destra:
  - `proposal workspace panel` dell'articolo in lavorazione

Questa surface deve permettere:

- triage del bisogno
- lettura dettagliata del candidate
- preview della proposta
- override e preparazione export
- costruzione di un batch leggero

senza richiedere navigazione verso una seconda pagina proposta per il lavoro operativo ordinario.

### 3. Batch model

La V1 del `Unified Planning Workspace` usa un modello di batch leggero.

Regola:

- la colonna sinistra supporta multi-selezione
- centro e destra lavorano su un candidate attivo alla volta
- la colonna destra mostra anche un riepilogo batch minimale

Non e richiesto, in questo slice, un editor massivo multi-riga dentro la stessa colonna destra.

### 4. Ruolo di `Production Proposals`

`Production Proposals` non scompare come dominio, ma cambia ruolo di product surface.

Diventa:

- compatibilita/backing surface del `ProposalWorkspace`
- base dati per il pannello proposal unificato
- sorgente dello storico export

Non resta la pagina operativa primaria del flusso umano.

### 5. Storico export separato

Lo storico export/reconcile deve vivere in una surface separata.

Naming target:

- `Proposal Export History`
  oppure
- `Export History`

Responsabilita:

- consultazione snapshot esportati
- stato `exported / reconciled / cancelled`
- reconcile e audit

Regola:

- il workspace operativo e lo storico export non devono convivere come due modalita paritarie della stessa surface primaria

## Consequences

### Positive

- si riduce la duplicazione percettiva tra `Candidates` e `Proposals`
- il flusso umano diventa lineare:
  - vedo bisogno
  - apro contesto
  - preparo proposta
  - aggiungo al batch
  - esporto
- il dominio gia costruito viene riusato, senza riscrivere il backend

### Constraints

- non va collassato il dominio `proposal` dentro il solo planning
- il pannello destro non deve diventare una seconda pagina completa miniaturizzata
- il batch v1 resta leggero
- lo storico export va tenuto separato dalla surface operativa principale

