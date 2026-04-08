"""
Source adapter per l'entita `mag_reale` (TASK-V2-036).

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/MAG_REALE) non deve mai essere modificata dalla sync.

Adapter disponibili:
- MagRealeSourceAdapter:   ABC — interfaccia obbligatoria
- EasyMagRealeSource:      adapter read-only verso MAG_REALE (EasyJob SQL Server)
- FakeMagRealeSource:      implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_MAG_REALE.md:
  ID_MAGREALE   -> id_movimento                  (source identity, cursor)
  ART_COD       -> codice_articolo               (nullable, normalizzato: strip+upper)
  QTA_CAR       -> quantita_caricata             (nullable)
  QTA_SCA       -> quantita_scaricata            (nullable)
  CAUM_COD      -> causale_movimento_codice      (nullable)
  DOC_DATA      -> data_movimento                (nullable)

Normalizzazione tecnica (DL-ARCH-V2-016 §8, EASY_MAG_REALE.md):
  codice_articolo: trim + uppercase per confronto cross-source con ANAART.ART_COD
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class MagRealeRecord:
    """Record di un movimento di magazzino proveniente da MAG_REALE."""

    id_movimento: int
    codice_articolo: str | None = None
    quantita_caricata: Decimal | None = None
    quantita_scaricata: Decimal | None = None
    causale_movimento_codice: str | None = None
    data_movimento: datetime | None = None


class MagRealeSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `mag_reale`."""

    @abstractmethod
    def fetch_since(self, min_id: int) -> list[MagRealeRecord]:
        """Restituisce i movimenti con ID_MAGREALE > min_id, ordinati per ID_MAGREALE ASC.

        min_id = 0 per il bootstrap completo.
        Read-only: nessuna scrittura verso Easy.
        """
        ...


def _normalize_codice_articolo(value: str | None) -> str | None:
    """Normalizzazione tecnica del codice articolo (DL-ARCH-V2-016 §8).

    Regole:
    - trim spazi iniziali e finali
    - conversione a maiuscolo
    - None se stringa vuota dopo trim
    """
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized if normalized else None


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyMagRealeSource(MagRealeSourceAdapter):
    """Adapter read-only per MAG_REALE (EasyJob SQL Server).

    Legge i movimenti con ID_MAGREALE > min_id per sync incrementale.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

    _QUERY = """
        SELECT
            ID_MAGREALE,
            ART_COD,
            QTA_CAR,
            QTA_SCA,
            CAUM_COD,
            DOC_DATA
        FROM MAG_REALE
        WHERE ID_MAGREALE > ?
        ORDER BY ID_MAGREALE ASC
    """

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string

    def fetch_since(self, min_id: int) -> list[MagRealeRecord]:
        """Legge i movimenti da MAG_REALE con ID_MAGREALE > min_id. Read-only."""
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[MagRealeRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY, (min_id,))
            for row in cursor.fetchall():
                records.append(MagRealeRecord(
                    id_movimento=int(row.ID_MAGREALE),
                    codice_articolo=_normalize_codice_articolo(row.ART_COD),
                    quantita_caricata=(
                        Decimal(str(row.QTA_CAR)) if row.QTA_CAR is not None else None
                    ),
                    quantita_scaricata=(
                        Decimal(str(row.QTA_SCA)) if row.QTA_SCA is not None else None
                    ),
                    causale_movimento_codice=_strip_or_none(row.CAUM_COD),
                    data_movimento=row.DOC_DATA,
                ))

        return records


class FakeMagRealeSource(MagRealeSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale."""

    def __init__(self, records: list[MagRealeRecord]) -> None:
        self._records = list(records)

    def fetch_since(self, min_id: int) -> list[MagRealeRecord]:
        return [r for r in self._records if r.id_movimento > min_id]
