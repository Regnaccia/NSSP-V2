# ODE V2 - General Project Review

## Date
2026-04-15

## Follow-up

La review e stata materializzata come baseline operativa in:

- `docs/decisions/ARCH/DL-ARCH-V2-039.md`
- `docs/decisions/ARCH/DL-ARCH-V2-042.md`
- `docs/roadmap/REBASE_V2_BACKLOG_2026-04-15.md`

## Scope

Review generale architetturale e operativa dell'intero progetto V2 dopo il consolidamento di:

- `sync`
- `articoli`
- `produzioni`
- fact quantitativi canonici
- `Planning Candidates`
- `Warnings`
- primo stream `Production Proposals`

L'obiettivo non e riesaminare singoli task, ma verificare:

- quali scelte sono ormai solide
- dove il progetto sta iniziando a frammentarsi
- quali semplificazioni conviene fare prima di estendere ancora il dominio

## Executive Summary

La V2 e in una posizione buona ma delicata.

Le fondamenta architetturali sono corrette:

- `sync` separato da `core`
- Easy mantenuto `read-only`
- computed fact nel layer giusto
- configurazione interna modellata come default famiglia + override articolo
- `Planning Candidates` e `Warnings` gia portati a forma operativa reale

Il rischio principale oggi non e il bootstrap tecnico. E la dispersione del modello di dominio in micro-decisioni locali, soprattutto nell'area:

- proposal logic
- ownership dei dati configurativi
- confine tra warning, diagnostica locale e workflow operativo

In sintesi:

- il progetto non e in crisi
- ma e al punto giusto per un `rebase architetturale leggero`
- prima di aggiungere altre logiche proposal, export rules o eccezioni UI

## What Is Solid

### 1. Layering generale

Il modello a layer resta la scelta giusta:

- `sync` come mirror tecnico
- `core` come luogo di significato, fact e read model
- `app` come orchestrazione/API
- `shared` come libreria infrastrutturale

Questa separazione ha tenuto bene anche quando sono emerse correzioni non banali:

- chiave articolo canonica
- planning stock-driven
- warning cross-modulo
- proposal workspace temporaneo

### 2. Fact canonici quantitativi

La linea `inventory -> customer_set_aside -> commitments -> availability` e corretta.

Anche i limiti noti confermano che il modello e buono: i problemi aperti non riguardano l'idea dei fact, ma:

- robustezza del refresh
- strategia del mirror `MAG_REALE`
- coerenza runtime delle chain

Questo e un buon segnale.

### 3. Pattern configurativo famiglia -> articolo -> effective

Questo e probabilmente il pattern piu riuscito della V2.

Funziona gia bene per:

- planning policy
- stock policy
- `gestione_scorte_attiva`
- proposal logic

La scelta di non mettere tutto solo sull'articolo e di non spingere tutto in `admin` e corretta. Il modello e abbastanza ricco ma ancora leggibile.

### 4. Planning Candidates come centro operativo

`Planning Candidates` e il modulo piu maturo del progetto.

Punti forti:

- modalita esplicite `by_article` / `by_customer_order_line`
- separazione tra componente cliente e scorta
- `primary_driver`
- horizon separati
- descrizione/destinazione/date leggibili
- integrazione warnings senza duplicare il dominio warning

Questa parte e ormai abbastanza solida da essere usata come riferimento per il livello di maturita desiderato sugli altri moduli.

### 5. Warnings come modulo trasversale

Anche qui la direzione e giusta:

- warning canonico unico
- visibilita per area
- surface dedicata
- nessuna duplicazione nelle surface operative

La distinzione tra:

- warning canonico
- contesto warning letto da altri moduli

e una delle scelte migliori fatte finora.

## Findings

### 1. Proposal e il punto piu frammentato del sistema

`Production Proposals` e il modulo dove oggi si vede piu chiaramente la frammentazione del modello.

Segnali:

