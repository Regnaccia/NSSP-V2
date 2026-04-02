# V2 Backend Tests

Struttura prevista:

- `unit/` logica pura del core
- `integration/` DB reale, API e rebuild
- `contracts/` contratti espliciti tra layer e DTO
- `sync/` adapter, normalizzazione e casi di riallineamento

Regola:

- i test `core` devono poter girare senza EasyJob online
- i test `sync` non devono diventare prerequisito per validare il core
