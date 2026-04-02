# DL-OPS-001 — Production Planning & Make-or-Buy Model

> Documento archiviato. Non e parte della convenzione attiva V2.
> I concetti operativi verranno riallineati progressivamente in charter, roadmap, task e futuri documenti V2.

## Status
Proposed

## Context

Il sistema MRS deve evolvere da una logica operativa basata su decisioni manuali e batch (es. pianificazione mensile) a un modello:

- fact-driven
- policy-driven
- rigenerabile
- estendibile

Sono emersi due bisogni fondamentali:

1. Separare **planning** da **release operativo**
2. Gestire in modo unificato:
   - produzione interna
   - acquisti
   - semilavorati
   - prodotti finiti
   - lavorazioni esterne

---

## Decision

Il sistema introduce:

### 1. Production Planning Layer (automatico)
### 2. Release Layer (controllato)
### 3. Unified Supply Model (Make / Buy / Make-or-Buy)

---

# 1. Production Planning Model

## 1.1 Definizione

Il planning è un processo automatico che:

- legge i source facts (ordini, stock, WIP, ecc.)
- calcola fabbisogni
- genera candidati di produzione/acquisto
- NON genera commitment operativo

---

## 1.2 Output del planning

Il planning genera:

### PlanningCandidate

Campi principali:

- item_id
- qty_required
- need_date (o finestra temporale)
- source_of_demand (ordine, scorta, ecc.)
- priority
- confidence
- planning_version

---

## 1.3 Proprietà fondamentali

- completamente rigenerabile
- nessun effetto operativo diretto
- aggiornato a ogni variazione dei facts

---

# 2. Release Model

## 2.1 Definizione

Il release è il processo che decide:

> cosa trasformare in commitment operativo (Easy o acquisto)

---

## 2.2 Output del release

### ReleaseDecision

Campi:

- item_id
- qty
- mode (make / buy)
- target_system (Easy / fornitore)
- planned_start_date
- reason
- policy_used

---

## 2.3 Regole

- il release avviene solo su subset del planning
- è governato da policy
- può essere:
  - manuale
  - semi-automatico
  - automatico (futuro)

---

# 3. Unified Supply Model

## 3.1 Principio

Ogni item è trattato come:

> **Supply Node**

Non esiste distinzione rigida tra:
- materia prima
- semilavorato
- prodotto finito

---

## 3.2 Coverage Modes

Ogni item può avere:

- buy
- make
- make_or_buy

---

## 3.3 CoverageOption

Ogni item può avere più opzioni:

- type: make | buy
- lead_time_estimate
- cost_estimate
- constraints
- enabled

---

## 3.4 CoverageDecision

Il sistema sceglie:

- make
- buy
- split

in base a policy e contesto.

---

# 4. Multi-Level Supply (Semilavorati)

## 4.1 Principio

Il sistema supporta domanda dipendente.

Esempio:

B = SEMI1 + lavorazione finale

---

## 4.2 Regole

Per un ordine su B:

1. verifica stock SEMI1
2. se insufficiente:
   - genera fabbisogno su SEMI1
3. calcola lead time totale

---

## 4.3 Lead Time


lead_time(B) =
lead_time(SEMI1)
+
lead_time_fase_finale


---

## 4.4 SEMI1 come Supply Node

SEMI1 è:

- stock managed
- producibile
- con proprio lead time

---

# 5. Routing & Phases Model

## 5.1 Definizione

Ogni item producibile ha un routing composto da fasi.

---

## 5.2 Tipi di fase

- per pezzo
- per lotto
- misto
- esterno

---

## 5.3 Fase esterna

È modellata come:

- tipo: external
- lead_time
- variabilità
- fornitore

---

## 5.4 Lead Time totale


lead_time =
somma fasi interne
+
fasi esterne
+
buffer


---

# 6. Make-or-Buy Decision

## 6.1 Principio

La scelta non è statica ma dinamica.

---

## 6.2 Input

- domanda
- stock
- capacità
- lead time
- costo
- priorità

---

## 6.3 Policy esempi

- costo minimo
- lead time minimo
- saturazione macchine
- urgenza cliente
- strategia mista

---

## 6.4 Output

- make
- buy
- split

---

# 7. Planning vs Release Boundary

## 7.1 Zone temporali

- long term → planning libero
- mid term → planning controllato
- short term → release candidate
- immediate → release

---

## 7.2 Regola

Planning ≠ commitment

---

# 8. Transition Strategy (V1 → V1.1)

## 8.1 Fase iniziale

- implementare legacy come policy:
  - legacy_release_policy

---

## 8.2 Fase intermedia

- introdurre:
  - lead time stimati
  - routing base
  - make_or_buy

---

## 8.3 Fase avanzata

- planning automatico completo
- release semi-automatico
- decisioni explainable

---

# 9. Key Principles

1. Planning è sempre automatico e rigenerabile  
2. Release è controllato  
3. Tutti gli item sono supply node  
4. Make-or-buy è dinamico  
5. Multi-level supply è nativo  
6. Lead time è composto, non fisso  
7. Policy governa le decisioni  
8. Il sistema è explainable  

---

## Notes

Questo documento definisce il modello operativo base per:

- produzione
- approvvigionamento
- gestione semilavorati
- pianificazione avanzata

Costituisce base per implementazione V1.1.

---

# 10. Criticità emerse in V1 e soluzioni pragmatiche

## 10.1 Contesto

Durante lo sviluppo e il test operativo di V1 sono emerse criticità che impattano
la fattibilità del modello planning/release completo come descritto nei capitoli
precedenti. Questa sezione documenta i problemi riscontrati, le soluzioni proposte
e il piano di transizione pragmatico verso V1.1.

---

## 10.2 Criticità riscontrate

