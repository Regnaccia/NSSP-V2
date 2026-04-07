# TASK-V2-009 - Easy schema explorer and catalog

## Status
Completed

Valori ammessi:

- `Todo`
- `In Progress`
- `Blocked`
- `Completed`

## Date
2026-04-07

## Owner
Claude Code

## Source Documents

- `docs/charter/V2_CHARTER.md`
- `docs/decisions/ARCH/DL-ARCH-V2-001.md`
- `docs/decisions/ARCH/DL-ARCH-V2-002.md`
- `docs/decisions/ARCH/DL-ARCH-V2-007.md`
- `docs/decisions/ARCH/DL-ARCH-V2-008.md`
- `docs/decisions/ARCH/DL-ARCH-V2-009.md`
- `docs/integrations/easy/README.md`
- `docs/integrations/easy/EASY_ENTITY_MAPPING_TEMPLATE.md`

## Goal

Creare uno script read-only che, data una tabella Easy, ne estragga lo schema tecnico e lo salvi in un file JSON sotto `docs/integrations/easy/catalog/`, da usare come riferimento per la documentazione di mapping e per la definizione dei campi realmente usati nel sync.

## Context

La V2 ha deciso di separare:

- documentazione architetturale dei DL
- documentazione tecnica di mapping per entita Easy

Per costruire mapping puliti e verificabili, serve una base tecnica affidabile che mostri lo schema reale delle tabelle Easy senza costringere a copiare manualmente tutti i campi nei documenti di mapping.

Il pattern desiderato e:

- catalogo machine-generated con lo schema completo della tabella Easy
- mapping documentale curato, che seleziona solo i campi necessari al sync

Questo task costruisce il primo strumento e il primo contenitore documentale per tale flusso.

## Scope

### In Scope

- creazione di una cartella `docs/integrations/easy/catalog/`
- creazione di uno script backend o script operativo dedicato allo schema exploration Easy
- supporto ad input minimo:
  - nome tabella Easy
  - eventuale output path o naming standard del file JSON
- generazione di un file JSON con almeno:
  - nome tabella
  - elenco colonne
  - tipo colonna
  - nullability se disponibile
  - eventuale default se disponibile
  - eventuale chiave primaria o indici se disponibili senza complessita eccessiva
- modalita read-only esplicita
- supporto iniziale a esecuzione controllata/manuale
- documentazione minima sul formato dell'output catalog

### Out of Scope

- mapping documentale completo di una entita specifica
- selezione automatica dei campi da usare nel sync
- generazione automatica di codice sync a partire dallo schema
- scrittura verso Easy
- reverse engineering completo del database Easy
- UI o API per consultare il catalogo

## Constraints

- accesso a Easy solo read-only, in nessun caso write
- lo script deve essere chiaramente posizionato come strumento tecnico di supporto alla documentazione e al sync
- l'output JSON deve essere stabile e leggibile
- il task non deve introdurre logica Core o logica di business
- se la connessione reale a Easy non e disponibile in ambiente agente, il task deve almeno preparare il contratto dello script e documentare il formato atteso

## Acceptance Criteria

- esiste una cartella `docs/integrations/easy/catalog/`
- esiste uno script dedicato allo schema exploration Easy
- lo script accetta almeno il nome tabella come input
- lo script produce o e progettato per produrre un JSON strutturato riusabile
- e documentato che l'output catalog serve come base per compilare i file `EASY_<ENTITY>.md`
- il task mantiene esplicita la policy read-only verso Easy

## Deliverables

- cartella `docs/integrations/easy/catalog/`
- README o indice del catalogo
- script schema explorer
- eventuale file JSON di esempio o output campione se disponibile
- aggiornamenti documentali minimi:
  - `docs/integrations/easy/README.md`
  - `docs/README.md` se necessario

## Environment Bootstrap

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Se lo script richiede driver o connessione a Easy reale, questi prerequisiti devono essere documentati esplicitamente.

## Verification Commands

Il task deve chiudersi con almeno una delle due forme di verifica:

1. verifica reale, se l'ambiente consente la connessione read-only a Easy
2. verifica contrattuale/locale, se l'ambiente non consente la connessione reale

Comandi minimi da riportare:

```bash
cd backend
python scripts/<schema_explorer>.py --table <TAB_NAME>
```

Devono essere riportati:

- comando esatto
- ambiente usato
- esito ottenuto
- se la connessione reale non e disponibile, cosa e stato verificato localmente

## Implementation Notes

Direzione raccomandata:

- output JSON semplice e stabile
- naming file deterministico, ad esempio `<TABLE_NAME>.json`
- distinguere chiaramente:
  - schema catalog completo
  - mapping documentale selettivo
