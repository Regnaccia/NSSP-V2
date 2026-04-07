# UIX_SPEC_CLIENTI_DESTINAZIONI - Variante a 3 colonne

## Status
In Use

Valori ammessi:

- `Draft`
- `In Use`
- `Superseded`

## Date
2026-04-07

## Purpose

Documentare come il pattern UIX multi-colonna standard viene applicato al caso `clienti/destinazioni`.

## Related Documents

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-003.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
- `docs/task/TASK-V2-012-core-clienti-destinazioni.md`
- `docs/task/TASK-V2-013-ui-clienti-destinazioni.md`
- `docs/task/TASK-V2-015-destinazione-principale-derivata.md`

## Variant

- pattern adottato: `3 colonne`

## Column Model

### Colonna 1 - Clienti

Contiene:

- elenco clienti
- filtro minimo per codice o ragione sociale
- selezione singola cliente

Ruolo:

- livello amministrativo di accesso e raggruppamento

### Colonna 2 - Destinazioni

Contiene:

- elenco destinazioni del cliente selezionato
- destinazione principale derivata dal cliente
- eventuali destinazioni aggiuntive da `POT_DESTDIV`

Ruolo:

- livello operativo principale di selezione

### Colonna 3 - Dettaglio e configurazione destinazione

Contiene:

- dati anagrafici read-only esposti dal Core
- dati interni configurabili della destinazione

Nel primo slice il dato interno principale e:

- `nickname_destinazione`

## Data Semantics

### Read-only

I dati provenienti da Easy o derivati dal Core a partire da Easy sono visualizzati come read-only.

### Configurable

I dati interni persistiti nel sistema V2 sono presentati come configurabili.

Nel primo slice:

- `nickname_destinazione`

## Selection Flow

- nessun cliente selezionato -> colonna 2 e 3 in stato vuoto guidato
- cliente selezionato -> popolamento colonna 2
- destinazione selezionata -> popolamento colonna 3
- cambio cliente -> reset coerente della selezione destinazione

## UX Notes

- le colonne devono poter avere scroll indipendente
- la selezione attiva deve restare evidente
- la destinazione principale derivata deve risultare esplicita e non confondersi con le destinazioni aggiuntive

## Notes

- Questa spec descrive il caso concreto `logistica`.
- Varianti future, come `articoli`, useranno lo stesso pattern generale con un numero differente di colonne.

## References

- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-010.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
