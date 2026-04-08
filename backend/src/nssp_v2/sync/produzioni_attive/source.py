"""
Source adapter per l'entita `produzioni_attive`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/DPRE_PROD) non deve mai essere modificata dalla sync.

Adapter disponibili:
- ProduzioneAttivaSourceAdapter: ABC — interfaccia obbligatoria
- EasyProduzioneAttivaSource:    adapter read-only verso DPRE_PROD (EasyJob SQL Server)
- FakeProduzioneAttivaSource:    implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_PRODUZIONI.md:
  ID_DETTAGLIO    -> id_dettaglio                          (source identity)
  CLI_RAG1        -> cliente_ragione_sociale               (nullable)
  ART_COD         -> codice_articolo                       (nullable)
  ART_DESCR       -> descrizione_articolo                  (nullable)
  ART_DES2        -> descrizione_articolo_2                (nullable)
  NR_RIGA         -> numero_riga_documento                 (nullable)
  DOC_QTOR        -> quantita_ordinata                     (nullable)
  DOC_QTEV        -> quantita_prodotta                     (nullable)
  MAT_COD         -> materiale_partenza_codice             (nullable)
  MM_PEZZO        -> materiale_partenza_per_pezzo          (nullable)
  ART_MISURA      -> misura_articolo                       (nullable)
  DOC_NUM         -> numero_documento                      (nullable)
  COD_IMM         -> codice_immagine                       (nullable)
  NUM_ORDINE      -> riferimento_numero_ordine_cliente     (nullable)
  RIGA_ORDINE     -> riferimento_riga_ordine_cliente       (nullable)
  NOTE_ARTICOLO   -> note_articolo                         (nullable)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProduzioneAttivaRecord:
    """Record di una produzione attiva proveniente da DPRE_PROD.

    Tutti i campi riflettono la sorgente Easy senza arricchimento business.
    I campi nullable vengono passati come None se assenti in sorgente.

    Mapping da EASY_PRODUZIONI.md:
    - id_dettaglio:                          ID_DETTAGLIO — source identity key
    - cliente_ragione_sociale:               CLI_RAG1 (nullable)
    - codice_articolo:                       ART_COD (nullable)
    - descrizione_articolo:                  ART_DESCR (nullable)
    - descrizione_articolo_2:                ART_DES2 (nullable)
    - numero_riga_documento:                 NR_RIGA (nullable)
    - quantita_ordinata:                     DOC_QTOR (nullable)
    - quantita_prodotta:                     DOC_QTEV (nullable)
    - materiale_partenza_codice:             MAT_COD (nullable)
    - materiale_partenza_per_pezzo:          MM_PEZZO (nullable)
    - misura_articolo:                       ART_MISURA (nullable)
    - numero_documento:                      DOC_NUM (nullable)
    - codice_immagine:                       COD_IMM (nullable)
    - riferimento_numero_ordine_cliente:     NUM_ORDINE (nullable)
    - riferimento_riga_ordine_cliente:       RIGA_ORDINE (nullable)
    - note_articolo:                         NOTE_ARTICOLO (nullable)
    """

    id_dettaglio: int
    cliente_ragione_sociale: str | None = None
    codice_articolo: str | None = None
    descrizione_articolo: str | None = None
    descrizione_articolo_2: str | None = None
    numero_riga_documento: int | None = None
    quantita_ordinata: Decimal | None = None
    quantita_prodotta: Decimal | None = None
    materiale_partenza_codice: str | None = None
    materiale_partenza_per_pezzo: Decimal | None = None
    misura_articolo: str | None = None
    numero_documento: str | None = None
    codice_immagine: str | None = None
    riferimento_numero_ordine_cliente: str | None = None
    riferimento_riga_ordine_cliente: Decimal | None = None
    note_articolo: str | None = None


class ProduzioneAttivaSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `produzioni_attive`.

    Ogni implementazione concreta deve:
    - leggere solo dalla sorgente esterna
    - non scrivere mai verso la sorgente

    Regola: nessun metodo write e permesso in questa interfaccia (DL-ARCH-V2-007 §2).
    """

    @abstractmethod
    def fetch_all(self) -> list[ProduzioneAttivaRecord]:
        """Restituisce tutte le produzioni attive dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    """Trim tecnico: stringa vuota o solo spazi → None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyProduzioneAttivaSource(ProduzioneAttivaSourceAdapter):
    """Adapter read-only per DPRE_PROD (EasyJob SQL Server).

    Legge i campi selezionati in EASY_PRODUZIONI.md tramite pyodbc.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

    # Query read-only — solo i campi del mapping EASY_PRODUZIONI.md
    _QUERY = """
        SELECT
            ID_DETTAGLIO,
            CLI_RAG1,
            ART_COD,
            ART_DESCR,
            ART_DES2,
            NR_RIGA,
            DOC_QTOR,
            DOC_QTEV,
            MAT_COD,
            MM_PEZZO,
            ART_MISURA,
            DOC_NUM,
            COD_IMM,
            NUM_ORDINE,
            RIGA_ORDINE,
            NOTE_ARTICOLO
        FROM DPRE_PROD
    """

    def __init__(self, connection_string: str) -> None:
        """
        Args:
            connection_string: pyodbc connection string per Easy SQL Server.
                               Formato: DRIVER={SQL Server};SERVER=...;DATABASE=ELFESQL;UID=...;PWD=...
        """
        self._connection_string = connection_string

    def fetch_all(self) -> list[ProduzioneAttivaRecord]:
        """Legge tutte le produzioni attive da DPRE_PROD. Read-only.

        Non modifica nessun dato nella sorgente.
        Normalizzazioni tecniche consentite (EASY_PRODUZIONI.md §Technical Normalization):
        - trim spazi iniziali e finali
        - stringa vuota → None per i campi nullable
        - valori numerici mantenuti come Decimal senza arrotondamenti business
        """
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[ProduzioneAttivaRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                records.append(ProduzioneAttivaRecord(
                    id_dettaglio=int(row.ID_DETTAGLIO),
                    cliente_ragione_sociale=_strip_or_none(row.CLI_RAG1),
                    codice_articolo=_strip_or_none(row.ART_COD),
                    descrizione_articolo=_strip_or_none(row.ART_DESCR),
                    descrizione_articolo_2=_strip_or_none(row.ART_DES2),
                    numero_riga_documento=(
                        int(row.NR_RIGA) if row.NR_RIGA is not None else None
                    ),
                    quantita_ordinata=(
                        Decimal(str(row.DOC_QTOR)) if row.DOC_QTOR is not None else None
                    ),
                    quantita_prodotta=(
                        Decimal(str(row.DOC_QTEV)) if row.DOC_QTEV is not None else None
                    ),
                    materiale_partenza_codice=_strip_or_none(row.MAT_COD),
                    materiale_partenza_per_pezzo=(
                        Decimal(str(row.MM_PEZZO)) if row.MM_PEZZO is not None else None
                    ),
                    misura_articolo=_strip_or_none(row.ART_MISURA),
                    numero_documento=_strip_or_none(row.DOC_NUM),
                    codice_immagine=_strip_or_none(row.COD_IMM),
                    riferimento_numero_ordine_cliente=_strip_or_none(row.NUM_ORDINE),
                    riferimento_riga_ordine_cliente=(
                        Decimal(str(row.RIGA_ORDINE)) if row.RIGA_ORDINE is not None else None
                    ),
                    note_articolo=_strip_or_none(row.NOTE_ARTICOLO),
                ))

        return records


class FakeProduzioneAttivaSource(ProduzioneAttivaSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale.

    Accetta una lista di ProduzioneAttivaRecord alla costruzione.
    Non richiede connessione a Easy o a qualsiasi sistema esterno.
    """

    def __init__(self, records: list[ProduzioneAttivaRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[ProduzioneAttivaRecord]:
        return list(self._records)