- passaggio da persistent inbox a workspace temporaneo
- export preview quasi 1:1 con EasyJob
- logiche proposal che crescono rapidamente
- requested vs effective logic
- fallback reason
- ownership del dato barra corretta solo dopo validazione operativa

Il problema non e che la direzione sia sbagliata. Il problema e che il modulo sta ancora scoprendo la propria forma mentre gia accumula logiche e policy.

Rischio:

- moltiplicazione di logiche monolitiche
- task sempre piu piccoli ma semanticamente collegati
- incremento del costo cognitivo per capire perche una proposal produce un certo risultato

### 2. Le proposal logic stanno diventando una DSL implicita

Oggi le logiche proposal non sono piu solo “strategie” isolate.

Stanno emergendo almeno quattro dimensioni distinte:

- base quantity selection
- forma lotto / barra / multiplo
- policy di capienza
- guardrail cliente

Esempio concreto:

- `proposal_target_pieces_v1`
- `proposal_full_bar_v1`
- `proposal_full_bar_v2_capacity_floor`

Questo suggerisce che stiamo già modellando combinazioni di assi decisionali, non semplici enum di strategie.

Rischio:

- nuova logica per ogni combinazione
- nomenclatura sempre piu lunga
- difficolta a capire cosa e veramente “nuovo” e cosa e solo una variante compositiva

### 3. Ownership dei dati ancora corretta a livello pattern, ma instabile nei dettagli

Il pattern generale e giusto:

- configurazione in famiglia
- override/assegnazione in articolo
- fact nel `core`

Pero nei dettagli emergono ancora ownership poco consolidate:

- `raw_bar_length_mm` inizialmente modellato sul finito, poi corretto sul materiale grezzo
- warning di configurazione inizialmente pensato sull'articolo proposal, poi corretto sul raw material
- `proposal_logic_key` su articolo ma con implicazioni che in parte appartengono al materiale

Questo non e un disastro, ma e un segnale che il perimetro:

- finito
- materiale grezzo
- famiglia
- configurazione tecnica di processo

va esplicitato meglio.

### 4. Confine tra warning canonico e diagnostica locale e buono, ma recente

La distinzione:

- warning canonico nel modulo `Warnings`
- fallback reason locale in `Production Proposals`

e corretta.

Pero e emersa tardi, dopo qualche oscillazione concettuale.

Rischio:

- se non viene congelata come principio generale, potrebbe riaprirsi in altri punti del progetto

Linea corretta da preservare:

- i warning segnalano anomalie trasversali del sistema
- la diagnostica locale spiega il comportamento di una logica dentro un modulo

### 5. Documentazione/tasking molto ricco, ma vicino alla saturazione

La catena:

- spec
- DL
- task
- handoff
- roadmap

ha funzionato molto bene.

Pero ora si vede un rischio di saturazione documentale:

- tanti task piccoli
- numerosi DL ravvicinati sullo stesso stream
- overview e status da riallineare spesso

Rischio:

- la docs continua a essere corretta, ma diventa piu difficile capire quali decisioni sono strutturali e quali sono solo aggiustamenti locali

### 6. Restano aperti tre debiti strutturali cross-modulo

Questi non sono nuovi, ma continuano a contare:

- `sync_mag_reale` con strategia non ancora strutturalmente definitiva
- refresh/freshness ancora non perfettamente fail-fast
- `core_articolo_config` con rischio di record orfani

Questi non bloccano il lavoro quotidiano, ma toccano il backbone del sistema e meritano di non sparire dietro ai refinement proposal.

## Architecture Assessment By Area

### Sync / Core

Valutazione:

- buono

Commento:

- il pattern di mirror tecnici e fact canonici e corretto
- i problemi aperti sono di robustezza runtime, non di modello

### Articoli / Famiglie

Valutazione:

- molto buono

Commento:

- e il punto in cui il progetto ha costruito il miglior linguaggio configurativo
- va pero chiarita meglio la frontiera tra articolo finito e articolo materiale grezzo

### Planning

Valutazione:

- molto buono

Commento:

