# DL-ARCH-V2-022 - Refresh semantici backend con dipendenze interne

## Status

Accepted

## Date

2026-04-09

## Context

La V2 ha introdotto refresh manuali backend-controlled per diverse surface, in particolare:

- `logistica`
- `articoli`
- `produzioni`

Con l'aumento dei fact canonici derivati, la surface `articoli` dipende ormai da una chain composita:

- `sync_articoli`
- `sync_mag_reale`
- `sync_righe_ordine_cliente`
- `sync_produzioni_attive`
- `rebuild_inventory_positions`
- `rebuild_customer_set_aside`
- `rebuild_commitments`
- `rebuild_availability`

Se questa conoscenza resta distribuita:

- nei router API
- nella UI
- nei task operativi

il rischio e crescente:

- dimenticare un prerequisito
- ricalcolare un fact su dati stantii
- duplicare orchestration simili in piu punti
- aumentare il coupling tra UI e dipendenze tecniche del backend

La review di progetto del `2026-04-08` ha gia evidenziato come area critica l'orchestrazione cross-modulo dei refresh e dei fact derivati.

## Decision

La V2 adotta il pattern dei **refresh semantici backend con dipendenze interne**.

Questo significa che:

- la UI invoca refresh logici ad alto livello
- il backend incapsula la chain reale di sync e rebuild necessaria
- le dipendenze non vengono replicate manualmente dalla UI o da chiamanti esterni

Un refresh semantico:

- ha un nome orientato al significato applicativo
- dichiara i propri prerequisiti interni
- orchestra in ordine sync e rebuild
- applica comportamento `fail-fast` o `skip downstream on failed prerequisite`
- restituisce risultati tracciabili step-by-step

## Regole

### Regola 1 - La UI non orchestra dipendenze tecniche

La UI non deve conoscere la lista completa di sync e rebuild necessaria per riallineare un contesto applicativo.

La UI chiama un solo refresh logico, ad esempio:

- `refresh articoli`
- `refresh produzioni`

### Regola 2 - Il backend possiede la catena di dipendenze

Il backend definisce e mantiene la sequenza completa richiesta da ciascun refresh semantico.

Per la surface `articoli`, la chain puo evolvere senza cambiare il contratto UI.

### Regola 3 - I refresh semantici devono essere tracciabili

Ogni refresh semantico deve produrre output step-by-step:

- sync eseguite
- rebuild eseguiti
- step saltati
- eventuali errori

### Regola 4 - Gli step dipendenti non devono proseguire su prerequisiti falliti

Se uno step fallisce:

- gli step downstream che dipendono da esso non devono partire
- il risultato del refresh deve riflettere il fallimento parziale

### Regola 5 - I refresh semantici non cambiano la semantica dei fact

Il refresh semantico orchestra:

- `sync_*`
- `rebuild_*`

ma non ridefinisce la semantica dei fact canonici:

- `inventory`
- `customer_set_aside`
- `commitments`
- `availability`

## Consequences

### Positive

- minore coupling UI-backend
- minore rischio di dimenticare dipendenze
- piu facile evolvere la chain interna dei refresh
- migliore tracciabilita operativa
- base piu robusta per scheduler futuri

### Negative

- backend orchestration piu ricca
- necessita di naming chiaro dei refresh logici
- maggior attenzione alla gestione degli errori step-by-step

## Initial Application

Il primo caso applicativo esplicito di questo pattern e la surface `articoli`.

L'evoluzione corretta e:

- oggi: refresh sequenziale esplicito documentato nei task
- target: refresh semantico backend che incapsula internamente la chain reale

## Out of Scope

Questo DL non introduce ancora:

- scheduler automatico
- parallelizzazione dei refresh
- orchestrazione distribuita multi-process
- workflow engine separato

## Related

- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-021.md`
- `docs/task/TASK-V2-053-refresh-sequenziale-articoli-con-commitments.md`
- `docs/task/TASK-V2-054-refresh-semantici-backend.md`
