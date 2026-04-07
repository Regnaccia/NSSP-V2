# DL-ARCH-V2-014 - Famiglia articolo come prima entita interna di produzione

## Status
Approved for initial implementation

## Date
2026-04-07

## Context

Con `TASK-V2-018`, `TASK-V2-019` e `TASK-V2-020` la V2 ha completato il primo percorso:

- mirror sync `articoli` da Easy
- Core `articoli` minimale
- surface browser `articoli` read-only

Il primo passo successivo naturale non e introdurre configurazioni generiche, ma aggiungere il primo dato interno stabile di dominio per `articoli`.

Serve un concetto che:

- non esiste come dato interno affidabile in Easy per il perimetro V2
- aiuta a classificare gli articoli secondo logica operativa interna
- possa essere esteso in futuro con ulteriori configurazioni

Il primo concetto scelto e `famiglia articolo`.

## Decision

La V2 introduce `famiglia articolo` come prima entita interna del dominio `articoli`.

Nel primo slice:

- esiste una tabella dedicata delle famiglie articolo
- ogni articolo puo essere associato a una famiglia interna
- la famiglia non sostituisce i dati Easy, ma li affianca nel Core
- il valore di famiglia e configurabile internamente e non deriva da Easy

## 1. Obiettivo della famiglia articolo

La `famiglia articolo` serve a classificare gli articoli secondo una tassonomia operativa interna della V2.

Non serve a:

- sostituire il mirror Easy
- ridefinire il codice articolo
- introdurre gia una gerarchia completa di dominio

Regola:

> La famiglia e il primo dato interno stabile associato all'articolo, distinto dai dati sincronizzati da Easy.

## 2. Catalogo iniziale delle famiglie

Nel primo slice il catalogo iniziale delle famiglie e limitato a:

- `materia_prima`
- `articolo_standard`
- `speciale`
- `barre`
- `conto_lavorazione`

Regole:

- il catalogo iniziale e controllato dal sistema
- i valori devono avere un codice stabile interno
- etichetta e descrizione utente possono essere aggiunte o raffinate senza cambiare il codice stabile

## 3. Modello dati

La V2 introduce almeno:

- una tabella `articolo_famiglie`
- un collegamento tra articolo e famiglia

Forma consigliata:

- `articolo_famiglie`
  - `id`
  - `code`
  - `label`
  - `description` opzionale
  - `sort_order` opzionale
  - `is_active`
- `core_articoli` o equivalente read model interno
  - `famiglia_id` nullable nel primo slice

Regola:

- il legame articolo -> famiglia e inizialmente opzionale
- la mancanza di famiglia non blocca il funzionamento della surface

## 4. Relazione con sync e Core

La famiglia articolo appartiene al Core, non al layer `sync`.

Regole:

- `sync_articoli` resta mirror read-only di Easy
- la famiglia non viene scritta nel mirror sync
- il Core combina dati Easy sincronizzati e classificazione interna

Regola fondamentale:

> Easy continua a fornire dati sorgente; il Core aggiunge significato interno.

## 5. Impatto sul contratto Core articoli

Il Core `articoli` evolve da semplice proiezione del mirror a primo read model misto:

- dati Easy read-only
- dati interni V2

Campi nuovi attesi nel contratto applicativo:

- `famiglia_code`
- `famiglia_label`

Il dettaglio articolo puo esporre anche:

- `famiglia_id`

La lista articoli puo introdurre la famiglia solo se utile alla UI, ma non e obbligatorio nel primo slice.

## 6. UX e configurazione

Nel primo slice la famiglia e un valore configurabile lato V2.

Questo DL non impone ancora:

- editor completo del catalogo famiglie
- bulk update massiva
- regole automatiche di assegnazione

Definisce solo che:

- esiste un catalogo interno
- un articolo puo essere associato a una famiglia
- la UI `articoli` potra mostrare e successivamente modificare questa classificazione

## 7. Migrazione incrementale

La V2 puo introdurre la famiglia articolo in modo incrementale:

1. creare catalogo famiglie
2. aggiungere il riferimento agli articoli Core
3. esporre la famiglia nel contratto Core/API
4. introdurre la UI di visualizzazione e poi di modifica

Regola:

- il primo slice puo limitarsi a persistenza e contratto backend, rinviando raffinamenti UI successivi

## 8. Confini intenzionali

Questo DL NON definisce:

- ulteriori entita interne articolo oltre alla famiglia
- regole di pricing
- logiche di distinta base
- relazioni complesse tra famiglia e produzione
- automazioni di assegnazione basate su campi Easy

## Consequences

### Positive

- introduce il primo dato interno reale nel dominio `articoli`
- mantiene chiaro il confine tra dati Easy e classificazione interna
- crea una base stabile per configurazioni future di produzione

### Negative / Trade-off

- il Core `articoli` non e piu solo proiezione del mirror
- introduce persistenza interna aggiuntiva e una prima scelta tassonomica da governare
- alcune famiglie potrebbero essere ridefinite nel tempo

## Impatto sul progetto

Questo DL diventa riferimento per:

- il primo task di configurazione interna `articoli`
- l'evoluzione del Core `articoli`
- le future UI di configurazione articoli

E prerequisito diretto per:

- task attuativo della famiglia articolo

## Notes

- Questo DL raffina `DL-ARCH-V2-013`: il Core `articoli` non e piu solo read-only, ma inizia ad accogliere dati interni strettamente necessari.
- La famiglia e la prima entita interna scelta perche introduce classificazione senza forzare ancora logiche di dominio piu profonde.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
- `docs/integrations/easy/EASY_ARTICOLI.md`
- `docs/task/TASK-V2-018-sync-articoli-reale.md`
- `docs/task/TASK-V2-019-core-articoli.md`
- `docs/task/TASK-V2-020-ui-articoli.md`
