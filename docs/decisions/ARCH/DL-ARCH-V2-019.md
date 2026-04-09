# DL-ARCH-V2-019 - Quantita appartata cliente come fact canonico intermedio

## Status
Approved

## Date
2026-04-09

## Context

La V2 ha gia introdotto tre building block canonici distinti:

- `inventory`
- `commitments`
- `customer_order_lines`

Nel modello ordini cliente esiste pero uno stato operativo che non coincide con nessuno dei tre:

- `DOC_QTAP`

`DOC_QTAP` rappresenta quantita gia inscatolata/appartata per cliente:

- non ancora evasa
- non ancora uscita dai movimenti di magazzino
- non piu giacenza libera
- non piu domanda ancora da coprire operativamente

Se questo stato viene assorbito troppo presto in:

- `inventory`
- `commitments`
- o nella futura `availability`

la V2 perde un passaggio semantico reale del dominio.

## Decision

La V2 introduce un fact canonico intermedio separato, derivato da `DOC_QTAP`, che rappresenta la quantita
fisicamente appartata per cliente ma non ancora evasa.

Nel lessico V2 il concetto puo essere espresso come:

- `set_aside`
- `set_aside_stock`
- `customer_set_aside`

Il nome definitivo della tabella/read model potra essere fissato nei task attuativi, ma il concetto resta stabile:

> la quantita appartata per cliente e un fact canonico distinto da `inventory`, `commitments` e `availability`.

## 1. Definizione

`Set aside` e la quota di articolo:

- gia preparata fisicamente per un cliente
- non ancora uscita dal sistema come evasione
- quindi ancora presente nello stock fisico
- ma non piu disponibile come stock libero

Regola:

> `Set aside` non e un mirror sync e non e un campo raw consumabile direttamente dai moduli.
> E una computed fact canonica del `core`.

## 2. Separazione concettuale

La V2 mantiene distinti quattro concetti:

- `inventory`
  - stock fisico netto
- `commitments`
  - domanda ancora da coprire operativamente
- `set_aside`
  - quota gia fisicamente preparata per cliente
- `availability`
  - concetto derivato futuro

Regola:

> `Set aside` non deve essere compresso automaticamente ne dentro `commitments` ne dentro `inventory`.

## 3. Sorgente iniziale

La provenienza iniziale del fact `set_aside` e:

- `customer_order`

tramite:

- `DOC_QTAP`

letto dalle righe ordine cliente canoniche del Core.

La sequenza corretta e:

1. mirror `V_TORDCLI`
2. Core `customer_order_lines`
3. computed fact `set_aside`

Non e ammesso costruire questo fact direttamente dal mirror sync grezzo nei moduli applicativi.

## 4. Modello canonico minimo

Il fact canonico puo includere almeno:

- `article_code`
- `source_type`
- `source_reference`
- `set_aside_qty`
- `computed_at`

Campi opzionali utili:

- `customer_code`
- `destination_code`
- `expected_delivery_date`
- `source_status`

## 5. Regole quantitative V1

Nel perimetro V1:

- `set_aside_qty = DOC_QTAP`

con le normali regole di sanita applicativa:

- quantita nulle o non positive non generano fact attivi
- il fact nasce solo se la riga ordine canonica ha un `article_code` valido

Questo fact non sostituisce `open_qty`, che resta:

- la domanda ancora da coprire

e non sostituisce `fulfilled_qty`, che resta:

- la domanda gia evasa

## 6. Relazione con commitments

Per le righe ordine cliente:

- `commitments` V1 usa `open_qty`
- `set_aside` usa `DOC_QTAP`

I due fact devono poter convivere sullo stesso articolo e sulla stessa origine, perche rappresentano stati diversi:

- domanda ancora aperta
- quota gia fisicamente preparata

Regola:

> `Set aside` non annulla il bisogno di `commitments`, ma ne sottrae la parte gia operativamente assorbita a monte del calcolo di `open_qty`.

## 7. Relazione con inventory

`Set aside` non modifica la definizione di `inventory`:

- lo stock fisico resta calcolato dai movimenti di magazzino

Finche la merce non viene registrata come uscita:

- resta in `inventory`

ma non e piu stock libero.

Regola:

> `Inventory` misura lo stock fisico; `set_aside` misura la quota fisicamente non libera.

## 8. Relazione con availability futura

La V2 rinvia ancora la definizione ufficiale di `availability`, ma fissa fin d'ora che essa dovra tenere conto almeno di:

- `inventory`
- `commitments`
- `set_aside`

Quindi la formula futura non potra essere introdotta in modo ingenuo come:

- `availability = inventory - commitments`

senza considerare esplicitamente il significato di `set_aside`.

Regola:

> prima di introdurre `availability`, la V2 deve disporre di un fact canonico separato per la quantita appartata.

## Consequences

### Positive

- evita di schiacciare stati operativi diversi in un'unica quantita
- prepara una `availability` piu corretta
- rende riusabile il concetto di merce appartata anche per future UI o alert operativi

### Negative / Trade-off

- introduce un ulteriore fact canonico da mantenere
- richiede disciplina nel non semplificare prematuramente il modello
- rinvia di poco l'introduzione della `availability`

## Impatto sul progetto

Questo DL prepara:

- un futuro task Core sul fact `set_aside` da ordini cliente
- la futura definizione di `availability`
- eventuali viste o API che distinguano stock fisico, impegno e appartato

Non introduce ancora:

- disponibilita finale
- allocazioni
- UI dedicata

## Notes

- `DOC_QTAP` e una semantica di dominio, non un semplice dettaglio tecnico Easy.
- Il fatto canonico intermedio nasce per evitare una modellazione troppo povera della disponibilita.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-016.md`
- `docs/decisions/ARCH/DL-ARCH-V2-017.md`
- `docs/decisions/ARCH/DL-ARCH-V2-018.md`
- `docs/integrations/easy/EASY_RIGHE_ORDINE_CLIENTE.md`
