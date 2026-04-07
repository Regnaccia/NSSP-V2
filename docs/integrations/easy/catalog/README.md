# Easy Catalog

Questa cartella contiene gli output machine-generated dello schema Easy in formato JSON.

Scopo:

- fotografare lo schema tecnico reale delle tabelle Easy
- evitare di copiare manualmente tutte le colonne nei documenti di mapping
- fornire una base stabile per decidere quali campi usare nel sync

Regole:

- i file del catalogo sono output tecnici, non documenti di business
- non sostituiscono i file `EASY_<ENTITY>.md`
- l'accesso a Easy resta sempre read-only
- il naming consigliato dei file e `<TABLE_NAME>.json`

Uso previsto:

1. estrazione schema tabella Easy in JSON
2. consultazione del JSON come riferimento completo
3. compilazione del mapping documentale solo con i campi realmente necessari
