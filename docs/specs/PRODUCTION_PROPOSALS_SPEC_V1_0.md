# PRODUCTION_PROPOSALS_SPEC_V1_0

## 1. Contesto

Il sistema dispone oggi di:

- fact canonici ODE
- `Planning Candidates` come inbox live del bisogno
- `Warnings` come contesto anomalia separato
- stock policy V1 sul ramo `by_article`
- sync produzioni Easy e riconciliazione via note

Il punto corretto del flusso e:

```text
Easy facts
-> ODE canonical facts
-> ODE Planning Candidates
-> selezione operatore in Planning Candidates
-> ODE Proposal Workspace temporaneo
-> export XLSX
-> ODE Exported Proposal History
-> Easy execution
-> ODE sync produzioni
-> ODE reconcile via ODE_REF
```

Nel baseline architetturale post-rebase, `Production Proposals` resta downstream del planning e non ridefinisce da solo la fattibilita di rilascio.

## 2. Obiettivo del modulo

`Production Proposals` non e piu una seconda inbox persistente del need.

La V1 deve:

- partire da candidate selezionati esplicitamente in `Planning Candidates`
- congelare uno snapshot temporaneo dei candidate selezionati
- permettere override quantitativi prima dell'export
- esportare le righe del workspace come file `xlsx` compatibile con EasyJob
- persistere solo lo storico esportato
- riconciliare lo storico esportato via `ODE_REF`

## 3. Confine tra Planning e Proposals

### Planning Candidates

Resta:

- inbox live del bisogno
- superficie di triage
- punto di selezione dei candidate
- luogo corretto in cui distinguere:
  - bisogno eventuale
  - quantita lanciabile ora

Aggiunge:

- selezione multipla
- azione `Genera proposte`

Non introduce:

- stato persistente di presa in carico
- proposal persistenti pre-export

### Production Proposals

Diventa:

- `workspace` temporaneo quando aperto da planning
- storico persistente degli export quando aperto senza `workspace_id`

Regola di confine:

- `Planning Candidates` risponde a `is there a need?`
- `Production Proposals` risponde a `what do we release/export?`

La semantica `release now` non deve nascere solo come side effect di una proposal logic.

## 4. Workspace temporaneo

Nuova entita applicativa:

- `ProposalWorkspace`

Campi minimi:

- `workspace_id`
- `status`:
  - `open`
  - `exported`
  - `abandoned`
- `created_at`
- `expires_at`
- `updated_at`

Il workspace contiene righe congelate derivate dai candidate selezionati.

## 5. Riga di workspace

Ogni riga mantiene almeno:

- `source_candidate_id`
- `planning_mode`
- `article_code`
- `primary_driver`
- `required_qty_minimum`
- `required_qty_total`
- `customer_shortage_qty`
- `stock_replenishment_qty`
- `display_description`
- `requested_delivery_date`
- `requested_destination_display`
- `active_warning_codes`
- `proposal_logic_key`
- `proposal_logic_params_snapshot`
- `proposed_qty`
- `override_qty`
- `override_reason`
- `final_qty`

Regola quantitativa:

```text
base_qty = required_qty_total
final_qty = override_qty se presente, altrimenti proposed_qty
```

Compatibilita:

- se un candidate legacy non valorizza `required_qty_total`, e ammesso fallback tecnico a `required_qty_minimum`

## 6. Freeze dei candidate

Quando l'utente clicca `Genera proposte`:

- il backend riceve `source_candidate_id[]`
- rilegge i candidate correnti
- congela solo quelli ancora presenti
- scarta quelli mancanti e li riporta nel risultato

Conseguenze:

- il workspace e stabile
- refresh successivi di planning non modificano il workspace
- planning resta la sola vista live del bisogno

## 7. Logiche proposal

La V1 mantiene il pattern gia usato altrove:

- suite globale configurabile in `admin`
- assegnazione logica e parametri specifici a livello articolo
- nessun default famiglia in V1

Campi articolo:

- `proposal_logic_key`
- `proposal_logic_article_params`

