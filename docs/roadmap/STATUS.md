# ODE V2 - Stato Progetto

## Date
2026-04-20

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha chiuso i primi stream operativi di:

- `logistica`
- `produzione/articoli`
- `produzioni`
- `planning candidates`
- `warnings` V1
- `production proposals` V1
- review generale di progetto e baseline di `architectural rebase` in-place

Sono oggi disponibili:

- backend base, auth browser e surface `admin`
- sync reale Easy read-only per `clienti`, `destinazioni`, `articoli`, `produzioni`, `MAG_REALE`, `righe ordine cliente`
- fact canonici quantitativi:
  - `inventory_positions`
  - `commitments`
  - `customer_set_aside`
  - `availability`
- refresh semantico backend `refresh_articoli()` con chain completa
- surface `articoli` con:
  - famiglia
  - override di planning policy
  - valori effettivi
  - `giacenza`
  - `customer_set_aside`
  - `committed_qty`
  - `availability_qty`
  - metriche stock policy:
    - `monthly_stock_base_qty`
    - `capacity_calculated_qty`
    - `capacity_effective_qty`
    - `target_stock_qty`
    - `trigger_stock_qty`
  - flag esplicito di attivazione stock policy:
    - `gestione_scorte_attiva`
    - `effective_gestione_scorte_attiva`
- pagina admin dedicata alla governance delle logiche stock
- surface `Planning Candidates` V2 con branching reale:
  - `by_article`
  - `by_customer_order_line`
- integrazione stock-driven nel ramo `by_article` con breakdown:
  - `customer_shortage_qty`
  - `stock_replenishment_qty`
  - `required_qty_total`
- separazione esplicita tra:
  - bisogno planning
  - rilascio immediato
  - priorita
- `customer_horizon` declassato a segnale UI / ranking
- `priority_score` introdotto nel read model planning come layer separato
- refinement finale di planning completato:
  - `stock_effective = max(stock_calculated, 0)`
  - `reason_code` / `reason_text`
  - `misura`
  - descrizione ordine primaria nel ramo per-riga
- refinement finale di leggibilita planning completato:
  - modello descrittivo unificato:
    - `description_parts`
    - `display_description`
  - descrizione ordine completa nel ramo `by_customer_order_line`
  - destinazione richiesta leggibile
  - badge famiglia
  - badge motivi sintetici con casi misti visibili ma non duplicati
  - colonna `Warnings` con warning articolo attivi
  - quick config modal articolo direttamente dalla vista planning
- modulo trasversale `Warnings` V1 con:
  - warning canonici unici
  - tipi iniziali:
    - `NEGATIVE_STOCK`
    - `INVALID_STOCK_CAPACITY`
  - prima surface dedicata `Warnings`
  - prima configurazione admin della visibilita
- primo slice `Production Proposals` V1 con:
  - workspace temporaneo generato da `Planning Candidates`
  - persistenza solo all'export
  - export `xlsx` EasyJob
  - reconcile via `ODE_REF`
  - governance proposal logic tra `admin` e `articoli`
