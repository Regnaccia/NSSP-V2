# ODE V2 - Stato Progetto

## Date
2026-04-14

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha chiuso i primi stream operativi di:

- `logistica`
- `produzione/articoli`
- `produzioni`
- `planning candidates`
- `warnings` V1
- `production proposals` V1

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
- primi horizon planning gia introdotti:
  - `customer horizon` nel ramo customer-driven
  - `stock horizon` nella sola componente scorta `by_article`
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
  - export CSV batch
  - reconcile via `ODE_REF`
  - governance proposal logic tra `admin` e `articoli`

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-033`
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

## Task completati

Completati:

- `TASK-V2-001` -> `TASK-V2-114`

## Task aperti

- `TASK-V2-115` contratti Core/API per preview export EasyJob in `Production Proposals`
- `TASK-V2-116` tabella UI `Production Proposals` allineata alla preview export EasyJob
- `TASK-V2-117` prima logica proposal V1 `proposal_target_pieces_v1`
- `TASK-V2-118` modello/config `raw_bar_length_mm_enabled` e `raw_bar_length_mm`
- `TASK-V2-119` UI `famiglie` per `raw_bar_length_mm_enabled`
- `TASK-V2-120` UI `articoli` per `raw_bar_length_mm` e `proposal_full_bar_v1`
- `TASK-V2-121` Core `proposal_full_bar_v1`
- `TASK-V2-122` warning `MISSING_RAW_BAR_LENGTH`
- `TASK-V2-123` fix UI `articoli` per visibilita condizionata di `raw_bar_length_mm`

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
- `TASK-V2-100` customer horizon Core in `Planning Candidates`
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

## Task deferred

- `TASK-V2-079` integrazione warning nelle surface operative, parcheggiato per mantenere `Warnings` come modulo esplicito e autonomo

## Gap noti

- il mirror `sync_mag_reale` mantiene ancora la strategia `append_only + no_delete_handling`; il re-bootstrap di `TASK-V2-073` ha riallineato il dataset corrente, ma il fix strutturale resta aperto in [KNOWN_BUGS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/KNOWN_BUGS.md#L1)
- `criticita articoli` e ancora presente come surface attiva, ma ormai concettualmente superata da `Planning Candidates` + `Warnings`

## Prossima sequenza consigliata

I prossimi stream naturali sono:
- raffinare `Production Proposals` su:
  - preview export EasyJob in Core/API e UI
  - prima logica proposal minima `proposal_target_pieces_v1`
  - seconda logica proposal `proposal_full_bar_v1`
  - warning configurativo `MISSING_RAW_BAR_LENGTH`
  - logiche proposal piu ricche
  - eventuali regole di riapertura / nuovo ciclo proposal
  - possibili blocchi o segnali operativi legati ai warning
  - eventuale export audit piu ricco
- valutare piu avanti badge warning in:
  - `articoli`
  - `Planning Candidates` extra rispetto alla colonna warning gia introdotta

Valutazioni rinviate:

- `TASK-V2-079` badge warning in `articoli` e `Planning Candidates`

Non sono prioritari adesso:

- nuovo scaffolding sync
- nuovo refactor planning di base
- scoring o scheduling avanzato prima di raffinare `Production Proposals`

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