### Rebase concettuale delle logiche proposal

Il modello target del rebase non e un elenco aperto di `proposal_logic_key` monolitiche.

Le logiche proposal devono essere ragionate come bundle di policy su assi distinti:

- `proposal_base_qty_policy`
- `proposal_lot_policy`
- `proposal_capacity_policy`
- `proposal_customer_guardrail_policy`
- `proposal_note_policy`

Compatibilita a breve termine:

- `proposal_logic_key` resta la compatibility surface reale in V2
- le key esistenti vanno reinterpretate come bundle impliciti

Mapping concettuale iniziale:

- `proposal_target_pieces_v1`
  - base qty: `required_qty_total`
  - lot: `pieces`
  - capacity: `none`
  - customer guardrail: `cover_customer_shortage`
  - note: `none`
- `proposal_full_bar_v1`
  - base qty: `required_qty_total`
  - lot: `full_bar`
  - capacity: `strict_capacity`
  - customer guardrail: `never_undercover_customer`
  - note: `bar_count`
- `proposal_full_bar_v2_capacity_floor`
  - base qty: `required_qty_total`
  - lot: `full_bar`
  - capacity: `capacity_floor`
  - customer guardrail: `never_undercover_customer`
  - note: `bar_count`

Nuovi task proposal non devono piu introdurre una nuova `proposal_*_vN` senza dichiarare esplicitamente su quale asse di policy intervengono.

Prima logica V1:

- `proposal_target_pieces_v1`

Semantica della prima logica:

- propone esattamente i pezzi mancanti al target
- `proposed_qty = required_qty_total`
- `note_fragment = null`

Ruolo della prima logica:

- baseline minima della V1
- fallback semplice e sempre valido anche in scenari futuri piu ricchi

Seconda logica V1:

- `proposal_full_bar_v1`

Semantica della seconda logica:

- lavora a barre intere di materiale
- risolve il `materiale_grezzo_codice` dell'articolo finito
- legge `raw_bar_length_mm` sull'articolo materiale grezzo associato
- usa i dati materiale:
  - `quantita_materiale_grezzo_occorrente`
  - `quantita_materiale_grezzo_scarto`
- produce un `note_fragment` sintetico:
  - `BAR xN`

Configurazione collegata:

- famiglia:
  - `raw_bar_length_mm_enabled`
  - abilita la configurabilita del campo barra sulle famiglie di materiale grezzo, non la scelta della logica
- articolo:
  - `raw_bar_length_mm` sull'articolo materiale grezzo
  - `proposal_logic_key`

Formula canonica:

```text
usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto
pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
bars_required = ceil(required_qty_total / pieces_per_bar)
proposed_qty = bars_required * pieces_per_bar
note_fragment = "BAR x{bars_required}"
```

Check capienza:

```text
availability_qty + proposed_qty <= capacity_effective_qty
```

Fallback obbligatorio a `proposal_target_pieces_v1` se:

- l'articolo finito non risolve un `materiale_grezzo_codice` valido
- `raw_bar_length_mm` manca sul materiale grezzo associato
- `usable_mm_per_piece <= 0`
- `pieces_per_bar <= 0`
- la proposta a barre sfora `capacity_effective_qty`
- la proposta a barre porterebbe a sotto-coprire `customer_shortage_qty`

Regola esplicita:

- `proposal_full_bar_v1` non deve mai proporre meno di `customer_shortage_qty`
- in V1 non e ammesso overflow di capienza
- in V1 non si blocca la proposta per config barra mancante sul materiale grezzo: si fa fallback a pezzi

Terza logica proposal:

- `proposal_full_bar_v2_capacity_floor`

Semantica della terza logica:

- mantiene lo stesso modello dati della `proposal_full_bar_v1`
- prova prima l'arrotondamento `ceil`
- se `ceil` sfora la capienza, prova una riduzione `floor`
- usa `floor` solo se resta sotto capienza e non sotto-copre il cliente

Formula:

