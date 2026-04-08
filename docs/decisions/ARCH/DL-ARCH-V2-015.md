# DL-ARCH-V2-015 - Core produzioni aggregato, bucket e stato computato

## Status
Approved

## Date
2026-04-08

## Context

La V2 ha gia fissato:

- mirror Easy separati per attive e storiche
- accesso Easy solo `read-only`
- mapping tecnico iniziale in `EASY_PRODUZIONI.md`

Nel dominio `produzioni` emerge una distinzione importante:

- `DPRE_PROD` contiene produzioni attive
- `SDPRE_PROD` contiene produzioni storiche

Per rigore architetturale i due flussi devono restare separati nel layer `sync`,
ma la UI e i futuri casi d'uso dovranno leggere un modello unificato nel `core`.

Serve inoltre un primo computed fact di dominio:

- capire se una produzione e `attiva` o `completata`

Infine, e noto che in Easy possono essere presenti dati sporchi o non coerenti;
serve quindi un override manuale interno che consenta di forzare la chiusura logica
di una produzione senza alterare il mirror sorgente.

## Decision

La V2 introduce un primo `core produzioni` che:

- aggrega i mirror `sync_produzioni_attive` e `sync_produzioni_storiche`
- espone un campo `bucket = active | historical`
- calcola un primo computed fact `stato_produzione`
- supporta un override interno `forza_completata`

## 1. Mirror separati, aggregazione nel Core

I mirror restano distinti:

- `sync_produzioni_attive`
- `sync_produzioni_storiche`

Il `core` e il primo layer autorizzato ad aggregarli in una vista unificata.

Regola:

> La distinzione tra `attive` e `storiche` si preserva nel `sync`; la vista unificata nasce solo nel `core`.

## 2. Bucket nel Core

Ogni record esposto dal `core produzioni` deve dichiarare un bucket applicativo:

- `active`
- `historical`

Il bucket:

- deriva dalla provenienza del record nel mirror sync
- non e un campo calcolato dalla UI
- non deve retroagire sui mirror sync

## 3. Primo computed fact: stato produzione

Il `core` introduce il primo computed fact `stato_produzione`.

Valori iniziali ammessi:

- `attiva`
- `completata`

Regola di calcolo standard:

- `attiva` se `DOC_QTOR > DOC_QTEV`
- `completata` se `DOC_QTEV >= DOC_QTOR`

Nel `core` i valori sync rilevanti vengono letti come:

- `quantita_ordinata`
- `quantita_prodotta`

## 4. Override manuale: forza completata

Il `core` introduce un flag interno:

- `forza_completata` booleano

Scopo:

- escludere dati sporchi noti presenti in Easy
- consentire alla V2 di trattare una produzione come chiusa logicamente anche quando i dati sorgente non sono affidabili

Regola:

> L'override vive solo nel `core` e non modifica mai il mirror `sync` ne la sorgente Easy.

## 5. Precedenza del computed fact

La regola di precedenza e:

1. se `forza_completata = true` -> `stato_produzione = completata`
2. altrimenti si applica la regola standard su `quantita_ordinata` e `quantita_prodotta`

Questo rende esplicita la distinzione tra:

- stato calcolato da dati sorgente
- stato corretto internamente per ragioni operative

## 6. Confine tra Sync e Core

Il layer `sync`:

- legge da Easy
- allinea i mirror dedicati
- non decide `bucket`
- non calcola `stato_produzione`
- non gestisce override manuali

Il layer `core`:

- aggrega i mirror
- espone `bucket`
- calcola `stato_produzione`
- persiste `forza_completata`

Regola fondamentale:

> Il `sync` trasferisce dati; il `core` costruisce bucket, stato e correzioni operative interne.

## 7. Primo perimetro attuativo

Il primo task attuativo dovra coprire:

- query/read model aggregato `produzioni`
- `bucket` esposto nel contratto core
- `stato_produzione` esposto nel contratto core
- persistenza del flag `forza_completata`
- endpoint o comando minimo per modificare il flag

Fuori scope nel primo slice:

- pianificazione avanzata
- stati intermedi diversi da `attiva` / `completata`
- scheduler automatico
- workflow di chiusura multipasso

## Consequences

### Positive

- separazione pulita tra mirror sorgente e modello applicativo
- primo computed fact di dominio esplicito
- gestione controllata dei dati sporchi senza toccare Easy
- base solida per future viste `produzioni`

### Negative / Trade-off

- duplicazione applicativa dei dati nel `core`
- necessita di persistere un override interno
- possibile futura estensione dello stato oltre i due valori iniziali

## Impatto sul progetto

Questo DL prepara il primo slice `produzioni` che andra oltre il solo mirror tecnico.

Diventa base per:

- il primo `core produzioni`
- la futura UI `produzioni`
- futuri filtri e viste per stato e bucket

## Notes

- Questo DL non cambia il vincolo Easy `read-only`.
- `forza_completata` e una correzione interna V2, non un dato di sorgente.
- Il pattern e coerente con i mirror separati `attive/storiche` e con l'aggregazione nel `core`.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/integrations/easy/EASY_PRODUZIONI.md`
