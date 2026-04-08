# V2 Implementation Patterns

## Scopo

Questa guida raccoglie i pattern emersi dai primi slice reali gia implementati nella V2.

Non sostituisce i `DL`, ma rende piu rapido progettare nuovi stream applicativi senza dover ricostruire ogni volta il percorso corretto.

## Pattern 1 - Vertical Slice esterno -> interno -> UI

Per entita che nascono da Easy o da altre sorgenti esterne, il percorso standard V2 e:

1. mapping tecnico della sorgente in `docs/integrations/...`
2. sync mirror read-only nel layer `sync`
3. Core slice che espone il contratto applicativo
4. UI che consuma solo il Core/API
5. sync on demand backend-controlled
6. dati interni introdotti solo quando emerge una logica reale

Applicazioni gia validate:

- `clienti`
- `destinazioni`
- `articoli`

Regola:

> La UI non legge mai direttamente i mirror sync.

## Pattern 2 - Mirror esterno + arricchimento interno

Quando una entita nasce da Easy:

- `sync_*` resta vicino alla sorgente e solo read-only
- il `core` aggiunge significato interno
- i dati interni non vengono mai rimandati nel mirror

Esempi:

- `nickname_destinazione`
- `famiglia articolo`

Regola:

> Easy fornisce dati sorgente; il Core aggiunge classificazione e configurazione interna.

## Pattern 3 - Dati interni solo quando servono

La V2 evita di modellare entita interne preventive.

Percorso corretto:

- prima read model quasi-proiettivo
- poi primo dato interno utile
- poi raffinamento progressivo

Questo approccio e gia emerso in:

- `DL-ARCH-V2-013` per il Core `articoli`
- `DL-ARCH-V2-014` per la prima entita interna `famiglia articolo`

Regola:

> Nessun dato interno viene introdotto "perche prima o poi servira".

## Pattern 4 - Sync on demand sempre backend-controlled

Il refresh manuale di una surface segue sempre lo stesso schema:

- la UI richiede
- il backend valida
- il backend esegue
- la UI riceve stato e freshness

La UI non puo:

- chiamare script direttamente
- parlare con Easy
- orchestrare dipendenze da sola

Pattern gia validato in:

- `logistica`
- `articoli`

## Pattern 5 - Pattern UIX prima, spec concreta dopo

Per la UI la struttura corretta e:

- `DL-UIX` per il pattern generale
- `UIX/specs/` per il caso concreto

Esempi:

- `DL-UIX-V2-002` = pattern multi-colonna
- `UIX_SPEC_CLIENTI_DESTINAZIONI` = variante a 3 colonne
- `UIX_SPEC_ARTICOLI` = variante a 2 colonne

Regola:

> I casi concreti non devono sporcare il pattern generale.

## Pattern 6 - Ricerca dominio-specifica normalizzata

Quando una ricerca ha convenzioni operative forti, la regola UX va resa esplicita e riusabile.

Esempio gia emerso:

- ricerca articoli con equivalenza `8.7.40` -> `8x7x40`

La logica vive:

- in un `DL-UIX` se la regola e stabile
- nella surface concreta se il comportamento e gia attivo

## Pattern 7 - Casi specifici documentati in mapping + task, non in nuovi DL architetturali

Per le sync per singola entita:

- il pattern generale vive nei `DL-ARCH-V2-007/008/009`
- il caso concreto vive in:
  - mapping doc
  - task attuativo

Esempi:

- `EASY_CLIENTI.md`
- `EASY_DESTINAZIONI.md`
- `EASY_ARTICOLI.md`

Regola:

> Un nuovo `DL-ARCH` per singola entita serve solo se introduce un pattern nuovo.

## Pattern 8 - Completion Notes come evidenza tecnica primaria

Per i task recenti, la verifica operativa vive soprattutto nelle `Completion Notes`.

Ogni task completo deve riportare almeno:

