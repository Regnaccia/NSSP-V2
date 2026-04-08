# DL-ARCH-V2-017 - Impegno come computed fact canonico

## Status
Approved

## Date
2026-04-08

## Context

La V2 ha gia introdotto:

- `inventory` / `on hand stock` come computed fact canonico di giacenza
- separazione netta tra mirror sync, computed fact Core e moduli applicativi

Per costruire in seguito il concetto di `disponibilita`, la V2 deve introdurre un secondo building block canonico e indipendente:

- `impegno`

`Impegno` non coincide con la giacenza e non coincide ancora con la disponibilita.
Rappresenta la quantita necessaria o assorbita da una domanda operativa non ancora chiusa.

Nel primo perimetro previsto, le provenienze iniziali di `impegno` sono:

- produzioni attive non completate
- righe ordine cliente ancora aperte

In futuro il modello dovra poter accogliere altre provenienze, senza cambiare il concetto di base.

## Decision

La V2 introduce `impegno` come computed fact canonico del `core`, separato da:

- `inventory`
- `availability`

Il modello e:

- sorgenti operative diverse alimentano impegni omogenei
- gli impegni confluiscono in una fact canonica unica
- la futura disponibilita verra costruita sopra:
  - `inventory`
  - `commitments`

## 1. Definizione

`Impegno` e la quantita necessaria ma non ancora assorbita/chiusa, riferita a una domanda operativa.

Nel lessico V2:

- `commitment`
- `committed_qty`
- `impegno`

Regola:

> `Impegno` e una computed fact canonica del Core, non un campo diretto di una singola sorgente.

## 2. Separazione concettuale

La V2 mantiene distinti tre concetti:

- `inventory`
  - stock fisico netto
- `commitments`
  - quantita impegnata da domanda operativa
- `availability`
  - concetto derivato futuro

Regola:

> La disponibilita non va introdotta prima che `inventory` e `commitments` siano fatti canonici separati e riusabili.

## 3. Provenienze iniziali

Le prime provenienze ammesse di `impegno` sono:

- `production`
  - da produzioni attive non completate
- `customer_order`
  - da righe ordine cliente aperte

In futuro potranno essere introdotte altre provenienze, ad esempio:

- trasferimenti
- fabbisogni interni
- prenotazioni operative

## 4. Modello canonico

La fact canonica `commitments` puo includere almeno:

- `article_code`
- `source_type`
- `source_reference`
- `committed_qty`
- `computed_at`

Campi opzionali utili:

- `source_status`
- `source_date`
- `debug_payload` o riferimenti secondari, se necessari

## 5. Livello di aggregazione V1

La V1 di `impegno` e definita:

- per `article_code`

Nel primo slice non vengono ancora introdotti:

- livelli di priorita
- allocazioni
- compensazioni automatiche tra sorgenti
- impegno per magazzino specifico
- impegno per lotto o location

## 6. Regole iniziali per provenienza

### Production

L'impegno da produzione deriva da:

- produzioni attive
- non completate

La quantita impegnata deve riflettere la domanda di materiale o di articolo ancora aperta,
secondo il modello che verra fissato nei task attuativi.

### Customer Order

L'impegno da cliente deriva da:

- righe ordine ancora aperte

La quantita impegnata deve riflettere la parte non ancora chiusa o assorbita della domanda cliente,
secondo il modello che verra fissato nei task attuativi.

## 7. Confine tra sorgenti e fact canonica

Le sorgenti operative:

- non devono essere consumate direttamente dai moduli applicativi come "impegno canonico"
- devono essere trasformate nel `core` in una fact uniforme

I moduli applicativi devono consumare:

- `commitments`

e non:

- produzioni grezze
- righe ordine grezze

Regola:

> I moduli leggono l'impegno canonico, non ricostruiscono l'impegno partendo da sorgenti eterogenee.

## 8. Relazione con disponibilita futura

La disponibilita e esplicitamente rinviata a una fase successiva.

Direzione futura prevista:

- `availability = inventory - commitments`

ma questa formula non va introdotta ancora come computed fact ufficiale.

Prima devono esistere:

- `inventory_positions`
- `commitments`

robusti e riusabili.

## Consequences

### Positive

- separazione chiara tra stock fisico e domanda impegnata
- base pulita per futura disponibilita
- riuso cross-modulo di un concetto operativo unico
- onboarding piu semplice di nuove provenienze di impegno

### Negative / Trade-off

- necessita di mantenere una fact canonica aggiuntiva
- alcune regole per singola provenienza andranno dettagliate nei task attuativi
- la disponibilita resta intenzionalmente rinviata

## Impatto sul progetto

Questo DL prepara:

- futuri task `commitments` da produzione
- futuri task `commitments` da ordini cliente
- la futura introduzione di `availability`

Non introduce ancora:

- disponibilita finale
- allocazione
- ATP
- logiche di pianificazione avanzata

## Notes

- `Impegno` e un building block Core condiviso.
- La V1 privilegia uniformita e riuso, non copertura completa di tutte le provenienze.
- Le regole quantitative specifiche di ciascuna provenienza saranno fissate nei task attuativi.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
