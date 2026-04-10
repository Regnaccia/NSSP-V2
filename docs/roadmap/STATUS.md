# ODE V2 - Stato Progetto

## Date
2026-04-10

## Stato generale

La V2 ha completato il bootstrap architetturale principale e ha chiuso quattro stream applicativi minimi:

- `logistica`
- `produzione/articoli`
- `produzioni`
- `criticita articoli`

Sono oggi disponibili:

- backend base, auth browser e surface `admin`
- sync reale Easy read-only per `clienti` e `destinazioni`
- Core slice `clienti + destinazioni`
- UI browser clienti/destinazioni
- sync on demand backend-controlled per la surface logistica
- sync reale Easy read-only per `articoli`
- Core `articoli`
- UI browser `articoli`
- sync on demand backend-controlled per `articoli`
- catalogo interno `famiglie articolo`
- associazione articolo -> famiglia
- filtro famiglia nella lista articoli
- vista dedicata al catalogo `famiglie articolo`
- gestione minima del catalogo famiglie
- flag `considera_in_produzione` nel catalogo famiglie
- sync reale Easy read-only per `produzioni_attive` e `produzioni_storiche`
- Core `produzioni` con `bucket`, `stato_produzione` e `forza_completata`
- UI browser `produzioni` consultiva a `2 colonne`
- sync on demand backend-controlled per `produzioni`
- prima gestione operativa del flag `forza_completata`
- default lista `produzioni` su `active`, con storico esplicito
- filtri `stato_produzione` e ricerca per articolo/documento
- sync reale Easy read-only per `MAG_REALE`
- computed fact canonica `inventory_positions`
- giacenza esposta nel dettaglio UI `articoli`
- computed fact canonica `commitments` da provenienza `customer_order`
- estensione `commitments` alla provenienza `production` per materiali `CAT_ART1 != 0`
- computed fact canonico `customer_set_aside` da `DOC_QTAP`
- `customer_set_aside` esposto nel dettaglio UI `articoli` come campo read-only ODE
- `sync_righe_ordine_cliente` come mirror operativo attivo (`delete_absent_keys`)
- computed fact canonico `availability` (inventory - set_aside - committed)
- fix applicato sul bug di `availability` dovuto a `article_code` incoerente tra fact canonici, tramite helper condivisa `normalize_article_code`
- `committed_qty` e `availability_qty` esposti nel dettaglio UI `articoli` come campi read-only ODE
- refresh semantici backend: `refresh_articoli()` in `app/services/refresh_articoli.py`, router thin, chain incapsulata
- prima surface operativa `criticita articoli`
- toggle del perimetro `considera_in_produzione` nella vista `criticita`
- refresh della vista `criticita` agganciato al refresh semantico completo della surface `articoli`
- hardening delle join cross-source della vista `criticita` sulla chiave articolo canonica
- perimetro `criticita` ristretto ai soli articoli presenti e attivi nella surface `articoli`

## Decision log attivi

Famiglie attive:

- `ARCH/` fino a `DL-ARCH-V2-024`
- `UIX/` fino a `DL-UIX-V2-004`

Supporti attivi:

- `UIX/specs/` per i casi concreti che istanziano i pattern UIX

Punti ormai stabili:

- separazione `sync / core / app / shared`
- Easy solo read-only
- sync per entita con run metadata e freshness anchor
- Core come ponte tra mirror sync e surface applicative
- navigazione multi-surface con evoluzione verso navigazione contestuale

## Task completati

Completati:

- `TASK-V2-001` -> `TASK-V2-060`

In particolare il primo caso applicativo oggi copre:

