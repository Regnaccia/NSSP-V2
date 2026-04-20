# TASK-V2-135 - UI Warnings come root navigation

## Status
Completed

## Date
2026-04-17

## Owner
Codex

## Source Documents

- `docs/SYSTEM_OVERVIEW.md`
- `docs/guides/UI_SURFACES_OVERVIEW.md`
- `docs/specs/WARNINGS_SPEC_V1.md`

## Goal

Spostare la surface `Warnings` fuori dal ramo `Produzione` e trattarla come modulo root di navigazione, allo stesso livello di aree come:

- `Produzione`
- `Magazzino`
- `Admin`

La surface deve continuare a filtrare i warning in base ai permessi/area utente come gia avviene oggi.

Nel medesimo refinement UI, la tabella `Warnings` va resa meno aderente al solo warning `NEGATIVE_STOCK`:

- introdurre filtro per `warning type`
- rimuovere le colonne troppo specifiche:
  - `giacenza`
  - `anomalia`
- introdurre al loro posto una colonna generale:
  - `reason`

## Context

`Warnings` non e piu solo una sotto-vista della produzione: e un modulo trasversale che aggrega anomalie canoniche cross-domain.

Il posizionamento attuale sotto `Produzione` comunica un perimetro troppo stretto rispetto al suo ruolo reale.

L'obiettivo di questo task e riallineare la navigazione alla semantica del modulo, senza cambiare il modello autorizzativo:

- `admin` mantiene la vista trasversale
- gli utenti operativi continuano a vedere solo i warning coerenti con la propria area

## Scope

- spostare `Warnings` nel navigation tree root
- rimuovere `Warnings` dal sottoalbero `Produzione`
- mantenere invariata la surface `Warnings`
- mantenere invariata la logica di filtro per area / permessi
- riallineare breadcrumb, label e routing UI dove necessario
- introdurre filtro UI per tipo warning
- ristrutturare la tabella warning:
  - rimuovendo colonne troppo specifiche per `NEGATIVE_STOCK`
  - introducendo una colonna `reason` generale

## Out of Scope

- redesign dei contenuti della pagina `Warnings`
- nuovi tipi warning
- modifica della logica Core warning visibility
- revisione dei ruoli / permessi utente
- redesign del payload Core warning oltre al minimo necessario per esporre `reason`

## Constraints

Regole:

- `Warnings` deve risultare modulo root, non sotto-voce `Produzione`
- il filtro per area corrente resta attivo come oggi
- il nuovo filtro per tipo warning e aggiuntivo, non sostitutivo del filtro per area
- `admin` continua a vedere la lista trasversale completa
- nessun cambio ai contratti backend warning e `visible_to_areas`
- la tabella non deve assumere che tutti i warning abbiano metriche tipo `giacenza` / `anomalia`
- `reason` deve diventare la colonna sintetica generale per spiegare il warning

## Pattern Checklist

Riferimento predefinito:

- `docs/guides/IMPLEMENTATION_PATTERNS.md`

Checklist minima:

- `Richiede mapping o chiarimento sorgente esterna?` No
- `Introduce o modifica mirror sync_*?` No
- `Introduce o modifica computed fact / read model / effective_* nel core?` No
- `Introduce configurazione interna governata da admin?` No
- `Introduce configurazione che deve essere visibile in articoli?` No
- `Introduce override articolo o default famiglia?` No
- `Richiede warnings dedicati o impatta warning esistenti?` No
- `Richiede refresh semantico backend o modifica una chain di refresh esistente?` No
- `Introduce impatti UI separabili dal core tramite filtro/tab invece che duplicazione entita?` Si
- `Introduce orizzonti temporali o logiche driver-specifiche da tenere separate?` No
- `Richiede aggiornamenti a spec / DL / guide oltre al task?` Si

## Pattern References

- `Pattern 09 - Una surface per dominio, non per query locale`

## Refresh / Sync Behavior

- `Nessun refresh semantico nuovo`

La modifica e solo di navigazione e posizionamento UI.

## Acceptance Criteria

- `Warnings` appare nella root navigation
- `Warnings` non appare piu sotto `Produzione`
- breadcrumb e routing restano coerenti
- la pagina continua a filtrare i warning per area/permessi come oggi
- `admin` continua a vedere la lista trasversale completa
- esiste un filtro UI per `warning type`
- la tabella non espone piu colonne `giacenza` e `anomalia`
- la tabella espone una colonna `reason` generale
- la surface resta leggibile anche con warning diversi da `NEGATIVE_STOCK`

## Deliverables

- refinement UI navigation per `Warnings`
- eventuali update minimi di route config / sidebar config
- update docs correlate se necessarie

## Verification Level

- `Mirata`

## Environment Bootstrap

```bash
cd frontend
npm install
```

## Verification Commands

```bash
cd frontend
npm run build
```

Atteso: exit code `0`.

## Implementation Log

### `shared/security.py`

Aggiunto `_OPERATIONAL_ROLES` e modificato `get_available_surfaces`:
- Per qualsiasi utente con almeno un ruolo operativo (admin/produzione/magazzino/logistica),
  viene iniettata una surface virtuale `{ role: "warnings", path: "/warnings", label: "Avvertimenti" }`
- Non richiede un nuovo ruolo utente — è una surface cross-role trasparente

### `frontend/src/App.tsx`

- Rimossa route `/produzione/warnings`
- Aggiunta route `/warnings` con `ProtectedRoute roles={['admin', 'produzione', 'magazzino', 'logistica']}`

### `frontend/src/components/AppShell.tsx`

- Rimossa voce `Avvertimenti` da `SURFACE_FUNCTIONS.produzione`
- Aggiunta entry `warnings: []` (surface root senza sub-funzioni)
- La surface appare nella sidebar primaria tramite `available_surfaces` (dal backend)

### `frontend/src/pages/surfaces/WarningsPage.tsx`

Refactor tabella:
- **Rimosse**: colonne `Giacenza` (`stock_calculated`) e `Anomalia` (`anomaly_qty`) — troppo specifiche per NEGATIVE_STOCK
- **Aggiunta**: colonna `Reason` che mostra `message` (campo generale valido per tutti i tipi)
- **Aggiunta**: colonna `Entità` che mostra `entity_key` (più generale di `article_code`)
- **Aggiunto**: filtro tipo warning in header — bottoni pill generati dinamicamente dai tipi presenti (derivati dalla lista live, non hardcoded)
- Aggiornato commento JSDoc (da "Surface Produzione" a "Surface Avvertimenti — root navigation")

**Esito build:** `✓ built in 7.42s`, exit code `0`.
