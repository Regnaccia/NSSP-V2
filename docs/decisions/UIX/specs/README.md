# UIX Specs

Questa cartella contiene le specifiche UIX dei casi applicativi concreti.

Regola:

- i `DL-UIX` fissano pattern generali e riusabili
- le `specs` descrivono come quel pattern viene istanziato in una specifica surface o funzione

Esempi tipici:

- variante a `3 colonne` per `clienti/destinazioni`
- variante a `2 colonne` per `articoli`

Le specs non sostituiscono:

- i DL UIX generali
- i task di implementazione
- i contratti backend/Core

Servono a documentare:

- variante di layout adottata
- entita presenti in ogni colonna
- distinzione tra dati read-only e dati configurabili
- stati vuoti e comportamento di selezione

File presenti:

| File | Contenuto |
|------|-----------|
| [UIX_SPEC_ARTICOLI.md](UIX_SPEC_ARTICOLI.md) | Istanziazione del pattern multi-colonna per il caso `articoli`, nella variante a `2 colonne` |
| [UIX_SPEC_CLIENTI_DESTINAZIONI.md](UIX_SPEC_CLIENTI_DESTINAZIONI.md) | Istanziazione del pattern multi-colonna per la surface logistica clienti/destinazioni |
| [UIX_SPEC_PRODUZIONI.md](UIX_SPEC_PRODUZIONI.md) | Istanziazione del pattern multi-colonna per la surface `produzioni`, nella variante consultiva a `2 colonne` |
