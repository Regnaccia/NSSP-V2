# Easy Integration Docs

Questa cartella raccoglie la documentazione tecnica delle entita lette da Easy in modalita read-only.

Scopo:

- rendere esplicita la sorgente Easy usata da ogni sync unit
- documentare la source identity
- documentare il mapping verso il target interno V2
- tracciare normalizzazioni tecniche consentite
- chiarire delete handling, dipendenze e note operative

Questi documenti non sostituiscono:

- i DL architetturali
- i task di implementazione
- il codice

Servono come specifica tecnica di integrazione per singola entita.

Regole:

- una mappatura per ogni entita Easy sincronizzata
- nessuna sezione deve introdurre logica di business Core
- l'accesso a Easy resta sempre read-only
- il documento deve parlare del target sync interno, non del modello Core finale

File presenti:

| File | Contenuto |
|------|-----------|
| [EASY_ARTICOLI.md](EASY_ARTICOLI.md) | Mapping tecnico iniziale di `ANAART` verso il target sync interno `articoli` |
| [catalog/README.md](catalog/README.md) | Catalogo machine-generated degli schemi Easy in formato JSON |
| [EASY_CLIENTI.md](EASY_CLIENTI.md) | Mapping tecnico iniziale di `ANACLI` verso il target sync interno `clienti` |
| [EASY_DESTINAZIONI.md](EASY_DESTINAZIONI.md) | Mapping tecnico iniziale di `POT_DESTDIV` verso il target sync interno `destinazioni` |
| [EASY_MAG_REALE.md](EASY_MAG_REALE.md) | Draft mapping tecnico di `MAG_REALE` come primo caso `append-only` con sync incrementale e rebuild completo futuro |
| [EASY_PRODUZIONI.md](EASY_PRODUZIONI.md) | Draft mapping tecnico di `DPRE_PROD` e `SDPRE_PROD` verso mirror sync separati per produzioni attive e storiche |
| [EASY_RIGHE_ORDINE_CLIENTE.md](EASY_RIGHE_ORDINE_CLIENTE.md) | Draft mapping tecnico di `V_TORDCLI` come primo mirror delle righe ordine cliente |
| [EASY_ENTITY_MAPPING_TEMPLATE.md](EASY_ENTITY_MAPPING_TEMPLATE.md) | Template base per la documentazione di una entita Easy |

Naming consigliato per le future entita:

- `EASY_ARTICOLI.md`
- `EASY_CLIENTI.md`
- `EASY_DESTINAZIONI.md`
- `EASY_MAG_REALE.md`
- `EASY_PRODUZIONI.md`
- `EASY_RIGHE_ORDINE_CLIENTE.md`