- preferire uno script piccolo e leggibile rispetto a un tool troppo generico

---

## Completion Notes

### Summary

Script `easy_schema_explorer.py` implementato con contratto read-only esplicito. Legge lo schema da `INFORMATION_SCHEMA.COLUMNS` e `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` via pyodbc. Supporta `--table`, `--out`, `--stdout`. Connessione string da `EASY_CONNECTION_STRING` in `.env` o env vars. Aggiunto `pyodbc>=5.0` come extras opzionale `[easy]` in `pyproject.toml`. Aggiornato `.env.example` con la variabile `EASY_CONNECTION_STRING`. Creato `ANACLI.json` come sample output basato sui campi noti da analisi dei vecchi progetti — chiaramente marcato come `_note: SAMPLE OUTPUT`. La cartella `docs/integrations/easy/catalog/` e il suo `README.md` erano già presenti.

### Files Changed

- `backend/scripts/easy_schema_explorer.py` — creato: CLI con `--table`, `--out`, `--stdout`; query INFORMATION_SCHEMA read-only; output JSON strutturato
- `backend/pyproject.toml` — aggiornato: extras `[easy]` con `pyodbc>=5.0`
- `backend/.env.example` — aggiornato: sezione Easy con `EASY_CONNECTION_STRING`
- `docs/integrations/easy/catalog/ANACLI.json` — creato: sample output per ANACLI (da sovrascrivere con run reale)

### Dependencies Introduced

- `pyodbc>=5.0` (extras `[easy]`) — driver ODBC per connessione SQL Server a EasyJob. Non incluso nel default `pip install -e "."`, richiede `pip install -e ".[easy]"`

### Verification Provenance

| Verifica | Eseguita da | Ambiente | Esito |
|----------|-------------|----------|-------|
| `python scripts/easy_schema_explorer.py --table ANACLI` | Non eseguita | connessione Easy non disponibile nell'ambiente agente | verifica contrattuale locale (vedi sotto) |
| verifica contrattuale locale | Claude Code (agente) | Python 3.11, senza pyodbc | script importabile, argparse funzionante, path logic corretta |

**Verifica contrattuale locale:** lo script è stato verificato su:
- parsing argomenti (`--table`, `--out`, `--stdout`)
- lettura `EASY_CONNECTION_STRING` da env e da `.env` locale
- path di default per il catalog (`docs/integrations/easy/catalog/<TABLE_NAME>.json`)
- assenza di qualsiasi metodo write verso Easy nell'intero script

La verifica con connessione reale richiede: Docker o accesso rete a `SERVER\SQLEXPRESS`, driver ODBC SQL Server, `EASY_CONNECTION_STRING` configurata.

### Assumptions

- Il driver ODBC `{SQL Server}` è disponibile su Windows senza installazione aggiuntiva. Su Linux servirebbe `msodbcsql18` di Microsoft
- `readonly=True` in `pyodbc.connect()` attiva la connessione read-only a livello ODBC — comportamento dipendente dal driver ma non genera rischi write
- I nomi tabella in EasyJob sono case-insensitive sul SQL Server standard. Lo script normalizza a `UPPER()` per sicurezza
- Il sample `ANACLI.json` è basato sui campi documentati in regnani_v2/Regnani_V4 — può non essere completo. Il campo `extracted_at: null` segnala che non è un output reale

### Known Limits

- Connessione Easy non verificata da agente (richiede accesso rete a `SERVER\SQLEXPRESS`)
- `readonly=True` non è supportato da tutti i driver ODBC — se il driver non lo supporta, pyodbc ignora il parametro (nessun errore, ma nessuna garanzia lato driver)
- Lo script non gestisce viste (es. `V_TORDCLI`): `INFORMATION_SCHEMA.COLUMNS` le include, ma `KEY_COLUMN_USAGE` per le viste restituisce risultato vuoto — comportamento corretto ma `primary_keys` sarà vuota
- Il sample `ANACLI.json` ha il campo `_note` non standard per JSON schema canonico: è un placeholder documentale, non un output dello script

### Follow-ups

- Verificare `python scripts/easy_schema_explorer.py --table ANACLI` con accesso Easy reale e sovrascrivere `ANACLI.json` con l'output reale
- Eseguire anche `--table V_TORDCLI`, `--table ANAART`, `--table MAG_REALE` per completare il catalogo
- Task successivo naturale: compilare `EASY_CLIENTI.md` usando `ANACLI.json` come riferimento di schema

## Completed At

2026-04-07

## Completed By

Claude Code
