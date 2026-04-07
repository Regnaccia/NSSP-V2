"""
Source adapter per l'entita `clienti`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/ANACLI) non deve mai essere modificata dalla sync.

Adapter disponibili:
- ClienteSourceAdapter: ABC — interfaccia obbligatoria
- EasyClienteSource:    adapter read-only verso ANACLI (EasyJob SQL Server)
- FakeClienteSource:    implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_CLIENTI.md:
  CLI_COD   -> codice_cli        (source identity)
  CLI_RAG1  -> ragione_sociale
  CLI_IND   -> indirizzo         (nullable)
  NAZ_COD   -> nazione_codice    (nullable)
  PROV      -> provincia         (nullable)
  CLI_TEL1  -> telefono_1        (nullable)
  CLI_DTMO  -> source_modified_at (nullable — candidato watermark futuro)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClienteRecord:
    """Record di un cliente proveniente dalla sorgente (ANACLI).

    Tutti i campi riflettono la sorgente Easy senza arricchimento business.
    I campi nullable vengono passati come None se assenti in sorgente.

    Mapping da EASY_CLIENTI.md:
    - codice_cli:          CLI_COD — source identity key
    - ragione_sociale:     CLI_RAG1
    - indirizzo:           CLI_IND (nullable)
    - nazione_codice:      NAZ_COD (nullable)
    - provincia:           PROV (nullable)
    - telefono_1:          CLI_TEL1 (nullable)
    - source_modified_at:  CLI_DTMO (nullable)
    """

    codice_cli: str
    ragione_sociale: str
    indirizzo: str | None = None
    nazione_codice: str | None = None
    provincia: str | None = None
    telefono_1: str | None = None
    source_modified_at: datetime | None = None


class ClienteSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `clienti`.

    Ogni implementazione concreta deve:
    - leggere solo dalla sorgente esterna
    - non scrivere mai verso la sorgente

    Regola: nessun metodo write e permesso in questa interfaccia (DL-ARCH-V2-007 §2).
    """

    @abstractmethod
    def fetch_all(self) -> list[ClienteRecord]:
        """Restituisce tutti i clienti dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    """Trim tecnico: stringa vuota o solo spazi → None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyClienteSource(ClienteSourceAdapter):
    """Adapter read-only per ANACLI (EasyJob SQL Server).

    Legge i campi selezionati in EASY_CLIENTI.md tramite pyodbc.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

    # Query read-only — solo i campi del mapping EASY_CLIENTI.md
    _QUERY = """
        SELECT
            CLI_COD,
            CLI_RAG1,
            CLI_IND,
            NAZ_COD,
            PROV,
            CLI_TEL1,
            CLI_DTMO
        FROM ANACLI
    """

    def __init__(self, connection_string: str) -> None:
        """
        Args:
            connection_string: pyodbc connection string per Easy SQL Server.
                               Formato: DRIVER={SQL Server};SERVER=...;DATABASE=ELFESQL;UID=...;PWD=...
        """
        self._connection_string = connection_string

    def fetch_all(self) -> list[ClienteRecord]:
        """Legge tutti i clienti da ANACLI. Read-only.

        Non modifica nessun dato nella sorgente.
        Normalizzazioni tecniche consentite (EASY_CLIENTI.md §Technical Normalization):
        - trim spazi iniziali e finali
        - stringa vuota → None per i campi nullable
        """
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[ClienteRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                records.append(ClienteRecord(
                    codice_cli=row.CLI_COD.strip() if row.CLI_COD else "",
                    ragione_sociale=_strip_or_none(row.CLI_RAG1) or "",
                    indirizzo=_strip_or_none(row.CLI_IND),
                    nazione_codice=_strip_or_none(row.NAZ_COD),
                    provincia=_strip_or_none(row.PROV),
                    telefono_1=_strip_or_none(row.CLI_TEL1),
                    source_modified_at=row.CLI_DTMO,
                ))

        return records


class FakeClienteSource(ClienteSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale.

    Accetta una lista di ClienteRecord alla costruzione.
    Non richiede connessione a Easy o a qualsiasi sistema esterno.
    """

    def __init__(self, records: list[ClienteRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[ClienteRecord]:
        return list(self._records)
