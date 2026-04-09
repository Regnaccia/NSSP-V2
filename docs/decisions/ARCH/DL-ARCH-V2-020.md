# DL-ARCH-V2-020 - Mirror operativo ordini cliente e storico separato

## Status
Approved

## Date
2026-04-09

## Context

La V2 usa `V_TORDCLI` come sorgente delle righe ordine cliente attive per costruire:

- `customer_order_lines`
- `commitments`
- `customer_set_aside`

L'implementazione iniziale di `sync_righe_ordine_cliente` ha adottato:

- `full_scan`
- `upsert`
- `no_delete_handling`

Questa scelta conserva nel mirror interno anche righe non piu presenti in `V_TORDCLI`.

Nel caso operativo reale:

- un ordine puo sparire da `V_TORDCLI` dopo emissione DDT
- il movimento di magazzino viene gia registrato altrove
- la riga non e piu operativamente attiva

Se il mirror continua a trattenerla, i fact derivati restano semanticamente errati.

Easy dispone gia di sorgenti storiche dedicate; quindi il mirror operativo V2 non deve fungere da archivio locale.

## Decision

La V2 stabilisce che `sync_righe_ordine_cliente` e:

- un mirror operativo delle sole righe ancora presenti in `V_TORDCLI`

e non:

- uno storico locale
- una tabella di audit

Regola:

> le righe non piu presenti nella full scan corrente di `V_TORDCLI` devono essere rimosse dal mirror operativo.

Lo storico, se necessario, dovra essere costruito in futuro da:

- sorgenti storiche Easy dedicate
- stream separati

## 1. Natura della sorgente

`V_TORDCLI` viene trattata come:

- dataset operativo corrente

Non viene trattata come:

- archivio completo degli ordini cliente

## 2. Delete handling del mirror

Per `sync_righe_ordine_cliente` la politica corretta non e:

- `no_delete_handling`

ma una politica equivalente a:

- rimozione dei record non piu presenti nella full scan attiva

Questo vale specificamente per questa sorgente e per il suo significato operativo.

## 3. Effetti sui fact derivati

Quando una riga ordine sparisce da `V_TORDCLI`:

- non deve piu esistere nel mirror operativo
- non deve piu alimentare `customer_order_lines`
- non deve piu alimentare `commitments`
- non deve piu alimentare `customer_set_aside`

## 4. Separazione tra operativo e storico

La V2 separa esplicitamente:

- mirror operativo ordini attivi
- eventuale storico ordini cliente

Regola:

> il bisogno futuro di audit non giustifica la permanenza di righe chiuse nel mirror operativo.

## 5. Implicazioni prestazionali

Questa scelta riduce la crescita del mirror operativo e il carico sui rebuild di:

- `customer_order_lines`
- `commitments`
- `customer_set_aside`

Quindi migliora anche la sostenibilita prestazionale del flusso.

## Consequences

### Positive

- i fact derivati restano semanticamente corretti
- il mirror operativo non accumula righe chiuse
- il dataset usato dai rebuild rimane piu leggero
- storico e audit possono essere modellati in modo pulito e separato

### Negative / Trade-off

- il mirror operativo non puo piu essere usato come pseudo-storico
- l'audit futuro richiedera un nuovo stream dedicato
- il contratto operativo della sync ordini cliente deve essere corretto

## Impatto sul progetto

Questo DL prepara:

- un task correttivo sulla sync `righe_ordine_cliente`
- il riallineamento dei fact `customer_order_lines`, `commitments` e `customer_set_aside`
- un futuro stream storico separato, se e quando servira

Non introduce ancora:

- storico ordini locale
- availability
- UI storico ordini

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/decisions/ARCH/DL-ARCH-V2-019.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`
- `docs/task/TASK-V2-040-sync-righe-ordine-cliente.md`
