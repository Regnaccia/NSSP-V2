# App Layer

Responsabilita:

- esporre API HTTP e workflow applicativi
- validare input/output
- comporre projection e comandi verso il core
- gestire auth, dipendenze runtime e bootstrap FastAPI

Non deve:

- contenere regole di dominio sostanziali
- accedere a sorgenti esterne di sync
- duplicare calcoli gia presenti nel core
