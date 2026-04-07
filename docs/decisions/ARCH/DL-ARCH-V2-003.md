# DL-ARCH-V2-003 - Database interno V2 come persistence backbone

## Status
Approved

## Date
2026-04-07

## Context

La V2 ha gia un bootstrap backend minimo:

- progetto Python configurato
- FastAPI avviabile
- SQLAlchemy e Alembic inizializzati
- configurazione centralizzata presente

Manca pero ancora una decisione architetturale esplicita sul ruolo del database interno.

Questa decisione e necessaria prima di implementare:

- autenticazione browser reale
- tabella utenti e ruoli
- facts canonici
- computed facts persistiti
- stati operativi e aggregate

Senza un modello chiaro del DB interno, c'e il rischio di far nascere:

- tabelle introdotte solo per urgenza locale
- dipendenze premature da sorgenti esterne
- confusione tra dato tecnico, dato canonico e dato applicativo
- migrazioni scollegate dalla struttura architetturale V2

La V2 ha quindi bisogno di fissare in modo esplicito:

- che il DB interno esiste fin dall'inizio come parte strutturale del sistema
- cosa deve ospitare
- come si relaziona ai layer `sync`, `core`, `app`
- quale bootstrap minimo e richiesto prima dei task auth e dominio

## Decision

La V2 adotta un database interno PostgreSQL come persistence backbone unico del sistema.

Il database interno e obbligatorio sin dai primi slice implementativi.

### 1. Il database interno e il backbone persistente della V2

Tutto cio che il sistema V2 deve:

- ricostruire
- spiegare
- verificare
- far evolvere con migrazioni controllate

deve passare dal database interno.

Questo include:

- dati riallineati da sorgenti esterne
- dati nativi della V2
- strutture necessarie al funzionamento applicativo

### 2. Nessun layer di business legge direttamente dalle sorgenti esterne

Le sorgenti esterne, ad esempio EasyJob, non sono lette direttamente da `core` o `app`.

Regola:

- `sync` acquisisce e riallinea
- il risultato viene persistito nel DB interno
- `core` e `app` lavorano sul DB interno
- l'accesso a EasyJob e solo read-only; nessuna scrittura verso EasyJob e permessa da V2

Questo vale anche quando la sorgente esterna resta la fonte originaria del dato.

### 3. Un solo database, una sola schema PostgreSQL iniziale

La V2 parte con:

- un solo database PostgreSQL
- una sola schema PostgreSQL iniziale, `public`

La separazione tra responsabilita non viene implementata inizialmente tramite piu database o piu schema.

Viene invece mantenuta tramite:

- confini di layer nel codice
- ownership esplicita delle tabelle
- naming e migrazioni disciplinate

Motivazione:

- ridurre complessita prematura
- mantenere bootstrap e test locali semplici
- evitare che la separazione architetturale venga delegata a una separazione fisica ancora non necessaria

### 4. Il DB interno ospita famiglie di dati diverse

Nel DB interno V2 convivono famiglie di dati diverse:

- dati di accesso e supporto applicativo
- dati sync-owned derivati da sorgenti esterne
- dati core-owned del dominio V2
- dati tecnici di supporto, quando servono al runtime

Queste famiglie vanno distinte a livello concettuale anche se condividono lo stesso database.

### 5. Primo slice persistente obbligatorio: access control

Prima di implementare il login browser reale, il DB interno deve ospitare almeno il primo slice persistente di accesso:

- `users`
- `roles`
- `user_roles`

Il modello deve supportare:

- utente nominale
- piu ruoli per utente
- utente attivo o inattivo

Questo slice e considerato parte del backbone del sistema, non una scorciatoia temporanea.

### 6. Ogni cambio strutturale passa da Alembic

Ogni modifica strutturale del DB interno deve passare da:

- modelli SQLAlchemy coerenti
- migration Alembic esplicita

Non sono ammessi come standard di progetto:

- schema drift manuale
- creazione tabelle fuori migrazione
- bootstrap affidato solo a SQL lanciato a mano

### 7. Test e ambienti devono usare database dedicati

La V2 deve distinguere almeno:

- database locale di sviluppo
- database di test

Regola:

- i test non devono dipendere dal DB di sviluppo
- la configurazione ambiente deve rendere esplicita la URL DB usata

### 8. Il frontend non ha accesso diretto al DB

Il frontend browser, e in futuro Electron o kiosk, non accede mai direttamente al database.

L'accesso avviene solo tramite `app layer` e contratti HTTP espliciti.

### 9. Conseguenza immediata sul piano dei task

Prima del task auth browser reale, il progetto deve introdurre un task dedicato al bootstrap DB interno.

Ordine corretto:

1. bootstrap backend minimo
2. hardening verifica riproducibile
3. bootstrap DB interno
4. auth browser e routing per ruoli

## Consequences

### Positive

- il login utente nasce su una base persistente reale
- i task successivi possono aggiungere tabelle e migrazioni senza ambiguita
- il `core` non rischia di accoppiarsi direttamente a EasyJob
- la strategia di test resta coerente con il charter

### Negative / Trade-off

- serve introdurre il DB prima di mostrare valore applicativo visibile all'utente finale
- aumenta leggermente il lavoro iniziale di setup
- richiede disciplina immediata su migrazioni e ambienti

### Impatto sul progetto

Questo DL non introduce ancora il modello auth completo e non introduce ancora facts di dominio.

Pero fissa il prerequisito architetturale comune per:

- auth
- sync persistito
- facts canonici
- stati operativi

## Notes

- Il DB interno non sostituisce il ruolo delle sorgenti esterne, ma diventa il perimetro operativo unico della V2.
- La separazione per layer resta nel codice e nella ownership delle tabelle, non in una moltiplicazione precoce di schema PostgreSQL.
- Il task naturale successivo a questo DL e `TASK-V2-003` per il bootstrap DB interno.

## References

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `backend/src/nssp_v2/shared/db.py`