- file cambiati
- dipendenze introdotte
- comandi eseguiti
- esito delle verifiche
- assunzioni
- limiti noti
- follow-up

Questo riduce la necessita di aprire ogni volta un report `docs/test/` dedicato.

## Pattern 9 - Catalogo interno di riferimento + associazione a entita

Quando emerge un primo dato interno stabile, il pattern corretto non e quasi mai un campo libero sparso.

Percorso consigliato:

1. introdurre un catalogo interno dedicato
2. associare le entita di dominio a quel catalogo
3. esporre il catalogo in una UI dedicata
4. solo dopo introdurre attributi aggiuntivi del catalogo

Esempio gia validato:

- `famiglie articolo`
  - catalogo interno
  - associazione articolo -> famiglia
  - vista dedicata del catalogo
  - gestione create / active
  - flag `considera_in_produzione`

Regola:

> Se una classificazione interna ha vita propria, va trattata come catalogo di riferimento e non solo come enum nascosto nella UI.

## Pattern 10 - Mirror separati, aggregazione nel Core, computed fact con override

Quando una stessa entita logica arriva da sorgenti o bucket distinti, il pattern corretto e:

1. mantenere mirror sync separati
2. aggregare solo nel `core`
3. esporre nel `core` un `bucket` applicativo
4. introdurre computed fact nel `core`, non nel `sync`
5. gestire eventuali correzioni manuali come override interni

Primo caso emerso:

- `produzioni`
  - `sync_produzioni_attive`
  - `sync_produzioni_storiche`
  - `bucket = active | historical`
  - `stato_produzione`
  - `forza_completata`

Regola:

> Se la distinzione nasce dalla sorgente, i mirror restano separati; se la vista deve essere unificata, l'aggregazione e i computed fact nascono nel `core`.

## Pattern 11 - Append-only incrementale con rebuild deterministico a valle

Per sorgenti grandi che registrano eventi o movimenti e non aggiornano i record esistenti, il
pattern corretto e:

1. mirror `append_only` nel layer `sync`
2. cursor incrementale stabile
3. nessun calcolo business nel mirror
4. computed fact o rebuild deterministico nel `core`
5. rebuild completo periodico rimandato allo scheduler, non al bootstrap quotidiano

Primo caso validato:

- `MAG_REALE` -> `sync_mag_reale` -> `inventory_positions`

Evidenza iniziale:

- primo bootstrap reale completato con `337721` movimenti scritti
- durata circa `10m 15s`
- conferma pratica che il bootstrap completo e sostenibile e che i run successivi possono
  beneficiare del cursor incrementale

Regola:

> Se la sorgente e append-only, l'ottimizzazione giusta e sincronizzare i nuovi eventi e
> ricostruire a valle i fact canonici, non comprimere la logica direttamente nel mirror.

## Quando riusare questi pattern

Questi pattern vanno riusati soprattutto per:

- nuovi stream da sorgenti Easy
- nuove anagrafiche configurabili
- nuove surface browser per configurazione
- nuovi dati interni che arricchiscono mirror gia esistenti

## Quando NON riusarli alla cieca

Non vanno applicati in modo automatico se:

- serve un dominio puramente interno e non derivato da Easy
- la UI richiede un'interazione completamente diversa dal pattern configurazione
- il dato non e un mirror + arricchimento ma una vera aggregate root interna

## References

- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/decisions/ARCH/DL-ARCH-V2-011.md`
- `docs/decisions/ARCH/DL-ARCH-V2-013.md`
- `docs/decisions/ARCH/DL-ARCH-V2-014.md`
- `docs/decisions/ARCH/DL-ARCH-V2-015.md`
- `docs/decisions/UIX/DL-UIX-V2-002.md`
- `docs/decisions/UIX/DL-UIX-V2-004.md`
- `docs/decisions/UIX/specs/UIX_SPEC_CLIENTI_DESTINAZIONI.md`
- `docs/decisions/UIX/specs/UIX_SPEC_ARTICOLI.md`