```text
usable_mm_per_piece = quantita_materiale_grezzo_occorrente + quantita_materiale_grezzo_scarto
pieces_per_bar = floor(raw_bar_length_mm / usable_mm_per_piece)
bars_ceil = ceil(required_qty_total / pieces_per_bar)
qty_ceil = bars_ceil * pieces_per_bar
bars_floor = floor(required_qty_total / pieces_per_bar)
qty_floor = bars_floor * pieces_per_bar
```

Policy:

- se `availability_qty + qty_ceil <= capacity_effective_qty`, usare `qty_ceil`
- altrimenti tentare `qty_floor`
- `qty_floor` e ammesso solo se:
  - `bars_floor > 0`
  - `availability_qty + qty_floor <= capacity_effective_qty`
  - se esiste `customer_shortage_qty`, allora `qty_floor >= customer_shortage_qty`
- se anche `floor` non e ammissibile, fallback a `proposal_target_pieces_v1`

Nota:

- il frammento note resta `BAR xN`, dove `N` e il numero di barre effettivamente usato
- questa logica e distinta dalla `proposal_full_bar_v1`, non ne cambia la semantica

## 7B. Diagnostica locale della logica proposal

Il workspace proposal deve distinguere tra:

- logica richiesta sull'articolo
- logica effettivamente applicata alla riga
- eventuale motivo di fallback

Campi minimi locali al modulo `Production Proposals`:

- `requested_proposal_logic_key`
- `effective_proposal_logic_key`
- `proposal_fallback_reason`

Questa diagnostica:

- non appartiene al modulo `Warnings`
- non introduce warning canonici cross-module
- serve a spiegare perche una riga proposal e stata calcolata con una logica diversa da quella richiesta

Esempi iniziali di `proposal_fallback_reason`:

- `missing_raw_bar_length`
- `invalid_usable_mm_per_piece`
- `pieces_per_bar_le_zero`
- `capacity_overflow`
- `customer_undercoverage`

Regola:

- se `requested_proposal_logic_key != effective_proposal_logic_key`, `proposal_fallback_reason` deve essere valorizzato
- se non c'e fallback, `proposal_fallback_reason = null`

## 8. Chiusura senza export

Regola operativa:

- se il workspace viene chiuso senza export, viene `abandoned`
- non resta alcuna proposal persistente pre-export
- i candidate continuano a vivere normalmente in planning

Il sistema puo anche abbandonare automaticamente workspace scaduti.

## 9. Persistenza al boundary di export

La persistenza di lungo periodo inizia all'export.

Entita persistenti V1:

- `ProductionProposalExportBatch`
- snapshot esportati in `core_production_proposals`

Ogni snapshot esportato conserva:

- i campi principali del workspace row
- `ode_ref`
- `export_batch_id`
- stato reconcile

## 10. Workflow V1

### Workflow workspace

- `open`
- `exported`
- `abandoned`

### Workflow storico esportato

- `exported`
- `reconciled`
- `cancelled` solo per eventuale gestione futura di audit, non per drift dal planning

Sono esplicitamente rimossi:

- `draft` persistente
- `validated` persistente
- auto-cancel dovuto alla scomparsa del candidate
- auto-refresh proposal da planning

## 11. Export V1

Il formato V1 canonico di export non e CSV.

Il formato reale target e:

- file `xlsx`
- un singolo sheet
- una riga per ogni workspace row

### 11.1 Colonne XLSX EasyJob

Le colonne V1 sono:

- `cliente`
- `codice`
- `descrizione`
- `immagine`
- `misura`
- `quantità`
- `materiale`
- `mm_materiale`
- `ordine`
- `note`
- `user`

### 11.2 Mapping colonna per colonna

- `cliente`
  - se il candidate contiene componente `customer`: `requested_destination_display`
  - altrimenti: `MAGAZZINO`
- `codice`
  - `article_code`
- `descrizione`
  - serializzazione di `description_parts` come literal Python-list:
    - `['riga_1', 'riga_2', ..., 'riga_n']`
- `immagine`
  - `codice_immagine`
- `misura`
  - `misura_articolo`
