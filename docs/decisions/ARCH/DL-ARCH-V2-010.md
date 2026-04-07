# DL-ARCH-V2-010 - Core slice clienti + destinazioni

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

La V2 dispone ora di:

- `sync_clienti` come target interno read-only derivato da `ANACLI`
- `sync_destinazioni` come target interno read-only derivato da `POT_DESTDIV`
- dipendenza esplicita `destinazioni -> clienti`
- policy di freshness e bootstrap mode per surface dati-dipendenti

I target di sync sono pero ancora mirror tecnici vicini alla sorgente.

Per alimentare la prima surface logistica clienti/destinazioni serve un livello Core che:

- legga solo dai target sync interni
- costruisca la relazione tra cliente e destinazione
- introduca i primi dati interni configurabili
- esponga un modello applicativo stabile per backend e UI

Senza questo slice Core il rischio e:

- usare direttamente i target sync come modello UI
- mescolare dati Easy read-only e dati interni nello stesso layer
- introdurre logiche di join e fallback direttamente nel frontend

## Decision

La V2 introduce un primo slice Core `clienti + destinazioni` come ponte tra il layer `sync` e la prima surface logistica.

Questo slice:

- legge da `sync_clienti`
- legge da `sync_destinazioni`
- introduce configurazione interna minima per destinazione
- espone read model applicativi orientati alla surface

Il Core non modifica mai i target `sync_*`.

## 1. Boundary del slice Core

Il primo slice Core ha perimetro limitato a:

- relazione cliente -> destinazioni
- arricchimento interno minimo della destinazione
- read model per navigazione e dettaglio

Non include ancora:

- logiche di pianificazione
- regole di spedizione
- contatti logistici
- orchestrazione runtime della sync

## 2. Ruolo concettuale delle entita

Nel Core iniziale valgono queste regole:

- il cliente e il contenitore amministrativo
- la destinazione e l'unita operativa primaria

Conseguenza:

- la navigazione parte dal cliente
- la configurazione avviene sulla destinazione

Questa semantica e il fondamento applicativo della futura surface a 3 colonne.

## 3. Origine dei dati

Il Core costruisce il proprio modello a partire da:

- dati sincronizzati read-only da Easy
- dati interni V2 di configurazione destinazione

Regole:

- `sync_clienti` resta la fonte interna per i dati cliente provenienti da Easy
- `sync_destinazioni` resta la fonte interna per i dati destinazione provenienti da Easy
- i dati configurabili della destinazione vivono in tabelle Core dedicate

## 4. Primo dato interno configurabile

Il primo dato interno introdotto dal Core e:

- `nickname_destinazione`

`nickname_destinazione`:

- e interno alla V2
- non proviene da Easy
- non viene mai scritto nei target sync
- e governato dal Core

Questo dato e persistito in una struttura Core dedicata alla configurazione di destinazione.

## 5. Identita Core della destinazione

Nel primo slice la destinazione nel Core e identificata usando la source identity tecnica gia stabile nel layer sync:

- `codice_destinazione`

Il Core mantiene inoltre come riferimenti rilevanti:

- `codice_cli`
- `numero_progressivo_cliente`

Regola:

- il Core non ridefinisce una nuova identita artificiale se la source identity esistente e gia stabile nel sistema interno

## 6. Read model richiesti dal Core

Il primo slice Core deve esporre almeno tre read model logici.

### 6.1 Lista clienti

Campi minimi:

- `codice_cli`
- `ragione_sociale`
- eventuali campi sintetici utili alla ricerca

Scopo:

- popolare la colonna sinistra della surface

### 6.2 Lista destinazioni per cliente

Campi minimi:

- `codice_destinazione`
- `codice_cli`
- `numero_progressivo_cliente`
- `indirizzo`
- `citta`
- `provincia`
- `nickname_destinazione`
- un campo descrittivo sintetico per la riga

Scopo:

- popolare la colonna centrale della surface

### 6.3 Dettaglio destinazione

Campi minimi:

