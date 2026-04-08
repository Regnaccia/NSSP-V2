# UIX_SPEC_ARTICOLI - Variante a 2 colonne

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-08

## Purpose

Documentare come il pattern UIX multi-colonna standard viene applicato al caso `articoli`.

## Related Documents

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
- `docs/task/TASK-V2-022-famiglia-articoli.md`
- `docs/task/TASK-V2-023-ui-famiglia-articoli.md`
- `docs/task/TASK-V2-038-giacenza-articoli-nel-dettaglio-ui.md`

## Variant

- pattern adottato: `2 colonne`

## Column Model

### Colonna 1 - Lista articoli

Contiene:

- elenco completo articoli
- campo ricerca articolo
- filtro famiglia articolo
- selezione singola articolo

Requisiti UX minimi:

- lista scrollabile in modo indipendente
- ricerca sempre visibile e usabile con liste lunghe
- evidenza chiara dell'articolo selezionato

#### Filtro famiglia

Posizionato nella colonna sinistra, sotto il campo ricerca. Opzioni:

- `Tutte le famiglie` - mostra tutti gli articoli
- `Non configurati` - solo articoli senza famiglia assegnata (`famiglia_code = null`)
- una opzione per ogni famiglia del catalogo interno

Il filtro si combina con la ricerca: la ricerca opera sul subset gia filtrato per famiglia.
Il filtro e client-side; nessuna modifica al contratto Core/API e necessaria perche
`famiglia_code` e gia esposto in `ArticoloItem`.

### Colonna 2 - Configurazione articolo

Contiene:

- dati read-only dell'articolo selezionato esposti dal Core
- dati interni configurabili dell'articolo

#### Sezione "Classificazione interna"

Prima configurazione interna introdotta con `TASK-V2-022` e `TASK-V2-023`.

- campo: `famiglia articolo`
- controllo: `select` con catalogo controllato interno
- catalogo seed iniziale: `materia_prima`, `articolo_standard`, `speciale`, `barre`, `conto_lavorazione`
- valore opzionale: l'articolo puo non avere famiglia assegnata
- salvataggio via `PATCH /api/produzione/articoli/{codice}/famiglia`
- feedback inline: `idle | salvataggio | salvato | errore`

#### Sezione "Dati anagrafici - sola lettura (Easy)"

Tutti i campi provenienti da Easy tramite `sync_articoli` sono visualizzati in sola lettura.

#### Sezione "Giacenza - sola lettura (ODE)"

Estensione introdotta con `TASK-V2-038`.

Contiene:

- `on_hand_qty`
- `giacenza_computed_at`

Semantica:

- la giacenza proviene dal computed fact Core `inventory_positions`
- non e un dato Easy diretto
- la sezione serve come verifica visiva dell'allineamento Easy/ODE, non come UI magazzino dedicata

## Search Behavior

La ricerca articolo deve seguire il pattern definito in `DL-UIX-V2-004`.

Regole minime:

- ricerca per codice articolo
- ricerca per descrizione articolo
- input tollerante alle varianti dimensionali

Esempio:

- `8.7.40` deve essere trattato come equivalente a `8x7x40`

## Data Semantics

### Read-only

I dati provenienti da Easy o derivati dal Core a partire da Easy sono visualizzati come read-only.

### Configurable

I dati interni persistiti nel sistema V2 sono presentati come configurabili.

Il set preciso dei campi configurabili crescera per slice successivi del dominio `articoli`.

## Selection Flow

- nessun articolo selezionato -> colonna 2 in stato vuoto guidato
- articolo selezionato -> popolamento colonna 2
- cambio articolo -> refresh coerente del pannello di dettaglio/configurazione

## UX Notes

- la lista articoli deve restare consultabile anche con dataset ampi
- il layout non richiede una colonna intermedia se non esiste un secondo livello naturale di nesting
- la UI deve restare coerente con la shell multi-surface gia adottata in V2

## Notes

- Questa spec descrive il caso concreto `articoli` come variante a `2 colonne`.
- Aggiornata a `In Use` con `TASK-V2-023`.
- Estesa con `TASK-V2-038` per includere la giacenza read-only proveniente dal Core.

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
