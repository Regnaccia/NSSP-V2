# DL-ARCH-V2-013 - Core slice articoli minimale

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 sta introducendo il primo stream `produzione` partendo da:

- mirror sync `articoli` derivato da `ANAART`
- futura surface UI `articoli` nella variante a `2 colonne`

Per mantenere il confine architetturale corretto, la UI non deve leggere direttamente `sync_articoli`.

Serve quindi un primo slice Core `articoli` che:

- legga solo dal target sync interno
- esponga un modello applicativo stabile per backend e UI
- resti inizialmente semplice e molto vicino al mirror
- rinvii l'introduzione di dati interni finche non emergera una logica reale di dominio

## Decision

La V2 introduce un primo Core `articoli` minimale, inizialmente costruito come proiezione applicativa dei dati sincronizzati da `sync_articoli`.

Nel primo slice:

- il Core duplica in modo controllato i campi sincronizzati necessari alla UI
- non introduce ancora entita interne dedicate o configurazioni aggiuntive
- resta il solo contratto ammesso tra `sync` e UI

## 1. Boundary del slice Core

Il primo Core `articoli` ha perimetro limitato a:

- lettura dei dati da `sync_articoli`
- esposizione di lista articoli
- esposizione di dettaglio articolo
- eventuali campi sintetici di presentazione utili alla UI

Non include ancora:

- configurazioni interne articolo
- regole di produzione
- logiche di magazzino
- logiche di pianificazione
- join con altre entita

## 2. Origine dei dati

Il Core `articoli` legge solo da:

- `sync_articoli`

Regole:

- il Core non scrive mai in `sync_articoli`
- il Core non accede direttamente a Easy
- la UI non legge mai `sync_articoli` in modo diretto

## 3. Proiezione iniziale dei campi

Nel primo slice il Core puo esporre tutti i campi oggi sincronizzati in `sync_articoli`, senza introdurre subito una forte selezione di dominio.

Campi minimi attesi nel read model iniziale:

- `codice_articolo`
- `descrizione_1`
- `descrizione_2`
- `unita_misura_codice`
- `source_modified_at`
- `categoria_articolo_1`
- `materiale_grezzo_codice`
- `quantita_materiale_grezzo_occorrente`
- `quantita_materiale_grezzo_scarto`
- `misura_articolo`
- `codice_immagine`
- `contenitori_magazzino`
- `peso_grammi`

Regola:

> Nel primo slice il Core puo essere vicino al mirror, ma resta comunque un contratto applicativo separato dal layer `sync`.

## 4. Duplicazione controllata

La duplicazione iniziale dei campi dal mirror al Core e esplicitamente ammessa.

Questa duplicazione e giustificata per:

- alimentare la UI senza esporre il mirror tecnico
- mantenere il confine `sync -> core -> ui`
- rinviare la modellazione di entita interne finche non servono davvero

Regola:

- la duplicazione iniziale non deve trasformarsi in un secondo mirror opaco
- i futuri dati interni dovranno entrare nel Core in modo esplicito e incrementale
- i campi non piu utili potranno essere rimossi dal Core in slice successivi

## 5. Read model richiesti

Il primo Core `articoli` deve esporre almeno due read model logici.

### 5.1 Lista articoli

Campi minimi:

- `codice_articolo`
- un campo sintetico di display
- eventuali campi utili alla ricerca o scansione rapida

Scopo:

- popolare la colonna sinistra della futura UI `articoli`

### 5.2 Dettaglio articolo

Campi minimi:

- tutti i campi sincronizzati oggi ritenuti necessari al primo slice UI

Scopo:

- popolare la colonna destra di dettaglio/configurazione

## 6. Campo sintetico di presentazione

Per supportare la lista articoli senza imporre una logica UI nel frontend, il Core puo esporre un campo sintetico di lettura, ad esempio `display_label`.

Ordine consigliato:

1. `descrizione_1 + descrizione_2` se presenti
2. `descrizione_1`
3. `codice_articolo`

Regola:

- `display_label` e un derivato Core orientato alla lettura
- non modifica il mapping Easy

## 7. Ricerca e UI

Il Core deve poter supportare la futura UI `articoli`, ma la regola UX di normalizzazione ricerca resta separata.

Relazione con UIX:

- `DL-UIX-V2-002` definisce il pattern a `2 colonne`
- `DL-UIX-V2-004` definisce la normalizzazione dell'input di ricerca articolo
- il Core espone dati leggibili; la specifica UX concreta vive nella spec `articoli`

## 8. Dati interni futuri

Nel primo slice il Core `articoli` non introduce ancora entita o configurazioni interne dedicate.

I dati interni verranno aggiunti solo quando emergera una logica concreta, ad esempio:

- classificazioni operative
- flag di produzione
- attributi di magazzino
- note o configurazioni dedicate

Regola:

- nessun dato interno "preventivo"
- le entita interne si introducono solo quando servono davvero

## 9. Confine con la futura pulizia del modello

Il primo Core `articoli` privilegia velocita e chiarezza del percorso incrementale.

In slice successivi sara possibile:

- restringere i campi realmente esposti
- introdurre entita interne dedicate
- eliminare campi duplicati che non servono

Questa pulizia e prevista e non rappresenta un errore del primo slice.

## Esclusioni

Questo DL NON definisce:

- dettaglio DDL delle tabelle Core
- design delle API HTTP
- configurazioni interne articolo
- UI finale `articoli`
- trigger `sync on demand` per `articoli`

## Consequences

### Positive

- sblocca il percorso `sync -> core -> ui` per `articoli`
- evita che la UI legga direttamente i mirror sync
- consente di partire senza sovra-modellare il dominio troppo presto

### Negative / Trade-off

- il primo Core `articoli` sara inizialmente molto vicino al mirror
- alcuni campi esposti oggi potranno risultare non necessari in futuro
- la vera modellazione di dominio verra rinviata a slice successivi

## Impatto sul progetto

Questo DL diventa riferimento per:

- primo task Core `articoli`
- futura UI `articoli`
- evoluzione incrementale dei dati interni di `produzione`

E prerequisito diretto per:

- task attuativo del Core `articoli`
- futura surface `articoli`

## Notes

- Questo DL applica al dominio `articoli` lo stesso principio generale gia usato per `clienti/destinazioni`: la UI consuma il Core, non i mirror sync.
- La differenza e che qui il primo Core nasce volutamente piu vicino al mirror, per non introdurre subito entita interne premature.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
