# DL-UIX-V2-002 — Surface logistica clienti/destinazioni a 3 colonne

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 introduce come primo caso applicativo una rubrica operativa clienti/destinazioni.

Nel dominio logistico:

- il **cliente** rappresenta l’entità amministrativa
- la **destinazione** rappresenta l’entità operativa configurabile

La surface deve quindi consentire:

- navigazione efficiente tra clienti
- accesso rapido alle destinazioni associate
- consultazione e prima configurazione della destinazione selezionata

Una UI basata su tabella annidata cliente → destinazioni è utile per esplorazione,
ma non è sufficiente come modello finale di configurazione, perché le policy operative
sono legate soprattutto alla destinazione.

È quindi necessario fissare un layout che separi chiaramente:

- livello di navigazione clienti
- livello di selezione destinazioni
- livello di dettaglio/configurazione

## Decision

La V2 adotta per la surface logistica clienti/destinazioni un layout a **3 colonne persistenti**:

1. **colonna sinistra** → elenco clienti
2. **colonna centrale** → elenco destinazioni del cliente selezionato
3. **colonna destra** → scheda configurazione della destinazione selezionata

## 1. Ruolo concettuale delle entità

La surface riflette esplicitamente il seguente modello:

- il **cliente** è il contenitore amministrativo
- la **destinazione** è l’unità operativa primaria di configurazione

Conseguenza:

- la navigazione parte dal cliente
- la configurazione avviene sulla destinazione

## 2. Colonna sinistra — Elenco clienti

La colonna sinistra mostra l’elenco clienti disponibili.

Funzioni minime:

- lista clienti
- ricerca/filtro per:
  - codice cliente
  - nome/ragione sociale
- selezione singola cliente

La selezione di un cliente aggiorna la colonna centrale.

## 3. Colonna centrale — Elenco destinazioni

La colonna centrale mostra le destinazioni associate al cliente selezionato.

Funzioni minime:

- elenco destinazioni del cliente
- selezione singola destinazione
- visualizzazione sintetica di:
  - codice destinazione
  - ragione sociale / nome sede
  - località essenziale
  - nickname destinazione, se presente

La selezione di una destinazione aggiorna la colonna destra.

## 4. Colonna destra — Configurazione destinazione

La colonna destra mostra il dettaglio della destinazione selezionata.

Nella prima implementazione la colonna contiene:

### 4.1 Dati anagrafici read-only provenienti da Easy

- codice cliente
- codice destinazione
- ragione sociale / nome sede
- indirizzo
- CAP
- città
- provincia

Questi dati sono visualizzati ma non modificabili.

### 4.2 Primo dato interno configurabile

- `nickname_destinazione`

Il nickname destinazione è:

- interno al sistema
- separato dai dati Easy
- usato per leggibilità operativa

## 5. Stato iniziale della surface

Comportamento iniziale:

- se nessun cliente è selezionato, la colonna centrale e la destra restano in stato vuoto guidato
- alla selezione di un cliente, viene popolata la colonna centrale
- alla selezione di una destinazione, viene popolata la colonna destra

## 6. Relazione con dati sincronizzati e dati interni

La surface deve distinguere chiaramente:

- dati sincronizzati da Easy (read-only)
- dati interni applicativi (configurabili)

Regola:

- i dati Easy non sono modificabili nella UI
- i dati interni configurabili sono persistiti nel sistema interno

## 7. Evoluzione prevista

Questo layout è progettato per supportare estensioni future nella colonna destra, tra cui:

- contatto logistico
- corrieri abituali
- spedizione a carico
- flag avvisi automatici
- regole di approntamento

La prima implementazione deve però restare limitata al solo `nickname_destinazione`
come configurazione modificabile.

## 8. Pattern UI risultante

La surface adotta quindi il seguente pattern:

- **cliente** come livello di raggruppamento e navigazione
- **destinazione** come livello di configurazione operativa
- **scheda destra** come spazio di dettaglio e impostazione progressiva

## Esclusions (out of scope)

Questo DL NON definisce:

- styling visivo dettagliato
- comportamento responsive avanzato
- editing inline massivo
- bulk actions
- configurazioni logistiche avanzate oltre il nickname
- policy di refresh dati runtime

## Consequences

### Positive

- separazione chiara tra livello amministrativo e operativo
- buona leggibilità della navigazione
- configurazione scalabile nel tempo
- coerenza con il dominio logistico reale

### Negative / Trade-off

- richiede un layout più strutturato rispetto a una semplice tabella
- introduce stato UI multi-selezione (cliente + destinazione)
- richiede maggiore disciplina nella gestione delle dipendenze dati

## Impatto sul progetto

Questo DL diventa riferimento per:

- prima surface logistica clienti/destinazioni
- task frontend della rubrica operativa
- future estensioni configurative per destinazione

## Notes

- Questo DL formalizza la destinazione come unità operativa primaria della logistica.
- Il cliente resta il punto di accesso amministrativo e di raggruppamento.

## References

- DL-UIX-V2-001 — Navigazione applicativa multi-surface (Sidebar)
- DL-ARCH-V2-007 — Primo caso applicativo clienti/destinazioni
- DL-ARCH-V2-008 — Sync Execution Model & Freshness Policy