- `quantità`
  - `final_qty`
- `materiale`
  - `materiale_grezzo_codice`
- `mm_materiale`
  - `quantita_materiale_grezzo_occorrente`
- `ordine`
  - `order_reference/line_reference`
  - se `line_reference` manca nel ramo customer: errore bloccante di export
  - se il candidate e `stock-only`: vuoto
- `note`
  - `nota_business + ODE_REF`
- `user`
  - username operatore export
  - opzionale

### 11.3 Regola `note`

La nota e deterministica.

Se il candidate contiene componente `customer`:

- prefisso da data consegna:
  - `CONS: dd/mm/yyyy`
- poi eventuale output testuale della logica di produzione
- chiusura con `ODE_REF`

Se il candidate e `stock-only`:

- nessun prefisso consegna
- eventuale output testuale della logica di produzione
- chiusura con `ODE_REF`

Per `proposal_full_bar_v1`:

- l'output testuale della logica e:
  - `BAR xN`

### 11.4 Vincoli di validazione export

Il writer `xlsx` deve bloccare l'export se:

- il candidate contiene componente `customer`
- `order_reference` o `line_reference` non consentono di costruire `ordine`

La validazione e bloccante sull'intero batch.

### 11.5 Persistenza ed export

`ODE_REF` viene assegnato al momento dell'export.

Dopo export:

- il workspace passa a `exported`
- gli snapshot esportati entrano nello storico persistente

## 12. Reconcile V1

Il reconcile V1 opera solo sullo storico esportato:

```text
ODE export XLSX
-> Easy crea produzione
-> ODE sync produzioni
-> match via ODE_REF
```

## 13. Warnings

`Warnings` resta separato.

Il workspace e lo storico esportato possono mostrare:

- `active_warning_codes`
- badge sintetici

Warning rilevante introdotto dal dominio `full bar`:

- `MISSING_RAW_BAR_LENGTH`
  - famiglia richiede `raw_bar_length_mm`
  - articolo non configurato correttamente

Ma:

- non ricalcolano warning
- non ne possiedono il lifecycle
- non introducono blocchi automatici in V1

## 14. Surface V1

### Planning Candidates

Azioni nuove:

- selezione righe
- `Genera proposte`

### Production Proposals

Modalita:

- `workspace mode` se aperta con `workspace_id`
- `history mode` altrimenti

Workspace mode espone:

- righe congelate con preview quasi 1:1 del tracciato export EasyJob
- override qty / reason
- `Esporta`
- `Chiudi senza esportare`

History mode espone:

- storico esportato
- warning sintetici
- `ode_ref`
- stato di reconcile

### 14.1 Preview export nella tabella proposals

Prima dell'introduzione del writer `xlsx`, la surface `Production Proposals` deve gia rendere visibile il tracciato di export.

La tabella workspace-oriented deve quindi esporre come colonne principali:

- `cliente`
- `codice`
- `descrizione`
- `immagine`
- `misura`
- `quantità`
- `materiale`
- `mm_materiale`
- `ordine`
- `note`
- `user`
- `warnings`

Campi non strettamente necessari alla preview export possono essere rimossi dalla tabella principale o relegati a dettaglio secondario, ad esempio:

- `planning_mode`
- `primary_driver`
- `required_qty_minimum`
- breakdown quantitativi interni del planning

### 14.2 Regola di rendering UI per `descrizione`

La semantica dati resta:

- serializzazione literal Python-list nel file export

La regola di rendering UI invece e diversa:

- la tabella proposal non mostra la repr della lista
- la `descrizione` viene renderizzata come campo multilinea
- ogni elemento di `description_parts` occupa una riga visiva distinta

Questa distinzione e intenzionale:

- storage/export: formato compatibile col template EasyJob
- UI: formato leggibile dall'operatore

## 15. Principio guida finale

> `Planning Candidates` resta la sola inbox live del bisogno. `Production Proposals` diventa un workspace temporaneo generato da selezione umana, e solo l'export produce lo storico persistente e riconciliabile via `ODE_REF`.
