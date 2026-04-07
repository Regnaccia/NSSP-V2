# DL-UIX-V2-003 - Navigazione contestuale per surface

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 ha gia fissato che:

- la sidebar primaria deriva da `available_surfaces`
- una `surface` e un'area applicativa, non un ruolo e non una singola pagina
- il layout applicativo e persistente e condiviso

Con l'aumento del numero di funzioni interne a ogni surface, una sidebar che mostri solo le surface principali non e piu sufficiente.

Serve un pattern stabile che permetta di:

- selezionare una surface
- vedere le funzioni disponibili all'interno di quella surface
- mantenere separato il livello "surface" dal livello "funzione/route"

Senza questa distinzione, il rischio e:

- appiattire tutta la navigazione in un unico elenco poco leggibile
- confondere surface e route
- rendere difficile la crescita modulare di `admin`, `logistica` e future surface

## Decision

La V2 adotta una navigazione contestuale per surface.

Il modello UI e composto da:

- livello primario: selezione della surface
- livello secondario: elenco delle funzioni interne alla surface selezionata

La sidebar o frame di navigazione deve quindi poter mostrare, in modo coerente:

- le surface autorizzate
- le funzioni contestuali della surface attiva

## 1. Due livelli di navigazione

La navigazione applicativa distingue esplicitamente due livelli:

### 1.1 Livello primario

Contiene le surface disponibili, ad esempio:

- `admin`
- `logistica`
- future surface di dominio

### 1.2 Livello secondario

Contiene le funzioni o route interne della surface selezionata, ad esempio:

- per `admin`: utenti, ruoli, access management
- per `logistica`: clienti/destinazioni, future funzioni logistiche

Regola:

- il livello secondario dipende dalla surface attiva
- il livello secondario non sostituisce il livello primario

## 2. Surface e funzione restano concetti distinti

Una funzione interna:

- non e una surface
- non deve comparire come voce primaria globale
- vive dentro il perimetro della surface selezionata

Regola:

- `surface` = area applicativa
- `function/route` = navigazione interna della surface

## 3. Origine dei dati di navigazione

La sidebar primaria continua a derivare da `available_surfaces`.

Le funzioni contestuali di una surface possono essere definite inizialmente nel frontend, se sono puro wiring UI e il perimetro e gia autorizzato dalla surface stessa.

In futuro il backend potra esporre capabilities piu fini, ma non e un prerequisito per il primo slice.

Regola:

- autorizzazione di alto livello resta governata dal backend tramite surface
- navigazione secondaria iniziale puo essere frontend-defined

## 4. Comportamento della sidebar

Quando l'utente seleziona una surface:

- la surface diventa attiva nel frame applicativo
- compaiono le funzioni contestuali pertinenti
- la navigazione interna usa route coerenti con quella surface

Quando l'utente cambia surface:

- cambia anche il set di funzioni contestuali visibili
- il frame globale resta invariato

## 5. Coerenza con il routing

Ogni funzione contestuale deve corrispondere a una route interna della surface.

Regole:

- il routing resta unico a livello applicativo
- le route di funzione devono essere raggruppate semanticamente sotto la surface
- il cambio funzione non deve apparire come cambio di prodotto separato

## 6. Crescita modulare

Questo pattern deve permettere di crescere senza riprogettare la navigazione globale a ogni nuova funzione.

Esempio:

- `logistica` puo iniziare con `clienti/destinazioni`
- poi aggiungere `contatti logistici`, `corrieri`, `regole di spedizione`

La crescita avviene nel livello secondario, lasciando stabile il livello primario.

## 7. Confine con il backend

Il backend continua a:

- autenticare
- autorizzare l'accesso alle surface
- proteggere endpoint e dati

Il frontend continua a:

- mostrare solo surface disponibili in sessione
- mostrare le funzioni contestuali della surface attiva

La presenza di una funzione nella UI non sostituisce le guard backend.

## Esclusioni

Questo DL NON definisce:

- design visivo finale della sidebar
- struttura dati definitiva di menu/capabilities lato backend
- permessi fini per singola funzione
- comportamento kiosk
- responsive avanzato del menu contestuale

## Consequences

### Positive

- navigazione piu leggibile e scalabile
- crescita naturale delle funzioni interne per surface
- separazione piu chiara tra area applicativa e route interna

### Negative / Trade-off

- maggiore complessita del frame di navigazione
- necessita di mantenere coerente il mapping surface -> funzioni
- futuro possibile riallineamento se si introdurranno capabilities backend piu fini

## Impatto sul progetto

Questo DL diventa riferimento per:

- evoluzione della sidebar applicativa
- navigazione interna di `admin`, `logistica` e future surface
- task UI sulla navigazione contestuale

## Notes

- Nel primo slice e accettabile che le funzioni contestuali siano configurate nel frontend.
- Se in futuro emergera il bisogno di permessi piu fini, il modello potra essere esteso senza cambiare il concetto di base.

## References

- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
