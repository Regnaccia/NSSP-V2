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
