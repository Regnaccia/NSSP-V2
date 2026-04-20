# Collaboration Rules For Rebase

## Scopo

Questo documento fissa le regole operative di collaborazione durante il `rebase` della V2.

Non definisce il dominio del prodotto.

Definisce invece:

- come classificare una nuova idea
- come discutere una variazione
- come decidere se serve:
  - chiarimento locale
  - task
  - test
  - decisione architetturale

## Principio base

Il progetto sta evolvendo su un dominio reale e ancora in emersione.

Quindi:

- implementare
- osservare casi reali
- riflettere
- rivedere

e un comportamento normale.

Il problema non e evitare la scoperta.  
Il problema e lasciare troppo a lungo aperte semantiche ambigue o compatibilita non necessarie.

## Regole operative

### 1. Ogni idea va classificata subito

Quando emerge una nuova idea o una variazione, va ricondotta subito a uno di questi livelli:

- `need detection`
- `release feasibility`
- `priority`
- `proposal policy`
- `UI / readability`
- `warning / diagnostics`
- `ownership / configuration`

Regola:

- non si discute una modifica senza prima dire a quale livello appartiene

### 2. Ogni caso reale va trasformato in regola generale

Quando emerge un caso reale:

- prima si capisce cosa succede nel caso
- poi si esplicita quale principio generale viene messo in crisi

Regola:

- non fermarsi al fix locale
- estrarre sempre la regola generale che il caso sta rivelando

### 3. Distinzione obbligatoria tra bisogno, rilascio e priorita

Ogni ragionamento planning deve distinguere esplicitamente:

- `cosa serve`
- `cosa posso lanciare ora`
- `cosa conviene trattare prima`

Traduzione operativa:

- `need detection`
- `release feasibility`
- `priority`

Regola:

- se una modifica tocca uno di questi tre livelli, va dichiarato esplicitamente quale

### 4. Lo score non corregge il dominio

`priority_score` e un layer di ordinamento/priorita.

Non deve diventare il posto dove nascondere:

- regole di bisogno
- regole di rilascio
- correzioni di semantica ambigua

Regola:

- se una regola cambia il significato del candidate, non va nello score
- se una regola ordina o pesa candidate gia validi, puo andare nello score

### 5. Compatibilita transitorie solo se davvero necessarie

Una compatibilita temporanea si giustifica solo se evita un rischio reale di migrazione.

Non si mantiene una doppia semantica solo per rinviare una decisione.

Regola:

- se la direzione corretta e chiara, si preferisce tagliare netto
- se la direzione non e ancora chiara, si dichiara esplicitamente che si sta ancora esplorando

### 6. Quando la scelta e chiara, va congelata

Quando dal confronto emerge una direzione netta:

- la scelta va congelata
- il backlog va riallineato
- le alternative scartate non devono restare implicitamente aperte

Regola:

- non lasciare attive due letture concorrenti dello stesso comportamento

### 7. I casi reali diventano `golden cases`

I casi reali piu significativi devono diventare:

- test
- esempi di spec
- riferimenti del rebase

Regola:

- se un caso reale cambia la comprensione del dominio, non deve restare solo nella conversazione

### 8. La risposta a una nuova idea deve seguire una struttura stabile

Quando arriva una nuova idea o variazione, la risposta deve chiarire almeno:

1. che tipo di modifica e
2. quale impatto ha sul modello
3. quale rischio o ambiguita introduce
4. quale direzione e consigliata
5. quale output serve:
   - nessuno
   - task
   - test
   - DL

## Regole decisionali pratiche

### Quando basta un chiarimento locale

Usare solo chiarimento locale se:

- non cambia il modello
- non cambia il contratto
- non cambia il significato dei dati

### Quando serve un task

Aprire un task se:

- la direzione e chiara
- il lavoro e implementativo
- non serve ridefinire un principio generale

### Quando serve un test dedicato

Aprire un test dedicato se:

- un caso reale rivela un rischio di regressione
- la regola e gia chiara
- va solo resa verificabile e stabile

### Quando serve un DL

Serve una decisione architetturale se:

- cambia la semantica del dominio
- cambia ownership
- cambia il confine tra moduli
- cambia il ruolo di una surface
- elimina o introduce una compatibilita importante

## Regola specifica per il rebase attuale

Nel rebase V2 la linea guida da preservare e:

- `Planning Candidates` deve restare semanticamente semplice
- `Unified Planning Workspace` deve rendere leggibile il contesto
- `priority_score` deve crescere come layer evolutivo
- `Production Proposals` deve restare downstream e non ridefinire il bisogno

## Obiettivo di collaborazione

L'obiettivo non e prendere decisioni perfette al primo colpo.

L'obiettivo e:

- scoprire velocemente
- chiarire presto
- congelare appena la direzione e sufficientemente solida
- evitare di trascinare ambiguita oltre il necessario