- baseline architetturale di rebase fissata con:
  - moduli principali congelati
  - split concettuale `need vs release now`
  - logiche proposal reinterpretate come bundle di policy
  - ownership dati stabile tra finito, materiale grezzo, famiglia e admin
  - separazione esplicita tra `Domain Rebase` e `Backbone Hardening`

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-044`
- `UIX/` fino a `DL-UIX-V2-004`

Supporti attivi:

- `UIX/specs/`
- `docs/specs/`

Punti ormai stabili:

- separazione `sync / core / app / shared`
- Easy solo read-only
- refresh semantici backend con dipendenze interne
- logiche di dominio sopra fact canonici
- distinzione esplicita tra chiave articolo raw e canonica
- planning policy con default famiglia + override articolo
- `planning_mode` come vocabolario esplicito
- modulo `Warnings` come sistema trasversale unico
- stock policy V1 fissata come estensione minima del planning `by_article`
- modello/config stock policy V1 gia introdotto con default famiglia e override articolo
- `gestione_scorte_attiva` gia introdotto come flag esplicito separato dal solo `planning_mode`
- configurazione interna delle logiche stock V1 gia introdotta con `strategy_key`, `params_json` e capacity setup fissa
- algoritmo `monthly_stock_base_from_sales_v1` riallineato al profilo V1 con:
  - finestre multiple
  - percentile configurabile
  - filtro outlier z-score
  - `min_movements`
  - `rounding_scale`
  - perimetro esplicito `by_article`
- `Production Proposals` come workspace temporaneo downstream di `Planning Candidates`, con storico persistente solo all'export
- `architectural rebase` della V2 come linea guida attiva per i prossimi stream

## Task completati

Completati:

- `TASK-V2-001` -> `TASK-V2-133`
- `TASK-V2-137` -> `TASK-V2-155`

## Task aperti

- `TASK-V2-134` note fragment dedicato `FASCI xN` per la logica proposal multi-bar
- `TASK-V2-135` `Warnings` come modulo root di navigazione
- `TASK-V2-136` pagina admin unificata `Logic Config` a `3 colonne`

La backlog attiva non e piu una semplice sequenza di task proposal, ma e organizzata nei due stream:

- `Domain Rebase`
- `Backbone Hardening`

Documento guida:

- [REBASE_V2_BACKLOG_2026-04-15.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/roadmap/REBASE_V2_BACKLOG_2026-04-15.md#L1)

Ultimi task chiusi rilevanti:

- `TASK-V2-074` refinement finale Core `Planning Candidates`
- `TASK-V2-075` refinement finale UI `Planning Candidates`
- `TASK-V2-076` primo slice Core `Warnings` V1
- `TASK-V2-077` prima configurazione admin della warning visibility, ancora nel modello iniziale per surface
- `TASK-V2-078` prima surface UI `Warnings`
- `TASK-V2-081` warning visibility riallineata a `visible_to_areas`
- `TASK-V2-082` filtro della surface `Warnings` per area corrente, con bypass `admin`
- `TASK-V2-083` modello/config stock policy V1 con default famiglia e override articolo
- `TASK-V2-084` Core stock policy metrics V1
- `TASK-V2-085` integrazione stock-driven in `Planning Candidates by_article`
- `TASK-V2-086` configurazione logiche stock con strategy selection e parametri tunabili
- `TASK-V2-087` hardening algoritmo `monthly_stock_base_qty`
- `TASK-V2-088` allineamento finale stock policy V1
- `TASK-V2-089` UI articoli per metriche e configurazioni stock
- `TASK-V2-090` configurazione admin delle logiche stock V1
- `TASK-V2-091` warning `INVALID_STOCK_CAPACITY`
- `TASK-V2-092` fix formula `capacity_from_containers_v1`
- `TASK-V2-093` UI famiglie per default stock
- `TASK-V2-094` refinement admin stock logic con capacity params
- `TASK-V2-095` pagina admin separata per stock logic
- `TASK-V2-096` modello/config per `gestione_scorte_attiva`
- `TASK-V2-097` UI famiglie per `gestione_scorte_attiva`
- `TASK-V2-098` UI articoli per override `gestione_scorte_attiva`
- `TASK-V2-099` Core planning e stock policy riallineati a `effective_gestione_scorte_attiva`
- `TASK-V2-100` customer horizon flag nel Core `Planning Candidates`
- `TASK-V2-101` stock horizon cap sugli impegni della componente scorta
- `TASK-V2-102` filtri UI `Planning Candidates` per driver e customer horizon
- `TASK-V2-103` separazione Core tra `customer horizon` e `stock horizon`
- `TASK-V2-104` fix semantico UI/API del filtro `customer horizon`
- `TASK-V2-105` classificazione primaria `customer|stock` dei candidate `by_article`
- `TASK-V2-106` `required_qty_minimum` coerente nei candidate `stock-only`
- `TASK-V2-107` data richiesta in `Planning Candidates` con semantica distinta per riga ordine e ramo aggregato
- `TASK-V2-108` contratti Core planning per descrizione completa, destinazione richiesta e campi di leggibilita
- `TASK-V2-109` refinement UI `Planning Candidates` per badge, misura, descrizioni e destinazioni
- `TASK-V2-110` modello descrittivo unificato con `description_parts` e `display_description`
- `TASK-V2-111` enrichment Core/API degli warning articolo in planning
- `TASK-V2-112` colonna `Warnings` nella tabella planning
- `TASK-V2-113` quick config modal articolo dalla vista planning
- `TASK-V2-114` bridge case-insensitive planning -> articoli per lookup e write config
- `TASK-V2-137` shadow view planning con colonne sinistra e centrale
- `TASK-V2-138` refinement UI della shadow view planning secondo la spec UX congelata
- `TASK-V2-139` filtri workspace planning: scope, `Orizzonte cliente`, ricerche e sorting
- `TASK-V2-140` blocco `Parametri di calcolo` e scheda destra `Planning / Scorte`
- `TASK-V2-141` refinement wide-screen del blocco `Parametri di calcolo`
- `TASK-V2-142` test core su `12x8x25`
- `TASK-V2-143` ordini aperti e giacenza effettiva nella colonna centrale
- `TASK-V2-144` blocco `Cliente / Ordine` visibile anche nei casi stock-only
- `TASK-V2-145` rebase Core planning: `customer_horizon` fuori dal calcolo shortage e `priority_score` baseline
- `TASK-V2-146` docs cleanup e archive alignment
- `TASK-V2-147` rimozione della surface legacy `Criticita`
- `TASK-V2-148` review delle compatibilita legacy prima del cleanup codice
- `TASK-V2-149` contratto e implementazione di `priority_score_v1_basic`
- `TASK-V2-150` blocco `Priority` nella colonna centrale del workspace planning
- `TASK-V2-151` contratti Core/API per la scheda destra `Proposal`
- `TASK-V2-152` UI della colonna destra `Proposal` V1
- `TASK-V2-153` apertura automatica della colonna destra alla selezione del candidate
- `TASK-V2-154` refinement layout della colonna destra `Proposal`
- `TASK-V2-155` revisione del `proposal_status` bloccante su `line_reference`

## Task deferred

- `TASK-V2-079` integrazione warning nelle surface operative, parcheggiato per mantenere `Warnings` come modulo esplicito e autonomo

## Gap noti

- il mirror `sync_mag_reale` mantiene ancora la strategia `append_only + no_delete_handling`; il re-bootstrap di `TASK-V2-073` ha riallineato il dataset corrente, ma il fix strutturale resta aperto in [KNOWN_BUGS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/KNOWN_BUGS.md#L1)
- `criticita articoli` e ancora presente come surface attiva, ma ormai concettualmente superata da `Planning Candidates` + `Warnings`

## Prossima sequenza consigliata

I prossimi stream corretti sono:

1. `Domain Rebase`
   - chiarire il target planning:
     - bisogno semplice
     - `priority_score` separato
     - rimozione di `customer_horizon` dal Core
   - materializzare il passaggio UX a `Unified Planning Workspace`:
     - `Planning Candidates` come surface primaria
     - `proposal workspace panel` contestuale
     - storico export separato
   - fissare il contratto `Production Proposals` in termini di policy bundle:
     - `proposal_base_qty_policy`
     - `proposal_lot_policy`
     - `proposal_capacity_policy`
     - `proposal_customer_guardrail_policy`
     - `proposal_note_policy`
   - rileggere ogni nuovo task planning/proposal contro il baseline di [DL-ARCH-V2-039.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/decisions/ARCH/DL-ARCH-V2-039.md#L1)
2. `Project Cleanup`
   - riallineare docs e archive
   - togliere dalla navigation le surface legacy non piu operative
   - censire compatibilita/alias prima di rimuovere codice
   - chiudere `TASK-V2-134` per riallineare il `note_fragment` della multi-bar a `FASCI xN`
2. `Backbone Hardening`
   - strategia strutturale `MAG_REALE`
   - refresh fail-fast e freshness
   - gestione orfani `core_articolo_config`

Il cluster proposal `115-127` e stato gia implementato e va ora letto come compatibility slice, non come roadmap lineare.

Valutazioni rinviate:

- `TASK-V2-079` badge warning in `articoli` e `Planning Candidates`

Non sono prioritari adesso:

- nuove micro-logiche proposal isolate senza rebase contrattuale
- scoring o scheduling avanzato prima del rebase di dominio
- riscrittura `V3`

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
