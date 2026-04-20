# ODE V2 - Cleanup Plan 2026-04-17

## Scopo

Questo documento definisce una strategia di pulizia del progetto V2 senza introdurre regressioni o cancellazioni premature.

La regola di base e:

- non cancellare in blocco
- separare:
  - cio che si puo rimuovere subito
  - cio che va archiviato o marcato superseded
  - cio che va tenuto ancora per compatibilita

## Principio guida

La pulizia della V2 deve ridurre:

- carico cognitivo
- duplicazioni
- surface legacy ancora visibili
- documentazione non piu guida

senza rompere:

- compatibilita runtime
- dati gia salvati
- test
- tracciabilita del rebase

## Bucket di cleanup

### A. Rimuovibile subito o quasi subito

Elementi che oggi non sono piu surface o concetti guida e che non dovrebbero restare in primo piano.

Primo cluster candidato:

- surface `Criticita Articoli` come voce di navigazione primaria
- label `legacy` ancora esposte in punti della UI dove non servono al flusso operativo

Regola:

- prima rimuovere dalla navigazione
- poi valutare la rimozione del codice solo dopo verifica che non serva piu come fallback tecnico

### B. Da archiviare o marcare superseded

Elementi documentali che hanno ancora valore storico ma non devono piu guidare il lavoro corrente.

Cluster tipici:

- note di transizione non piu attive
- decisioni o spec sorpassate da DL di rebase piu recenti
- documenti roadmap non piu rappresentativi della V2 reale

Regola:

- non cancellare i DL storici
- se non sono piu guida:
  - marcarli `superseded by`
  - oppure spostarli in `docs/archive/`

### C. Da tenere per compatibilita finche non verificato

Elementi legacy o alias che possono ancora avere impatto reale su:

- dati gia configurati
- config admin/articoli
- test di compatibilita
- vecchi snapshot o chiavi persistite

Primo cluster candidato:

- alias proposal `proposal_required_qty_total_v1`
- eventuali riferimenti backend/frontend collegati
- compatibilita residue su route o surface ancora accessibili ma non piu primarie

Regola:

- prima review completa di riferimenti e dati
- poi task di rimozione mirata

## Sequenza consigliata

### 1. Docs Cleanup

Obiettivo:

- ridurre i documenti che oggi competono con il baseline del rebase
- chiarire cosa e attivo e cosa e solo storico

Output attesi:

- indici piu puliti
- documenti superseded marcati
- riduzione dei riferimenti contraddittori

### 2. UI / Navigation Cleanup

Obiettivo:

- togliere dalle navigation path e dalla percezione utente le surface legacy non piu operative

Output attesi:

- sidebar piu coerente
- meno doppie surface mentali
- meno confusione tra stream attivi e stream legacy

### 3. Compatibility Review prima di rimozione codice

Obiettivo:

- decidere cosa e davvero morto
- evitare di rimuovere alias o fallback ancora usati

Output attesi:

- lista breve di compatibilita da mantenere
- lista breve di compatibilita rimovibili

## Candidati concreti gia emersi

### Surface legacy

- `frontend/src/components/AppShell.tsx`
  - voce `Criticita (legacy)`
- `frontend/src/pages/surfaces/CriticitaPage.tsx`
  - surface legacy/deprecated ancora presente tecnicamente

### Compatibilita proposal da rivedere

- `backend/src/nssp_v2/core/production_proposals/config.py`
- `backend/src/nssp_v2/core/production_proposals/logic.py`
- `frontend/src/lib/proposalLogicMeta.ts`

### Documentazione da riallineare

- overview e handoff che citano ancora surface legacy come presenti tecnicamente
- note che raccontano compatibilita ormai superate dal rebase

## Guardrail

- non cancellare decisioni architetturali storiche senza archivio o marcatura esplicita
- non rimuovere alias compatibili senza review di riferimenti e test
- non fare cleanup distruttivo assieme a refactor funzionali non correlati

## Task collegati

- `TASK-V2-146` docs cleanup e archive alignment
- `TASK-V2-147` navigation cleanup delle surface legacy
- `TASK-V2-148` compatibility review di alias e codice legacy prima della rimozione
