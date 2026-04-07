# DL-ARCH-V2-003 - Modello di accesso utente, ruoli e canali client

## Status
Approved

## Date
2026-04-07

## Context

La V2 deve introdurre presto un primo flusso di autenticazione per mantenere lo sviluppo:

- incrementale
- testabile
- coerente con i confini architetturali gia fissati

Il bisogno immediato e un login utente su frontend browser che:

- autentica l'utente
- identifica il suo insieme di ruoli
- lo reindirizza alle funzioni coerenti con i suoi permessi

Ma il browser non e il punto finale del sistema. A breve il progetto dovra supportare anche:

- client browser
- client Electron
- terminali kiosk

Se il modello nasce centrato solo sul browser o solo sul ruolo singolo, rischia di diventare fragile
appena entrano in gioco:

- utenti con piu ruoli
- accessi da client diversi
- terminali shared o kiosk
- policy diverse tra accesso nominale e accesso di contesto

La V2 ha quindi bisogno di un modello esplicito che distingua:

- identita utente
- ruoli e permessi
- canale di accesso / tipo client
- routing iniziale applicativo

## Decision

La V2 adotta un modello di accesso composto da tre assi distinti:

1. identita utente
2. ruoli utente
3. canale di accesso client

Questi assi non vanno fusi in un solo concetto.

### 1. Identita utente

L'identita utente e nominale.

Ogni utente ha almeno:

- `id`
- `username`
- `password_hash`
- `attivo`

L'identita serve a:

- autenticare la persona
- tracciare chi ha aperto la sessione
- supportare audit leggero e ownership applicativa futura

### 2. Ruoli come insieme, non come campo singolo

Un utente puo avere uno o piu ruoli contemporaneamente.

Il modello V2 assume quindi che il concetto corretto sia:

- `user.roles[]`

non:

- `user.role`

Ruoli iniziali previsti:

- `admin`
- `produzione`
- `logistica`
- `magazzino`

Conseguenza:

- l'autorizzazione backend deve ragionare per membership del ruolo richiesto
- il frontend non deve assumere un solo ruolo attivo per utente
- il routing iniziale puo dipendere da una priorita applicativa o da una scelta utente, non da un solo campo hardcoded

### 3. Canale di accesso separato dai ruoli

La modalita con cui l'utente accede al sistema e un concetto separato dai ruoli.

Canali iniziali:

- `browser`
- `electron`
- `kiosk`

Il canale di accesso descrive:

- il tipo di client
- il contesto di esecuzione
- i vincoli UX e di sicurezza

Non descrive da solo cosa l'utente puo fare.

### 4. Browser-first, ma non browser-centric

La prima implementazione V2 copre solo il canale:

- `browser`

Ma il contratto architetturale deve gia essere estendibile a:

- `electron`
- `kiosk`

Regola:

- il backend non deve hardcodare comportamento specifico del browser come se fosse l'unico client possibile
- il frontend browser puo essere il primo client implementato, ma non definisce da solo il modello di accesso

### 5. Kiosk come accesso di contesto, non login nominale standard

Il canale `kiosk` e concettualmente diverso da browser ed Electron.

Nel kiosk, il sistema deve poter rappresentare:

- accesso legato a postazione o terminale
- contesto operativo fisico
- esperienza senza login nominale continuo

Per ora il kiosk non viene implementato, ma il modello deve gia lasciargli spazio.

Quindi:

- il login nominale browser non deve diventare prerequisito architetturale universale
- il concetto di `client context` o `access context` deve restare modellabile

### 6. Sessione di accesso e payload minimo

Dopo login riuscito, il sistema deve poter esporre almeno:

- identita utente
- ruoli utente
- canale di accesso
- capability o viste iniziali consentite

Il payload applicativo di sessione deve quindi essere pensato come:

- `user`
- `roles`
- `access_mode`
- `available_surfaces` o equivalente

Il backend resta fonte di verita per autorizzazione e claims di sessione.

### 7. Routing iniziale guidato da capability, non da pagina fissa

Dopo il login, il frontend non deve fare redirect sulla base di una singola pagina hardcoded per ruolo.

Deve invece ragionare su:

- ruoli posseduti
- superfici disponibili
- eventuale priorita di default

Strategia iniziale consigliata:

- se l'utente ha una sola superficie primaria, redirect automatico
- se l'utente ha piu superfici primarie, landing di scelta

Questo evita di introdurre presto assunzioni fragili per utenti multi-ruolo.

### 8. Confine tra backend e frontend

Backend:

- autentica
- emette la sessione o token
- espone ruoli e capability consentite
- applica le guard di autorizzazione

Frontend:

- consuma il profilo di sessione
- mostra solo le superfici consentite
- applica il routing iniziale

Il frontend non decide i permessi.

### 9. Implementazione incrementale richiesta da questo DL

Il primo task guidato da questo DL deve introdurre solo il minimo necessario per il canale `browser`:

- login nominale
- sessione utente
- ruoli multipli nel contratto
- routing iniziale coerente

Non deve ancora introdurre:

- kiosk reale
- client Electron reale
- policy di terminal binding complete

## Consequences

### Positive

- il browser puo partire subito senza bloccare il modello futuro
- utenti multi-ruolo non diventano un edge case tardivo
- auth e access mode restano concetti puliti e separati
- kiosk ed Electron avranno spazio architetturale senza refactor prematuro

### Negative / Trade-off

- il primo modello auth e leggermente piu astratto di un semplice `role -> page`
- il frontend iniziale richiede un minimo di logica in piu per il routing
- alcune scelte concrete su kiosk restano rinviate a DL successivi

### Impatto sul progetto

Questo DL non introduce ancora workflow di dominio.

Introduce pero il primo contratto di accesso applicativo che dovra essere rispettato da:

- backend auth
- guard applicative
- frontend browser
- futuri client Electron e kiosk

## Notes

- Questo DL recupera la lezione valida del modello ibrido V1, ma evita di inglobare troppo presto i dettagli di implementazione legacy.
- Il prossimo task naturale e l'implementazione del primo slice `browser auth` coerente con questo modello.
- Un DL successivo potra dettagliare il modello kiosk quando il canale diventera attivo.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
