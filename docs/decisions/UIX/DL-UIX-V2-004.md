# DL-UIX-V2-004 - Normalizzazione della ricerca articoli

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La ricerca articoli nella V2 deve restare veloce e tollerante rispetto alle convenzioni di scrittura usate dagli utenti.

Nel dominio attuale molti articoli hanno descrizioni o riferimenti dimensionali del tipo:

- `8x7x40`

Nella pratica operativa gli utenti possono pero digitare varianti equivalenti, ad esempio:

- `8.7.40`
- `8 x 7 x 40`
- `8 X 7 X 40`

Senza una normalizzazione esplicita, la UX della ricerca articolo diventa fragile e richiede di ricordare un solo formato esatto.

## Decision

La V2 introduce una normalizzazione standard degli input di ricerca articolo.

Per tutti i campi ricerca articolo, la UI deve trattare i separatori dimensionali alternativi come equivalenti al separatore canonico `x`.

## 1. Ambito di applicazione

Questa regola vale per:

- campo ricerca principale dell'anagrafica articoli
- eventuali futuri campi di ricerca articolo in altre surface

Non vale automaticamente per:

- campi non legati alla ricerca articolo
- form di configurazione articolo
- valori salvati o persistiti

## 2. Regola di normalizzazione

Prima di eseguire il filtro o inviare la query di ricerca, l'input articolo deve essere normalizzato.

Normalizzazione minima richiesta:

- trim degli spazi iniziali e finali
- conversione di `.` in `x`
- normalizzazione di varianti con spazi intorno al separatore verso `x`
- confronto case-insensitive sul token normalizzato

Esempi equivalenti:

- `8x7x40`
- `8.7.40`
- `8 x 7 x 40`
- `8 X 7 X 40`

## 3. Obiettivo della normalizzazione

La normalizzazione serve a migliorare la tolleranza della ricerca, non a reinterpretare semanticamente il dato.

Regola:

> La UI normalizza l'input di ricerca, ma non modifica il valore sorgente dell'articolo.

## 4. Relazione con backend e Core

Nel primo slice la normalizzazione puo vivere nel frontend se il filtro e locale o UI-driven.

Se in futuro la ricerca verra delegata al backend, la stessa regola dovra essere mantenuta coerente nel contratto di ricerca.

## 5. Confine della decisione

Questo DL non definisce:

- la logica di ranking dei risultati
- la strategia definitiva di ricerca full-text
- la ricerca fuzzy generale su tutti i campi articolo

Definisce solo una regola UX stabile di tolleranza sull'input articolo.

## Esclusioni

Questo DL NON definisce:

- parsing semantico delle misure
- validazione dei campi articolo
- ricerca per altri domini non articolo
- persistenza di versioni normalizzate del dato

## Consequences

### Positive

- ricerca articolo piu tollerante e naturale
- riduzione degli errori dovuti alla forma del separatore
- regola riusabile in piu schermate articolo

### Negative / Trade-off

- introduce una piccola logica di normalizzazione da mantenere coerente tra client e backend se il contratto evolvera

## Impatto sul progetto

Questo DL diventa riferimento per:

- future surface UI di ricerca articoli
- eventuali filtri articolo in produzione o magazzino
- specifiche UIX dedicate al caso `articoli`

## Notes

- Il separatore canonico scelto per la UX e `x`.
- La normalizzazione riguarda l'input di ricerca, non il dato sorgente mostrato o sincronizzato.

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
