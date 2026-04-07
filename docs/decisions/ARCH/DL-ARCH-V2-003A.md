# DL-ARCH-V2-003A - Identity & Auth Data Model

## Status
Approved

## Date
2026-04-07

## Context

`DL-ARCH-V2-003` ha fissato il ruolo del DB interno come persistence backbone della V2.

`DL-ARCH-V2-004` ha fissato il modello di accesso basato su:

- identita utente
- ruoli multipli
- canale di accesso

Durante l'implementazione dei primi slice V2 e stato introdotto un modello dati minimo per supportare:

- autenticazione nominale browser
- ruoli multipli per utente
- base dati per autorizzazione backend
- surface `admin` di access management

Questo DL non introduce un target alternativo.

Serve invece a rendere esplicito e stabile il modello dati identity/auth gia adottato nel codice e nelle migrazioni iniziali.

## Decision

La V2 adotta un modello dati interno minimale per identity e ruoli basato su tre entita principali:

1. `users`
2. `roles`
3. `user_roles`

Questo modello e il riferimento documentale per il primo slice auth della V2.

### 1. Entita `users`

Rappresenta l'identita nominale dell'utente.

Campi minimi adottati nel primo slice:

- `id` (PK)
- `username` (unique)
- `password_hash`
- `attivo` (boolean)
- `created_at`

Regole:

- `username` deve essere unico
- la password non viene mai salvata in chiaro
- `attivo = false` blocca l'accesso senza eliminare l'utente

Nota:

- `updated_at` non fa parte del modello iniziale implementato
- se servira in futuro, verra introdotto da un DL e da una migration dedicata

### 2. Entita `roles`

Rappresenta i ruoli applicativi disponibili nel primo slice V2.

Campi minimi adottati:

- `id` (PK)
- `name` (unique)

Esempi iniziali:

- `admin`
- `produzione`
- `logistica`
- `magazzino`

Regole:

- `name` e l'identificatore logico usato da backend e frontend
- i ruoli sono definiti lato sistema, non creati dinamicamente dagli utenti nella V2 iniziale

Nota:

- campi come `description` non fanno parte del primo slice implementato
- se serviranno metadata aggiuntivi, verranno introdotti esplicitamente in un'evoluzione successiva

### 3. Entita `user_roles`

Tabella di relazione molti-a-molti tra utenti e ruoli.

Campi:

- `user_id` (FK -> `users.id`)
- `role_id` (FK -> `roles.id`)

Vincoli:

- PK composta (`user_id`, `role_id`)
- un utente puo avere `1..N` ruoli
- un ruolo puo essere assegnato a `0..N` utenti

## Modello logico risultante

- `user.roles` e un insieme
- non esiste un "ruolo attivo" persistito nel DB
- la selezione di contesto, se necessaria, resta responsabilita del livello applicativo

## Relazione con access mode e sessione

Il modello dati identity/auth NON include:

- `access_mode`
- sessioni persistite
- refresh token storage
- device binding
- kiosk identity

`access_mode` resta un attributo della sessione o del contesto di accesso, non della persistenza utente.

## Relazione con il codice attuale

Questo DL documenta il modello effettivamente introdotto nei primi slice V2.

In particolare:

- il campo utente adottato e `attivo`, non `is_active`
- il ruolo usa `name`, non `code`
- il modello iniziale non include `updated_at`
- il modello iniziale non include `roles.description`

Queste scelte sono considerate valide per il primo slice e non richiedono un task di riallineamento dedicato.

## Esclusioni esplicite

Questo modello NON include ancora:

- permessi fine-grained
- policy matrix avanzate
- cataloghi ruoli editabili da UI
- modellazione sessioni avanzate
- registry di client o terminali

Questi aspetti potranno essere introdotti solo con nuovi DL espliciti.

## Consequences

### Positive

- abilita autenticazione reale su DB interno
- supporta nativamente utenti multi-ruolo
- mantiene semplice il primo slice V2
- resta coerente con auth browser e con la surface `admin`

### Negative / Trade-off

- il naming e volutamente minimale e poco esteso
- non esistono metadata avanzati sui ruoli
- eventuali evoluzioni future richiederanno migration dedicate

### Impatto sul progetto

Questo DL diventa riferimento esplicito per il modello dati gia usato da:

- `TASK-V2-003` bootstrap DB interno
- `TASK-V2-004` browser auth
- `TASK-V2-005` admin access management

## Notes

- Il modello e volutamente minimale: privilegia stabilita e chiarezza rispetto a completezza.
- Questo DL e una formalizzazione del modello implementato, non una richiesta retroattiva di refactor.

## References

- `docs/decisions/ARCH/DL-ARCH-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/task/TASK-V2-003-bootstrap-db-interno.md`
- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
