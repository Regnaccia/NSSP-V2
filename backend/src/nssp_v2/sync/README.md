# Sync Layer

Responsabilita:

- leggere dalle sorgenti esterne
- assorbire complessita tecniche della sorgente
- normalizzare e riallineare dati input verso il perimetro V2
- produrre run metadata e change detection utili al core

Non deve:

- prendere decisioni operative
- scrivere stati o policy del dominio
- dipendere da router o UI