### C1 — Sync timing e disallineamento dati

**Problema:**
Il sync periodico (ogni N minuti) introduce finestre di staleness significative.
L'utente che apre F1a può vedere dati aggiornati 15+ minuti fa. Nel frattempo
EasyJob ha ricevuto nuovi ordini o chiuso produzioni. Le decisioni vengono prese
su dati non aggiornati.

**Impatto:** alto — decisioni operative su dati errati.

**Soluzione proposta: sync on-demand non bloccante**

- Ogni endpoint operativo (F1a, F1b) lancia sync delle dipendenze in background
- Risponde immediatamente con i dati correnti
- Il frontend mostra indicatore "aggiornamento in corso"
- Dopo 3-5s il frontend fa un secondo fetch automatico
- Il sync periodico resta come fallback

Costo stimato: ~20 righe backend, ~5 frontend. Non tocca il modello dati.

---

### C2 — Override persi al refresh

**Problema:**
Gli override utente (qty, sorgente, tipo produzione) sono mantenuti in React state.
Un refresh, una navigazione, o una sessione scaduta cancella tutto il lavoro non
ancora lanciato. In contesti operativi reali questo causa rilavorazione e frustrazione.

**Impatto:** medio — UX degradata, rischio di errori per riesecuzione incompleta.

**Soluzione proposta: tabella `pending_overrides`**

```sql
CREATE TABLE pending_overrides (
  id              uuid PRIMARY KEY,
  articolo_id     uuid NOT NULL,
  riga_ordine_id  uuid,           -- NULL per F1b (scorta)
  qty             integer,
  sorgente_json   jsonb,          -- campi SorgenteOverride serializzati
  created_by      varchar(50),
  created_at      timestamptz,
  expires_at      timestamptz     -- pulizia automatica fine giornata
);
```

- Override confermati nel modal → PATCH `/api/pending-overrides`
- Genera commesse legge prima da `pending_overrides`, poi fallback ai valori calcolati
- Pulizia automatica al lancio o a fine giornata
- `needs_review = true` quando il sync aggiorna i facts e la qty diverge >10% dall'override

Costo stimato: 1 tabella, 2 endpoint, cambio frontend nel LancioModal.

---

### C3 — Logica famiglia/aggregazione sparsa nel codice

**Problema:**
La distinzione tra articoli aggregati (standard) e articoli per-riga-ordine (speciali,
barre, BCL) è implementata tramite CASE SQL in `get_righe_da_processare` e dispatch
nel router. Aggiungere un nuovo tipo di articolo richiede modifiche in punti multipli
del codice, con rischio di regressioni.

**Impatto:** medio — manutenibilità bassa, configurabilità assente.

**Soluzione proposta: `famiglia` e `release_mode` su `articoli`**

```sql
ALTER TABLE articoli ADD COLUMN famiglia     varchar(20) DEFAULT NULL;
-- 'standard' | 'speciali' | 'barre' | 'bcl'
-- configurabile in UI parametri articoli

ALTER TABLE articoli ADD COLUMN release_mode varchar(20) DEFAULT 'aggregate';
-- 'aggregate': una riga per articolo (standard, scorte)
-- 'per_row':   una riga per riga ordine (speciali, BCL, barre)
```

- Migrazione popola i default da `categorie_articolo.famiglia` e dalla regola codice `S*`
- Tutta la logica di dispatch diventa un check su `release_mode`
- `categorie_articolo.famiglia` resta per compatibilità ma cessa di guidare la logica

Costo stimato: 1 migrazione, refactor ~50 righe backend, UI parametri articoli.

---

### C4 — Planning/release non separati (gap rispetto a DL-OPS-001)

**Problema:**
V1 non implementa il planning layer separato dal release layer come descritto
nei capitoli 1-7. Le commesse vengono generate direttamente dai calcoli live,
senza una fase di planning rigenerabile intermedia.

**Impatto:** accettabile per V1, bloccante per V1.1 (scheduler, make-or-buy).

**Decisione:**
Non implementare planning/release completo prima di completare logistica e
magazzino. I requisiti del planning dipendono dalla visibilità completa di tutti
i flussi — che oggi non è disponibile.

Il layer planning/release (due tabelle, policy engine) viene rimandato a dopo
il completamento di logistica e magazzino, quando i requisiti sono stabili.

---

## 10.3 Piano di transizione pragmatico V1 → V1.1

```
Step 1 — famiglia + release_mode su articoli
  Prerequisito per tutto il resto. Elimina codice fragile.
  Non tocca logistica, magazzino, scheduler.

Step 2 — Sync on-demand non bloccante
  Fix al problema operativo più urgente.
  Trasparente all'utente, non cambia nessun modello dati.

Step 3 — pending_overrides
  Fix UX persistenza override.
  Dipende da Step 1 (usa articolo_id + release_mode).

Step 4 — Completare logistica
  Indipendente dagli step 1-3.

Step 5 — Completare magazzino
  Indipendente dagli step 1-3.

Step 6 — Planning/release layer
  Solo dopo Step 4+5. Requisiti stabili.
  Implementa planning_candidates + release_decisions.
  Wrap della logica attuale come legacy_release_policy.

Step 7 — Scheduler avanzato
  Usa planning layer. Triggera ricalcolo su variazione facts.
  Make-or-buy policy. Lead time compositi.
```

---

## 10.4 Cosa NON cambia rispetto a DL-OPS-001

- Il modello concettuale (planning separato da release) rimane valido
- I principi chiave (§9) rimangono l'obiettivo
- La transition strategy (§8) rimane la direzione — viene solo resa più graduale
- `pending_overrides` è compatibile con il futuro `release_decisions`:
  quando verrà implementato, i pending_overrides migreranno in release_decisions
