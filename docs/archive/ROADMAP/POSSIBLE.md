# POSSIBLE — Ragionamenti aperti, non ancora confermati

Questo documento raccoglie ipotesi architetturali e possibili evoluzioni discusse
ma non ancora validate come decisioni operative. Nessuno di questi elementi è da
implementare prima del completamento di logistica e magazzino.

---

## P1 — Planning/Release layer separato

**Concetto:**
Separare il calcolo dei fabbisogni (planning, rigenerabile) dal rilascio operativo
(release, con effetti su EasyJob).

Entità candidate:
- `planning_candidates`: output del calcolo fabbisogni, completamente rigenerabile
- `release_decisions`: subset del planning trasformato in commitment operativo

**Perché non ora:**
I requisiti del planning dipendono dalla visibilità completa di tutti i flussi
(logistica, magazzino). Implementarlo adesso significherebbe progettare su basi
instabili. Le `commesse` attuali restano il release layer fino a quando i requisiti
sono stabili.

**Quando rivalutare:** dopo il completamento di logistica (FUTURE.md F4) e magazzino (FUTURE.md F5).

---

## P2 — PlanningRun + ReleaseProposal + PendingOverride (mini-spec)

**Contesto:** proposta discussa in sessione 2026-04-02.

**Modello:**
```
PlanningRun          → snapshot rigenerabile dei fabbisogni
ReleaseProposal      → subset del planning approvato per il lancio
PendingOverride      → modifiche utente con stato (still_valid / needs_review / invalidated)
```

**Meccanismo rebase:**
Quando un nuovo PlanningRun viene generato, ogni PendingOverride viene classificato:
- `still_valid`: facts cambiati ma override ancora coerente
- `needs_review`: divergenza >10% rispetto al valore calcolato
- `invalidated`: l'articolo non è più in fabbisogno

**Problema aperto:** la logica di equivalenza per il rebase (come fare match
tra override e nuovo planning su articoli aggregati vs per-riga) è complessa
e non ancora risolta.

**Relazione con FUTURE.md F3:** `pending_overrides` (F3) è una versione semplificata
di questo modello, senza PlanningRun persistito. Quando verrà implementato P1,
i pending_overrides migreranno in release_decisions.

---

## P3 — Make-or-Buy layer

**Concetto:**
Ogni articolo trattato come Supply Node con più opzioni di copertura:
- `make`: produzione interna
- `buy`: acquisto esterno
- `make_or_buy`: scelta dinamica

Decisione guidata da policy (costo minimo, lead time minimo, saturazione macchine, urgenza).

**Stato attuale:** il sistema gestisce solo produzione interna.

**Prerequisiti:** P1 (planning layer) deve esistere prima. Make-or-buy è una policy
applicata ai planning_candidates, non ha senso senza quel layer.

---

## P4 — Routing e fasi di lavorazione

**Concetto:**
Ogni articolo producibile ha un routing composto da fasi (interne, esterne, per pezzo, per lotto).
Lead time calcolato come somma delle fasi + buffer.

**Stato attuale:** il sistema usa solo `data_consegna`, capienza e priorità.
Non esiste modello di routing o lead time composito.

**Prerequisiti:** P1 e P3. Il routing serve al planning per calcolare date realistiche.

---

## P5 — Scheduler avanzato

**Concetto:**
Lo scheduler non solo esegue sync periodico ma triggera ricalcolo del planning
a ogni variazione significativa dei facts (nuovo ordine, chiusura produzione, ecc.).

**Prerequisiti:** P1 (planning layer rigenerabile) deve esistere.
L'attuale scheduler è sufficiente per le esigenze di V1.

---

## Note generali

- P1 è il prerequisito comune di P2, P3, P4, P5
- Nessuno di questi elementi deve bloccare il completamento di logistica e magazzino
- La priorità è: sistema operativo funzionante end-to-end > architettura avanzata
