# TEST-V2-003 - Verifica TASK-V2-004 browser auth e routing iniziale

## Date
2026-04-07

## Scope

Verifica del task:

- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`

Obiettivo della verifica:

- controllare se il task auth browser e stato seguito fedelmente
- verificare login, sessione e payload `available_surfaces`
- verificare la build frontend e la consistenza del primo slice browser

## Sources Checked

- `docs/task/TASK-V2-004-browser-auth-and-role-routing.md`
- `docs/decisions/ARCH/DL-ARCH-V2-004.md`
- `docs/decisions/ARCH/DL-ARCH-V2-005.md`
- `backend/src/nssp_v2/app/api/auth.py`
- `backend/src/nssp_v2/app/deps/auth.py`
- `backend/src/nssp_v2/app/schemas/auth.py`
- `backend/src/nssp_v2/shared/security.py`
- `backend/scripts/seed_initial.py`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/app/authStore.ts`
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/SurfaceChooser.tsx`

## Verification Summary

Esito complessivo: `Pass`

Motivo:

- login browser e lettura sessione risultano funzionanti su DB seedato
- il payload di sessione espone `roles[]`, `access_mode`, `available_surfaces`
- la build frontend di produzione passa
- la suite unit backend passa integralmente

Nota residua:

- la verifica runtime backend richiede ancora env vars sane; un ambiente locale sporco puo rompere il bootstrap dei settings

## Fidelity Check

### Requisiti rispettati

- endpoint `POST /api/auth/login` presente e funzionante
- endpoint `GET /api/auth/me` presente e funzionante
- payload sessione con `roles[]`, `access_mode`, `available_surfaces`: presente
- supporto a `surface chooser` documentato e implementato lato frontend
- placeholder surfaces presenti per `admin`, `produzione`, `logistica`, `magazzino`
- hashing password reale introdotto con `bcrypt`
- test unit backend presenti e passanti

### Deviazioni o limiti osservati

- la verifica end-to-end richiede DB attivo e seed applicato
- il frontend non e stato verificato tramite browser manuale in questa sessione; e stata verificata la build

## Runtime Verification Performed

Comandi e controlli eseguiti:

- `pytest tests/unit/ -v`
- `npm run build`
- login applicativo tramite `fastapi.testclient.TestClient`
- richiesta autenticata a `GET /api/auth/me`

Risultati:

- test unit backend: `19 passed`
- build frontend: completata con successo
- `POST /api/auth/login`: `200`
- `GET /api/auth/me`: `200`

Payload osservato:

- `roles: ["admin"]`
- `access_mode: "browser"`
- `available_surfaces: [{"role": "admin", "path": "/admin", "label": "Admin"}]`

## Architecture Check

Allineamento con `DL-ARCH-V2-004` e `DL-ARCH-V2-005`:

- identita, ruoli e canale di accesso distinti: si
- `roles[]` come insieme, non ruolo singolo: si
- `available_surfaces` come output backend verso frontend: si
- routing iniziale impostabile su surface, non su pagina hardcoded: si

Non sono emerse violazioni architetturali evidenti nel perimetro del task.

## Risks And Notes

- il layer settings resta accoppiato a configurazioni ambiente locali; la verifica ha richiesto env vars esplicite
- manca ancora un test di integrazione backend dedicato al flusso auth con fixture DB separata
- la build frontend e verificata, ma non sostituisce una sessione browser manuale completa

## Final Verdict

`TASK-V2-004` puo essere considerato verificato in modo sostanziale sul piano backend, contratto di sessione e build frontend.

La documentazione e ora sufficientemente stabile per procedere alla definizione di `TASK-V2-005` sulla surface `admin`.
