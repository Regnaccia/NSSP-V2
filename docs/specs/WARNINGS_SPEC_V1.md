# WARNINGS_SPEC_V1

## 1. Contesto

Il sistema V2 sta iniziando a separare in modo esplicito:

- bisogno produttivo reale
- anomalie dati o di processo

Questa separazione e gia emersa in `Planning Candidates`:

- lo stock negativo non deve generare automaticamente un candidate
- resta pero un'anomalia importante che il sistema deve rendere visibile

In futuro esisteranno anche altri warning che potranno interessare:

- piu reparti
- un singolo reparto
- una singola surface

Serve quindi un modulo warning unico e trasversale.

## 2. Obiettivo del modulo

Il modulo `Warnings` ha lo scopo di:

- rappresentare anomalie operative o dati anomali in modo canonico
- evitare che le anomalie vengano duplicate in piu moduli
- permettere visibilita differenziata per area/reparto, ruolo o dominio
- mantenere separata la logica di warning dalle logiche decisionali dei moduli operativi

## 3. Principio architetturale

`Warnings` e un modulo trasversale unico.

Non esistono warning duplicati per reparto.

Esiste invece:

- un warning canonico
- con metadati di audience / visibilita
- proiettato nelle surface opportune

Regola:

- un warning puo essere rilevante per piu reparti
- ma resta un solo oggetto warning

## 4. Scope V1

### Il modulo FA

- introduce un oggetto warning persistente o comunque canonico
- supporta il primo tipo di warning:
  - `NEGATIVE_STOCK`
- separa il warning dalla logica di `Planning Candidates`
- consente di dichiarare chi puo vedere il warning

### Il modulo NON FA ancora

- non introduce ancora workflow avanzato completo
- non introduce ancora note operatore obbligatorie
- non introduce ancora una tassonomia completa di tutti i warning futuri
- non sostituisce i moduli operativi che consumano i warning

## 5. Oggetto centrale

### Warning

`Warning` e l'oggetto canonico del modulo.

Rappresenta:

- un'anomalia o condizione da segnalare
- separata dai moduli che la consumano

## 6. Tipologia iniziale V1

Primo warning in scope:

- `NEGATIVE_STOCK`

Definizione:

- articolo con `stock_calculated < 0`

Nota:

- questo warning non genera automaticamente una produzione
- non e un need produttivo
- puo pero essere rilevante per magazzino, produzione e altri ruoli futuri

## 7. Visibilita e audience

Il modulo non modella i warning per reparto come entita separate.

Usa invece metadati di visibilita.

Dimensioni target:

- `visible_to_areas`
- `visible_to_roles`
- `domain_tags`

Dove `visible_to_areas` rappresenta aree/reparti operativi, per esempio:

- `magazzino`
- `produzione`
- `logistica`

La modellazione per singola surface applicativa non e il target architetturale preferito.
Puo esistere come soluzione intermedia tecnica, ma la semantica corretta e per area/reparto.

Esempio:

- `NEGATIVE_STOCK`
  - visibile a:
    - `magazzino`
    - `produzione`

La surface `Warnings` deve essere accessibile di default come punto unico di consultazione trasversale.

Precisazione operativa:

- la surface `Warnings` e raggiungibile come modulo trasversale
- ma il contenuto mostrato all'utente deve essere filtrato in base all'area/reparto corrente
- quindi ogni reparto vede nella surface `Warnings` solo i warning di propria competenza
- la configurazione `visible_to_areas` governa sia i consumi nelle surface operative sia la lista della surface `Warnings`

### Configurazione

La configurazione di visibilita dei warning e un dato interno V2.

Deve essere accessibile e governabile dalla surface:

- `admin`

Questo vale in particolare per:

- audience per area/reparto
- audience per ruolo
- eventuali domain tag o classificazioni future

## 8. Dati warning

Shape minima suggerita:

- `warning_id`
- `type`
- `severity`
- `entity_type`
- `entity_key`
- `message`
- `source_module`
- `visible_to_areas`
- `created_at`

Campi specifici per `NEGATIVE_STOCK`:

- `article_code`
- `stock_calculated`
- `anomaly_qty`

## 9. Regole di ownership

Il warning appartiene al modulo `Warnings`, non al modulo che lo visualizza.

Questo implica:

- `Planning Candidates` puo leggere o mostrare un warning
- `articoli` puo leggere o mostrare un warning
- ma la generazione e persistenza del warning restano centralizzate

## 10. Integrazione con moduli esistenti

### Planning Candidates

- non deve trattare `negative_stock` come need produttivo
- puo in futuro mostrare badge warning
- non deve possedere la logica warning

### Articoli

- puo essere una surface naturale per visualizzare warning relativi all'articolo

### Admin

- deve essere la surface deputata a governare la configurazione di visibilita dei warning
- non necessariamente la UI finale del modulo `Warnings`, ma il punto di controllo amministrativo delle audience

### Produzione / Magazzino

- possono consumare gli stessi warning se pertinenti
- ciascun reparto vede solo i warning che lo includono in `visible_to_areas`

## 11. Workflow warning

V1 puo restare molto leggero.

Stati futuri possibili:

- `open`
- `acknowledged`
- `resolved`

Ma non sono obbligatori per il primo slice.

## 12. Principio guida finale

> `Warnings` e un modulo trasversale canonico: un warning esiste una sola volta, puo essere visibile a piu aree o ruoli, e resta separato dai moduli che lo consumano.