- `codice_destinazione`
- `codice_cli`
- `numero_progressivo_cliente`
- `ragione_sociale_cliente`
- `indirizzo`
- `citta`
- `provincia`
- `nazione_codice`
- `telefono_1`
- `nickname_destinazione`

Scopo:

- popolare la colonna destra della surface

## 7. Regola sui campi non ancora presenti

Il primo slice Core non introduce campi Easy non ancora sincronizzati.

In particolare:

- `CAP` non entra nel primo slice se non e presente nei target sync correnti
- `nome sede` o ragione sociale destinazione non entra se non e presente nel mapping attivo

Regola:

- il Core puo comporre e presentare i dati disponibili
- il Core non deve inventare o dedurre dati sorgente assenti

## 8. Campo descrittivo sintetico della destinazione

Per supportare la UI senza forzare nuovi campi sorgente nel primo slice, il Core puo esporre un campo sintetico di presentazione, ad esempio `display_label`.

Ordine consigliato:

1. `nickname_destinazione`, se presente
2. `indirizzo`, se presente
3. `codice_destinazione`

Regola:

- `display_label` e un derivato Core orientato alla lettura
- non sostituisce i campi sorgente e non modifica il mapping Easy

## 9. Separazione read-only vs configurabile

Nel read model Core deve essere sempre chiaro cosa e:

- dato Easy read-only
- dato interno configurabile

Regole:

- i campi provenienti da Easy non sono modificabili dalla surface
- i campi interni configurabili sono persistiti nel database interno V2
- il Core espone un contratto che distingua chiaramente i due gruppi

## 10. Relazione con freshness e bootstrap mode

Questo slice Core dipende da:

- `clienti`
- `destinazioni`

Il Core non implementa direttamente la sync, ma deve essere compatibile con il modello runtime gia fissato.

Regole:

- se non esiste snapshot locale iniziale, la surface segue il bootstrap mode definito dal layer runtime
- se i dati sono stale ma disponibili, il Core puo servire il read model corrente mentre il refresh avviene in background

## 11. Confine backend/frontend

Backend:

- costruisce i read model Core
- applica join e fallback di presentazione ammessi
- gestisce la persistenza di `nickname_destinazione`

Frontend:

- consuma i read model Core
- non accede direttamente ai target `sync_*`
- non ricostruisce nel client la relazione dati Easy + dati interni

## Esclusioni

Questo DL NON definisce:

- dettaglio DDL delle tabelle Core
- design delle API HTTP
- layout grafico della surface
- scheduler o orchestrazione runtime
- configurazioni logistiche oltre `nickname_destinazione`

## Consequences

### Positive

- protegge la separazione tra `sync` e UI
- introduce un primo modello operativo leggibile per la surface logistica
- consente di partire con UIX 2 senza estendere subito il mapping Easy oltre il necessario
- crea il punto corretto in cui persistire `nickname_destinazione`

### Negative / Trade-off

- introduce un layer in piu rispetto all'uso diretto dei mirror sync
- richiede di modellare con disciplina i read model e i dati interni minimi
- lascia fuori alcuni campi desiderabili fino a un slice successivo

## Impatto sul progetto

Questo DL diventa riferimento per:

- il primo task Core clienti + destinazioni
- la persistenza interna di `nickname_destinazione`
- le API che alimenteranno la surface logistica

E prerequisito diretto per:

- `TASK-V2-012` Core clienti + destinazioni
- l'implementazione della surface descritta in `DL-UIX-V2-002`

## Notes

- Questo DL non sostituisce i mapping Easy: li usa come input stabile.
- Il primo slice privilegia un modello operativo minimo ma pulito.
- Campi come `CAP` o un nome destinazione sorgente potranno entrare in slice successivi, dopo estensione del mapping sync.
- `DL-ARCH-V2-012` raffina questo modello introducendo la regola per cui il cliente va trattato come destinazione principale esplicita nel Core.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-012.md`
- `docs/decisions/UIX/DL-UIX-V2-001.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/integrations/easy/EASY_CLIENTI.md`
- `docs/integrations/easy/EASY_DESTINAZIONI.md`