- il modulo e leggibile, coerente e gia abbastanza stabile
- dovrebbe diventare il benchmark interno per chiarezza degli altri moduli

### Warnings

Valutazione:

- buono

Commento:

- il confine e corretto
- va preservato con rigore per evitare reintroduzione di warning locali non canonici

### Proposals

Valutazione:

- promettente ma non ancora stabilizzato

Commento:

- il modulo ha trovato un buon confine con il workspace temporaneo
- ma la modellazione delle logiche e ancora in fase di scoperta

## Main Recommendation

La raccomandazione principale e:

> fermare temporaneamente la proliferazione di nuove logiche proposal e fare un consolidamento architetturale leggero del dominio `Production Proposals`.

Ma non solo.

Serve anche una piccola pulizia di livello progetto:

1. congelare i principi davvero stabili
2. separare i debiti strutturali cross-modulo dai refinement locali
3. ridurre la probabilita che ogni nuovo caso operativo generi un nuovo tipo di logica monolitica

## Suggested Rebase

### 1. Proposals architecture rebase

Produrre un documento breve che fissi:

- confine del modulo
- ciclo di vita workspace/export/history
- taxonomy delle logiche proposal
- assi compositivi delle logiche
- ownership dei dati finito/materiale/famiglia

Obiettivo:

- evitare che `proposal_*` cresca solo per enumerazione di varianti

### 2. Distinguere “logic family” da “logic variant”

Ragionamento consigliato:

- `target pieces` = famiglia base
- `full bar` = famiglia di logiche
- `strict_capacity` e `capacity_floor` = varianti/policy della stessa famiglia

Questo non impone subito un refactor tecnico, ma cambia come pensare i prossimi task.

### 3. Aprire un piccolo stream backbone

Senza questo, il progetto rischia di continuare a rifinire il dominio sopra fondamenta runtime ancora non completamente robuste.

Priorita suggerita:

- fix architetturale `MAG_REALE`
- refresh fail-fast / freshness coerente
- hardening `core_articolo_config` orfani

### 4. Ridurre il ritmo dei DL locali sui refinement minori

Non per smettere di documentare.

Ma per distinguere meglio:

- decisioni strutturali
- correzioni implementative
- task operativi

Quando il pattern e gia chiaro, non ogni refinement merita un nuovo DL.

## Proposed Next Sequence

1. Chiudere una review/rebase architetturale dedicata a `Production Proposals`.
2. Separare backlog `backbone` da backlog `proposal refinement`.
3. Eseguire almeno uno dei tre fix backbone aperti.
4. Solo dopo riprendere:
   - logiche proposal aggiuntive
   - writer `xlsx`
   - export/reconcile enrichment

## What Should Not Be Changed

Queste scelte non andrebbero rimesse in discussione adesso:

- Easy `read-only`
- layering `sync/core/app/shared`
- fact canonici quantitativi
- `Warnings` come modulo separato
- `Planning Candidates` come inbox live del bisogno
- `Production Proposals` come workspace temporaneo downstream di planning
- pattern `famiglia -> articolo -> effective`

## Final Assessment

Il progetto e architetturalmente buono.

La V2 non sta degenerando, ma sta entrando nella fase in cui le buone idee locali possono iniziare a produrre dispersione se non vengono ricondensate.

La cosa giusta adesso non e rallentare lo sviluppo in generale. E:

- riallineare il modello in 1-2 punti chiave
- fare pulizia sui debiti backbone
- poi ripartire con uno spazio concettuale piu pulito

## References

- [SYSTEM_OVERVIEW.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/SYSTEM_OVERVIEW.md#L1)
- [AI_HANDOFF_CURRENT_STATE.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/AI_HANDOFF_CURRENT_STATE.md#L1)
- [STATUS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/roadmap/STATUS.md#L1)
- [IMPLEMENTATION_PATTERNS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/guides/IMPLEMENTATION_PATTERNS.md#L1)
- [KNOWN_BUGS.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/KNOWN_BUGS.md#L1)
