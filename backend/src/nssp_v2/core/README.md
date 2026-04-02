# Core Layer

Centro semantico della V2.

Responsabilita:

- costruire source facts canonici
- costruire computed facts riusabili
- gestire aggregate, stati operativi, policy e decision trace
- orchestrare rebuild completi o mirati in modo deterministico

Non deve:

- conoscere FastAPI, router o dettagli HTTP
- conoscere dettagli tecnici di EasyJob o di altre sorgenti esterne
