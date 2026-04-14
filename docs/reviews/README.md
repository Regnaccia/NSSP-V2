# V2 Reviews

Questa cartella raccoglie review critiche trasversali sullo stato del progetto.

Uso consigliato:

- fissare finding che non appartengono a un singolo task
- tenere separate review architetturali, operative e di rischio dagli indici di roadmap
- aggiornare o sostituire i memo quando lo stato del sistema cambia in modo sostanziale

Documenti attivi:

- `KNOWN_BUGS.md`
- `PROJECT_REVIEW_2026-04-08.md`
- `PROJECT_REVIEW_2026-04-10_ARCHITECTURAL.md`
- `PROJECT_REVIEW_2026-04-10_SYSTEMS_ENGINEERING.md`

Bug reports:

- `BUG-MAG-REALE-DELETE-HANDLING-2026-04-10.md` - movimenti eliminati in Easy restano nel mirror ODE -> giacenze errate (fix operativo `TASK-V2-073` gia eseguito; follow-up architetturale ancora aperto)
- `BUG-CORE-ARTICOLO-CONFIG-ORPHAN-2026-04-13.md` - alcuni `PATCH` articolo possono creare stato interno su codici inesistenti
- `BUG-REFRESH-ARTICOLI-INVENTORY-WITH-STALE-MAG-REALE-2026-04-13.md` - il refresh semantico puo ricostruire `inventory_positions` anche se `mag_reale` fallisce nel run corrente
