# DL-UIX-V2-002 - Pattern standard multi-colonna per menu configurazioni

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 sta introducendo surface applicative che espongono:

- navigazione su entita o gruppi principali
- eventuali livelli figli o correlati
- pannelli di dettaglio o configurazione

Il primo caso concreto e stato `clienti/destinazioni`, ma il pattern non appartiene solo alla logistica.

Lo stesso impianto puo essere riusato anche per:

- anagrafiche configurabili di produzione, come `articoli`
- future schermate admin o operative con gerarchie naturali
- casi con nesting differente ma stessa esigenza di consultazione e configurazione progressiva

E quindi necessario fissare un pattern UIX generico, stabile e riusabile,
senza legarlo a una sola surface.

## Decision

La V2 adotta come pattern standard per i menu di configurazione una UI a colonne progressive.

Il layout puo usare:

- `2 colonne`
- `3 colonne`
- `4 colonne`

in funzione del nesting reale del caso specifico.

## 1. Principio generale

Ogni colonna rappresenta un livello di selezione o approfondimento.

Pattern base:

1. colonna 1 -> elenco entita principali
2. colonna 2 -> elementi figli o correlati, se esistono
3. colonna 3 -> dettaglio o configurazione dell'elemento selezionato
4. colonna 4 -> pannello avanzato o contesto secondario, solo se realmente necessario

Regola:

> Il numero di colonne deve derivare dal nesting reale del caso, non da una scelta estetica fissa.

## 2. Variazioni ammesse

### 2 colonne

Da usare quando il caso ha:

- un elenco principale
- un solo pannello di dettaglio o configurazione

Esempio naturale:

- `articoli -> configurazione articolo`

### 3 colonne

Da usare quando il caso ha:

- un elenco principale
- un secondo livello di selezione
- un pannello finale di dettaglio o configurazione

Esempio naturale:

- `clienti -> destinazioni -> configurazione destinazione`

### 4 colonne

Da usare solo quando esiste un quarto livello reale e stabile, ad esempio:

- entita principale
- sotto-entita
- dettaglio
- pannello tecnico o configurazione avanzata separata

La quarta colonna non deve essere introdotta per semplice comodita di layout.

## 3. Fonte dati ammessa

Le colonne devono consumare:

- read model Core
- API backend applicative

Non devono consumare direttamente:

- mirror `sync_*`
- tabelle tecniche di integrazione
- logiche di join costruite nel frontend

Regola:

> Il frontend usa contratti Core/API; i mirror sync non sono un contratto UI.

## 4. Relazione tra dati read-only e dati configurabili

Ogni schermata che adotta questo pattern deve distinguere chiaramente:

- dati sincronizzati o derivati in sola lettura
- dati interni configurabili

Regole:

- i dati provenienti da Easy restano read-only
- i dati interni modificabili devono essere presentati come tali
- la UI non deve mescolare semanticamente campi sorgente e campi interni

## 5. Comportamento di selezione

Ogni colonna dipende dalla selezione della colonna precedente.

Comportamenti minimi:

- nessuna selezione -> colonne successive in stato vuoto guidato
- selezione colonna N -> popola la colonna N+1 se prevista
- cambio selezione a monte -> reset coerente delle colonne a valle

## 6. Scroll e layout

Il pattern deve supportare colonne con contenuto lungo.

Regole:

- ogni colonna deve poter avere scroll indipendente quando necessario
- il layout non deve trasformarsi in una singola pagina lunga
- la leggibilita della selezione corrente deve restare evidente

## 7. Reusability del pattern

`DL-UIX-V2-002` definisce il pattern generale.

I casi specifici devono essere documentati in spec dedicate, ad esempio sotto:

- `docs/decisions/UIX/specs/`

Le spec descrivono:

- quale variante del pattern viene usata (`2`, `3`, `4` colonne)
- quali entita popolano ogni colonna
- quali dati sono read-only
- quali dati sono configurabili

## 8. Prima applicazione e casi futuri

Prima applicazione concreta:

- `clienti/destinazioni` -> variante a `3 colonne`

Caso successivo previsto:

- `articoli` -> variante a `2 colonne`

## Esclusioni (out of scope)

Questo DL NON definisce:

- styling visivo dettagliato
- comportamento responsive avanzato per ogni breakpoint
- contenuti specifici di una singola surface
- policy runtime di refresh o sync
- contratti backend di dettaglio per un caso concreto

## Consequences

### Positive

- coerenza trasversale tra surface configurative diverse
- maggiore riuso dei pattern UI senza copiare schermate
- separazione pulita tra DL UIX generico e casi specifici

### Negative / Trade-off

- richiede disciplina nel non forzare tutti i casi nello stesso numero di colonne
- impone una documentazione aggiuntiva per i casi specifici

## Impatto sul progetto

Questo DL diventa riferimento per:

- menu configurazioni basati su pattern multi-colonna
- future surface `produzione`, `logistica` e altre anagrafiche configurabili
- spec UIX specifiche di ciascun caso

## Notes

- Il pattern e volutamente generico: `2`, `3` o `4` colonne sono varianti dello stesso modello, non soluzioni concorrenti.
- I casi specifici devono vivere in spec dedicate, non dentro il DL generale.

## References

- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
