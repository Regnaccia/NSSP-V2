"""
Source adapter per l'entita `destinazioni`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/POT_DESTDIV) non deve mai essere modificata dalla sync.

Adapter disponibili:
- DestinazioneSourceAdapter: ABC — interfaccia obbligatoria
- EasyDestinazioneSource:    adapter read-only verso POT_DESTDIV (EasyJob SQL Server)
- FakeDestinazioneSource:    implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_DESTINAZIONI.md:
  PDES_COD             -> codice_destinazione   (source identity)
  CLI_COD              -> codice_cli             (nullable)
  NUM_PROGR_CLIENTE    -> numero_progressivo_cliente (nullable)
  PDES_IND             -> indirizzo              (nullable)
  NAZ_COD              -> nazione_codice         (nullable)
  CITTA                -> citta                  (nullable)
  PROV                 -> provincia              (nullable)
  PDES_TEL1            -> telefono_1             (nullable)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DestinazioneRecord:
    """Record di una destinazione proveniente dalla sorgente (POT_DESTDIV).

    Tutti i campi riflettono la sorgente Easy senza arricchimento business.

    Mapping da EASY_DESTINAZIONI.md:
    - codice_destinazione:          PDES_COD — source identity tecnica
    - codice_cli:                   CLI_COD (nullable)
    - numero_progressivo_cliente:   NUM_PROGR_CLIENTE (nullable)
    - indirizzo:                    PDES_IND (nullable)
    - nazione_codice:               NAZ_COD (nullable)
    - citta:                        CITTA (nullable)
    - provincia:                    PROV (nullable)
    - telefono_1:                   PDES_TEL1 (nullable)
    """

    codice_destinazione: str
    codice_cli: str | None = None
    numero_progressivo_cliente: str | None = None
    indirizzo: str | None = None
    nazione_codice: str | None = None
    citta: str | None = None
    provincia: str | None = None
    telefono_1: str | None = None


class DestinazioneSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `destinazioni`.

    Ogni implementazione concreta deve:
    - leggere solo dalla sorgente esterna
    - non scrivere mai verso la sorgente

    Regola: nessun metodo write e permesso in questa interfaccia (DL-ARCH-V2-007 §2).
    """

    @abstractmethod
    def fetch_all(self) -> list[DestinazioneRecord]:
        """Restituisce tutte le destinazioni dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    """Trim tecnico: stringa vuota o solo spazi → None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyDestinazioneSource(DestinazioneSourceAdapter):
    """Adapter read-only per POT_DESTDIV (EasyJob SQL Server).

    Legge i campi selezionati in EASY_DESTINAZIONI.md tramite pyodbc.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

    # Query read-only — solo i campi del mapping EASY_DESTINAZIONI.md
    _QUERY = """
        SELECT
            PDES_COD,
            CLI_COD,
            NUM_PROGR_CLIENTE,
            PDES_IND,
            NAZ_COD,
            CITTA,
            PROV,
            PDES_TEL1
        FROM POT_DESTDIV
    """

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string

    def fetch_all(self) -> list[DestinazioneRecord]:
        """Legge tutte le destinazioni da POT_DESTDIV. Read-only."""
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[DestinazioneRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                records.append(DestinazioneRecord(
                    codice_destinazione=row.PDES_COD.strip() if row.PDES_COD else "",
                    codice_cli=_strip_or_none(row.CLI_COD),
                    numero_progressivo_cliente=_strip_or_none(row.NUM_PROGR_CLIENTE),
                    indirizzo=_strip_or_none(row.PDES_IND),
                    nazione_codice=_strip_or_none(row.NAZ_COD),
                    citta=_strip_or_none(row.CITTA),
                    provincia=_strip_or_none(row.PROV),
                    telefono_1=_strip_or_none(row.PDES_TEL1),
                ))

        return records


class FakeDestinazioneSource(DestinazioneSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale."""

    def __init__(self, records: list[DestinazioneRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[DestinazioneRecord]:
        return list(self._records)
