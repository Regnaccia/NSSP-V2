# DL-ARCH-V2-034

## Titolo

Contratto di export `xlsx` EasyJob per `Production Proposals`

## Data

2026-04-14

## Stato

Accepted

## Contesto

Il primo slice `Production Proposals` era stato implementato con export tecnico `csv`.

La verifica sul file reale di import EasyJob mostra invece che il target corretto e:

- file `xlsx`
- un tracciato colonne specifico
- contenuti business-oriented, non solo campi tecnici interni ODE

Serve quindi fissare il contratto di export prima di evolvere ulteriormente il modulo.

## Decisione

Il formato canonico di export V1 verso EasyJob e:

- `xlsx`
- singolo sheet
- una riga per ogni workspace row esportata

## Mapping colonne

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

## Regole di mapping

- `cliente`
  - `requested_destination_display` se il candidate contiene componente customer
  - altrimenti `MAGAZZINO`
- `codice`
  - `article_code`
- `descrizione`
  - `description_parts` serializzata come literal Python-list
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
  - vuoto per stock-only
- `note`
  - nota business deterministica + `ODE_REF`
- `user`
  - username operatore export
  - opzionale

## Regola bloccante su `ordine`

Nel ramo customer:

- `line_reference` non e opzionale
- se `ordine` non puo essere costruito come `order_reference/line_reference`, l'export fallisce

Questa validazione e bloccante per il batch.

## Regola `note`

La nota e composta in forma deterministica:

- se c'e componente customer:
  - prefisso `CONS: dd/mm/yyyy`
- poi eventuale output sintetico della logica di produzione
- chiusura con `ODE_REF`

La V1 fissa anche che:

- `ODE_REF` deve sempre essere preservato nella nota finale
- il fragment prodotto dalla logica proposal deve essere append-only rispetto alla struttura della nota

## Preview UI

Prima del writer `xlsx`, `Production Proposals` deve gia rendere visibile la preview quasi 1:1 del tracciato export.

La tabella principale del workspace deve quindi privilegiare le colonne export:

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

Campi interni di planning non strettamente necessari alla preview possono essere declassati a vista secondaria.

## Regola di rendering UI per `descrizione`

La decisione separa:

- formato export
- formato di presentazione UI

Quindi:

- nell'export `descrizione` resta una literal Python-list
- nella UI proposal la stessa informazione viene resa come testo multilinea
- ogni item di `description_parts` occupa una riga visiva distinta

## Conseguenze

### Positive

- il contratto EasyJob e esplicito
- `Production Proposals` puo evolvere verso un export realmente usabile
- reconcile e note business condividono una stessa struttura deterministica

### Negative

- il writer export deve conoscere piu campi articolo rispetto al primo slice tecnico
- l'assenza di `line_reference` nei casi customer diventa un hard error operativo

## Note attuative V1

- il writer dovra passare da `csv` a `xlsx`
- il serializzatore `descrizione` usa literal Python-list, non JSON
- `ODE_REF` resta la chiave di reconcile
