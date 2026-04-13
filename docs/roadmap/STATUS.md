# ODE V2 - Stato Progetto

## Date
2026-04-13

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha chiuso i primi stream operativi di:

- `logistica`
- `produzione/articoli`
- `produzioni`
- `planning candidates`
- `warnings` V1

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
- surface `Planning Candidates` V2 con branching reale:
  - `by_article`
  - `by_customer_order_line`
- refinement finale di planning completato:
  - `stock_effective = max(stock_calculated, 0)`
  - `reason_code` / `reason_text`
  - `misura`
  - descrizione ordine primaria nel ramo per-riga
- modulo trasversale `Warnings` V1 con:
  - warning canonici unici
  - primo tipo `NEGATIVE_STOCK`
  - prima surface dedicata `Warnings`
  - prima configurazione admin della visibilita

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-030`
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

## Task completati

Completati:

- `TASK-V2-001` -> `TASK-V2-082`

Ultimi task chiusi rilevanti:

- `TASK-V2-074` refinement finale Core `Planning Candidates`
- `TASK-V2-075` refinement finale UI `Planning Candidates`
- `TASK-V2-076` primo slice Core `Warnings` V1
- `TASK-V2-077` prima configurazione admin della warning visibility, ancora nel modello iniziale per surface
- `TASK-V2-078` prima surface UI `Warnings`
- `TASK-V2-081` warning visibility riallineata a `visible_to_areas`
- `TASK-V2-082` filtro della surface `Warnings` per area corrente, con bypass `admin`

## Task aperti

- `TASK-V2-083` modello/config stock policy V1
- `TASK-V2-084` Core stock policy metrics V1
- `TASK-V2-085` integrazione stock-driven in `Planning Candidates by_article`

## Task deferred

- `TASK-V2-079` integrazione warning nelle surface operative, parcheggiato per mantenere `Warnings` come modulo esplicito e autonomo

## Gap noti

- il mirror `sync_mag_reale` mantiene ancora la strategia `append_only + no_delete_handling`; il re-bootstrap di `TASK-V2-073` ha riallineato il dataset corrente, ma il fix strutturale resta aperto in [KNOWN_BUGS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/KNOWN_BUGS.md#L1)
- `criticita articoli` e ancora presente come surface attiva, ma ormai concettualmente superata da `Planning Candidates` + `Warnings`

## Prossima sequenza consigliata

I prossimi stream naturali sono:

- attuare la stock policy V1:
  - `TASK-V2-083`
  - `TASK-V2-084`
  - `TASK-V2-085`
- poi decidere se aprire `Production Proposals` sopra planning+scorte o direttamente sul planning attuale

Valutazioni rinviate:

- `TASK-V2-079` badge warning in `articoli` e `Planning Candidates`

Non sono prioritari adesso:

- nuovo scaffolding sync
- nuovo refactor planning di base
- scoring o horizon temporale prima di chiudere `Warnings`

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