- `TASK-V2-010` sync clienti reale
- `TASK-V2-011` sync destinazioni reale
- `TASK-V2-012` Core clienti/destinazioni
- `TASK-V2-013` UI clienti/destinazioni
- `TASK-V2-014` sync on demand backend-controlled
- `TASK-V2-015` integrazione della destinazione principale derivata
- `TASK-V2-016` refinement scroll indipendente delle colonne
- `TASK-V2-017` navigazione contestuale per-surface
- `TASK-V2-018` sync articoli reale
- `TASK-V2-019` Core articoli
- `TASK-V2-020` UI articoli
- `TASK-V2-021` sync on demand articoli
- `TASK-V2-022` famiglia articoli
- `TASK-V2-023` UI famiglia articoli
- `TASK-V2-024` filtro famiglia articoli
- `TASK-V2-025` UI tabella famiglia articoli
- `TASK-V2-026` gestione famiglie articoli
- `TASK-V2-027` flag considera in produzione famiglie
- `TASK-V2-028` sync produzioni attive
- `TASK-V2-029` sync produzioni storiche
- `TASK-V2-030` Core produzioni
- `TASK-V2-031` UI produzioni
- `TASK-V2-032` sync on demand produzioni
- `TASK-V2-033` gestione operativa `forza_completata`
- `TASK-V2-034` performance produzioni con default `active`
- `TASK-V2-035` filtri e ricerca produzioni
- `TASK-V2-036` sync `MAG_REALE`
- `TASK-V2-037` computed fact `inventory_positions`
- `TASK-V2-038` giacenza nel dettaglio `articoli`
- `TASK-V2-039` refresh sequenziale `articoli -> mag_reale -> inventory_positions`
- `TASK-V2-040` sync `righe_ordine_cliente`
- `TASK-V2-041` Core `ordini cliente`
- `TASK-V2-042` `commitments` cliente
- `TASK-V2-043` `commitments` produzione
- `TASK-V2-044` computed fact `customer_set_aside` da `DOC_QTAP`
- `TASK-V2-045` `customer_set_aside` nel dettaglio UI `articoli`
- `TASK-V2-046` refresh sequenziale esteso a `customer_set_aside`
- `TASK-V2-047` refresh corretto con `sync_righe_ordine_cliente` a monte del rebuild
- `TASK-V2-048` allineamento operativo `sync_righe_ordine_cliente` — `delete_absent_keys`
- `TASK-V2-049` Core `availability`
- `TASK-V2-050` `committed_qty` e `availability_qty` nel dettaglio UI `articoli`
- `TASK-V2-051` refresh sequenziale `articoli` esteso a `availability`
- `TASK-V2-052` hardening normalizzazione `article_code` cross-source
- `TASK-V2-053` refresh `articoli` esteso a `sync_produzioni_attive` + `rebuild_commitments`
- `TASK-V2-054` refresh semantici backend con `refresh_articoli()`
- `TASK-V2-055` prima vista operativa minima `criticita articoli`
- `TASK-V2-056` refinement UI `criticita`: perimetro `considera_in_produzione`, filtro famiglia e ordinamenti
- `TASK-V2-057` toggle del perimetro `considera_in_produzione` con default attivo e disattivazione per debug
- `TASK-V2-058` pulsante `Aggiorna` della vista `criticita` collegato al refresh semantico `refresh_articoli()`
- `TASK-V2-059` hardening join raw/canonical nel slice `criticita`
- `TASK-V2-060` perimetro `criticita` ristretto ai soli articoli presenti e attivi in `articoli`

## Task aperti

- `TASK-V2-061` separare nella vista `articoli` la ricerca per codice dalla ricerca per descrizione

## Gap noti

- la documentazione `UIX` e separata tra pattern generale e spec caso concreto; i prossimi casi dovranno aggiungere nuove spec dedicate
- il catalogo `famiglie articolo` e ormai un vero riferimento interno; i prossimi stream dovranno decidere se riusare lo stesso pattern anche per altri cataloghi di dominio
- i report `docs/test/` coprono formalmente solo i primi test storici; per i task piu recenti la verifica vive nelle `Completion Notes`
- manca uno script `rebuild_commitments.py` on-demand (analogo a `rebuild_inventory_positions.py` e `rebuild_availability.py`)

## Prossima sequenza consigliata

Il perimetro V1 del modello quantitativo e ora completamente chiuso e operativo:

- `inventory`, `commitments`, `customer_set_aside`, `availability`
- tutti e quattro i fact esposti nel dettaglio `articoli`
- refresh semantico completo della surface `articoli` in un unico trigger (8 step)
- normalizzazione `article_code` canonica cross-source
- router thin: la chain non e piu replicata negli endpoint
- prima vista operativa `criticita articoli` gia coerente con la surface `articoli`

I prossimi stream naturali riguardano:

- refinement UX della ricerca `articoli`: campo `codice` con normalizzazione dimensionale e campo `descrizione` testuale separato
- evoluzione futura della surface `criticita articoli` verso logiche piu ricche: famiglie, scorte, policy di aggregazione e slice temporali
- scheduler automatico dei refresh
- `rebuild_commitments.py` script on-demand mancante

## Notes

- Questo documento e uno snapshot di stato, non sostituisce task, DL o report di test.
- Va aggiornato quando cambia in modo sostanziale il perimetro completato del progetto.
