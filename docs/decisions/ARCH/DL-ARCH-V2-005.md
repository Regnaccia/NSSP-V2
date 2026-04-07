# DL-ARCH-V2-005 - Definizione di surfaces applicative

## Status
Approved

## Date
2026-04-07

## Context

Con `DL-ARCH-V2-004` la V2 ha introdotto il modello di accesso composto da:

- identita utente
- ruoli utente
- canale di accesso client

Nel testo di quel DL compare anche il concetto di:

- `available_surfaces`

ma senza una definizione architetturale autonoma e stabile.

Questo crea un rischio di ambiguita nella documentazione e nei task successivi:

- usare `surface` come sinonimo di ruolo
- usare `surface` come sinonimo di pagina frontend
- usare `surface` come sinonimo di permesso tecnico
- rendere fragile il routing iniziale post-login
- accoppiare troppo presto il modello di autorizzazione al layout UI

La V2 ha quindi bisogno di fissare in modo esplicito cosa sia una `surface`,
cosa non sia, e come si relazioni a:

- ruoli
- route frontend
- capability backend
- moduli applicativi

Questo DL serve a stabilizzare il lessico e il contratto applicativo prima di introdurre:

- `TASK-V2-004` browser auth e routing iniziale
- il primo modulo `admin access management`
- future superfici di dominio come produzione, logistica e magazzino

## Decision

La V2 definisce una `surface` come una superficie applicativa di accesso,
cioe un'area funzionale coerente del prodotto che il sistema puo esporre a un utente autenticato come punto di ingresso operativo.

Una `surface` e un concetto applicativo, non un concetto infrastrutturale.

### 1. Definizione formale

Una `surface`:

- rappresenta un'area funzionale riconoscibile del sistema
- puo essere mostrata nel chooser iniziale o nel menu applicativo
- puo essere usata come destinazione di routing iniziale
- puo contenere piu pagine, viste e workflow interni

Esempi iniziali plausibili:

- `admin`
- `produzione`
- `logistica`
- `magazzino`

### 2. Una surface non e un ruolo

Il ruolo resta un concetto di autorizzazione.

La `surface` resta un concetto di esposizione applicativa.

Quindi:

- un ruolo puo abilitare una o piu surfaces
- una surface puo dipendere da uno o piu ruoli

Nel primo slice V2 e ammessa una relazione semplice quasi uno-a-uno, ma questa non va trattata come identita semantica.

Regola:

- `role != surface`

### 3. Una surface non e una route o una pagina

Una `surface` non coincide con:

- una route frontend specifica
- una singola pagina
- un componente UI

Una `surface` puo contenere:

- dashboard iniziale
- lista
- dettaglio
- form
- workflow secondari

Regola:

- `surface != route`
- `surface != page`

### 4. Una surface non e un permesso fine-grained

Una `surface` non sostituisce:

- guard backend puntuali
- permessi su singola azione
- capability tecniche di basso livello

Le surfaces servono per:

- ingresso applicativo
- navigazione primaria
- organizzazione coerente delle aree del prodotto

Non servono da sole a garantire autorizzazione completa su ogni operazione interna.

### 5. available_surfaces e output applicativo del backend

Il backend, a partire da identita, ruoli e policy applicative, espone un output di sessione che puo includere:

- `user`
- `roles`
- `access_mode`
- `available_surfaces`

`available_surfaces` e quindi un output derivato e stabilizzato per il frontend.

Il frontend:

- non deduce da solo le surfaces leggendo direttamente i ruoli
- consuma il valore esposto dal backend
- usa questo valore per chooser, menu e redirect iniziale

### 6. Uso delle surfaces nel routing iniziale

Le surfaces sono il livello corretto per decidere il routing iniziale dopo il login.

Strategia V2:

- se esiste una sola surface primaria disponibile, redirect automatico
- se esistono piu surfaces primarie, pagina di scelta
- le route interne della surface sono un dettaglio implementativo successivo

Questo evita mapping fragili del tipo:

- `role -> page`

### 7. Ownership del concetto

La definizione delle surfaces appartiene al contratto applicativo tra backend e frontend.

In pratica:

- il backend e fonte di verita per quali surfaces sono disponibili in sessione
- il frontend e responsabile della resa UX di chooser, menu e navigazione

Il modello auth non deve hardcodare il frontend,
ma il frontend non deve nemmeno reinventare la semantica delle superfici.

### 8. Surface iniziale admin

La prima `surface` implementata intenzionalmente dalla V2 dopo auth e:

- `admin`

`admin` rappresenta la superficie applicativa da cui governare:

- utenti
- ruoli assegnati
- stato attivo/inattivo degli utenti

Questo non implica che il ruolo `admin` e la surface `admin` siano la stessa cosa,
ma nel primo slice operativo V2 il ruolo `admin` abilita la surface `admin`.

### 9. Stabilita documentale

Da questo DL in poi il termine `surface` deve essere usato nei documenti V2 solo con questo significato:

> area funzionale applicativa esposta all'utente come punto di ingresso operativo

Se un documento parla di:

- ruolo
- route
- pagina
- permesso

deve usare quei termini in modo distinto e non intercambiabile con `surface`.

## Consequences

### Positive

- il lessico V2 diventa piu stabile
- backend e frontend condividono un contratto piu pulito
- il routing iniziale post-login resta spiegabile
- il modulo admin puo nascere senza confondere ruolo, area applicativa e pagina

### Negative / Trade-off

- introduce un livello concettuale in piu tra ruolo e route
- richiede disciplina documentale e implementativa
- alcune policy di mapping ruolo -> surface resteranno da dettagliare nei task o DL successivi

### Impatto sul progetto

Questo DL non introduce nuove tabelle e non modifica il modello dati.

Rafforza pero il contratto applicativo che guidera:

- `TASK-V2-004`
- il futuro DL su `admin access management`
- i task successivi relativi a menu, chooser e moduli di dominio

## Notes

- Nel primo slice V2 il mapping tra ruoli e surfaces puo restare semplice, ma non va considerato definitivo.
- Le surfaces sono un concetto lato prodotto/applicazione, non un sostituto del modello autorizzativo.
- Il prossimo DL naturale dopo questo e quello su `admin access management`.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
