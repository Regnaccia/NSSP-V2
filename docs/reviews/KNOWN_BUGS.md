# ODE V2 - Known Bugs

## Scopo

Questo file raccoglie bug e limiti noti che:

- hanno gia evidenza reale
- non appartengono solo a un singolo task
- richiedono memoria architetturale o operativa nel tempo

Uso consigliato:

- tenere qui il promemoria dei fix strutturali da non perdere
- linkare il bug report dettagliato quando esiste
- distinguere tra:
  - fix temporaneo operativo
  - fix architetturale di lungo termine

## Bug aperti

### 1. `sync_mag_reale` non rileva cancellazioni o rettifiche in Easy

Status:

- aperto

Sintesi:

- il mirror `sync_mag_reale` usa ancora:
  - `append_only`
  - `cursor`
  - `no_delete_handling`
- se Easy elimina o rettifica movimenti gia importati, il mirror ODE puo mantenere movimenti fantasma
- la conseguenza e una divergenza su:
  - `inventory_positions`
  - `availability`
  - UI `articoli`
  - `Planning Candidates`

Fix temporaneo disponibile:

- [TASK-V2-073-fix-mag-reale-rebootstrap.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/task/TASK-V2-073-fix-mag-reale-rebootstrap.md#L1)
  - re-bootstrap completo del mirror
  - rebuild della chain quantitativa
  - gia eseguito con riallineamento exact-match del dataset corrente

Fix architetturale ancora da aprire:

- nuovo `DL-ARCH` dedicato per ridefinire la strategia di sync di `MAG_REALE`
- direzioni possibili da valutare:
  - `full_replace`
  - `reconcile`
  - `append_only` + rebuild totale schedulato come strategia esplicita

Riferimenti:

- [BUG-MAG-REALE-DELETE-HANDLING-2026-04-10.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/BUG-MAG-REALE-DELETE-HANDLING-2026-04-10.md#L1)
- [TASK-V2-073-fix-mag-reale-rebootstrap.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/task/TASK-V2-073-fix-mag-reale-rebootstrap.md#L1)
- [EASY_MAG_REALE.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/integrations/easy/EASY_MAG_REALE.md#L1)

### 2. `core_articolo_config` puo contenere record orfani per articoli inesistenti

Status:

- aperto

Sintesi:

- alcuni endpoint `PATCH` della surface `produzione` possono scrivere su
  `core_articolo_config` senza verificare prima che l'articolo esista in `sync_articoli`
- il modello non ha FK hard verso `sync_articoli`
- in alcuni casi la API puo fare `commit` e poi rispondere `404`

Impatto:

- stato interno incoerente
- override fantasma su codici inesistenti
- debugging piu difficile delle configurazioni articolo

Direzione di fix:

- validazione esplicita esistenza articolo prima di ogni write
- `404` prima del `commit`
- test dedicati sui codici inesistenti

Riferimenti:

- [BUG-CORE-ARTICOLO-CONFIG-ORPHAN-2026-04-13.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/BUG-CORE-ARTICOLO-CONFIG-ORPHAN-2026-04-13.md#L1)

### 3. `refresh_articoli()` ricostruisce `inventory_positions` anche dopo failure di `mag_reale`

Status:

- aperto

Sintesi:

- lo step `inventory_positions` del refresh semantico viene eseguito sempre
- se `mag_reale` fallisce nel run corrente, il rebuild puo andare in `success`
  usando un mirror non aggiornato
- la response step-by-step diventa ambigua rispetto allo stato reale della chain quantitativa

Impatto:

- percezione di refresh riuscito su input stantio
- debugging piu difficile dei refresh parziali

Direzione di fix:

- saltare il rebuild inventory se `mag_reale` non e `success`
- oppure documentare e distinguere esplicitamente il caso "stale input"

Riferimenti:

- [BUG-REFRESH-ARTICOLI-INVENTORY-WITH-STALE-MAG-REALE-2026-04-13.md](/c:/Users/Alberto.REGNANI/Desktop/NSSP/NSSP/V2/docs/reviews/BUG-REFRESH-ARTICOLI-INVENTORY-WITH-STALE-MAG-REALE-2026-04-13.md#L1)
