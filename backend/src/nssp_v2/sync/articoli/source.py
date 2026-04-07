"""
Source adapter per l'entita `articoli`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/ANAART) non deve mai essere modificata dalla sync.

Adapter disponibili:
- ArticoloSourceAdapter: ABC — interfaccia obbligatoria
- EasyArticoloSource:    adapter read-only verso ANAART (EasyJob SQL Server)
- FakeArticoloSource:    implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_ARTICOLI.md:
  ART_COD         -> codice_articolo                      (source identity)
  ART_DES1        -> descrizione_1                        (nullable)
  ART_DES2        -> descrizione_2                        (nullable)
  UM_COD          -> unita_misura_codice                  (nullable)
  ART_DTMO        -> source_modified_at                   (nullable — candidato watermark futuro)
  CAT_ART1        -> categoria_articolo_1                 (nullable)
  MAT_COD         -> materiale_grezzo_codice              (nullable)
  REGN_QT_OCCORR  -> quantita_materiale_grezzo_occorrente (nullable)
  REGN_QT_SCARTO  -> quantita_materiale_grezzo_scarto     (nullable)
  ART_MISURA      -> misura_articolo                      (nullable)
  COD_IMM         -> codice_immagine                      (nullable)
  ART_CONTEN      -> contenitori_magazzino                (nullable)
  ART_KG          -> peso_grammi                          (nullable)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class ArticoloRecord:
    """Record di un articolo proveniente dalla sorgente (ANAART).

    Tutti i campi riflettono la sorgente Easy senza arricchimento business.
    I campi nullable vengono passati come None se assenti in sorgente.

    Mapping da EASY_ARTICOLI.md:
    - codice_articolo:                      ART_COD — source identity key
    - descrizione_1:                        ART_DES1 (nullable)
    - descrizione_2:                        ART_DES2 (nullable)
    - unita_misura_codice:                  UM_COD (nullable)
    - source_modified_at:                   ART_DTMO (nullable)
    - categoria_articolo_1:                 CAT_ART1 (nullable)
    - materiale_grezzo_codice:              MAT_COD (nullable)
    - quantita_materiale_grezzo_occorrente: REGN_QT_OCCORR (nullable)
    - quantita_materiale_grezzo_scarto:     REGN_QT_SCARTO (nullable)
    - misura_articolo:                      ART_MISURA (nullable)
    - codice_immagine:                      COD_IMM (nullable)
    - contenitori_magazzino:                ART_CONTEN (nullable)
    - peso_grammi:                          ART_KG (nullable)
    """

    codice_articolo: str
    descrizione_1: str | None = None
    descrizione_2: str | None = None
    unita_misura_codice: str | None = None
    source_modified_at: datetime | None = None
    categoria_articolo_1: str | None = None
    materiale_grezzo_codice: str | None = None
    quantita_materiale_grezzo_occorrente: Decimal | None = None
    quantita_materiale_grezzo_scarto: Decimal | None = None
    misura_articolo: str | None = None
    codice_immagine: str | None = None
    contenitori_magazzino: str | None = None
    peso_grammi: Decimal | None = None


class ArticoloSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `articoli`.

    Ogni implementazione concreta deve:
    - leggere solo dalla sorgente esterna
    - non scrivere mai verso la sorgente

    Regola: nessun metodo write e permesso in questa interfaccia (DL-ARCH-V2-007 §2).
    """

    @abstractmethod
    def fetch_all(self) -> list[ArticoloRecord]:
        """Restituisce tutti gli articoli dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    """Trim tecnico: stringa vuota o solo spazi → None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyArticoloSource(ArticoloSourceAdapter):
    """Adapter read-only per ANAART (EasyJob SQL Server).

    Legge i campi selezionati in EASY_ARTICOLI.md tramite pyodbc.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

    # Query read-only — solo i campi del mapping EASY_ARTICOLI.md
    _QUERY = """
        SELECT
            ART_COD,
            ART_DES1,
            ART_DES2,
            UM_COD,
            ART_DTMO,
            CAT_ART1,
            MAT_COD,
            REGN_QT_OCCORR,
            REGN_QT_SCARTO,
            ART_MISURA,
            COD_IMM,
            ART_CONTEN,
            ART_KG
        FROM ANAART
    """

    def __init__(self, connection_string: str) -> None:
        """
        Args:
            connection_string: pyodbc connection string per Easy SQL Server.
                               Formato: DRIVER={SQL Server};SERVER=...;DATABASE=ELFESQL;UID=...;PWD=...
        """
        self._connection_string = connection_string

    def fetch_all(self) -> list[ArticoloRecord]:
        """Legge tutti gli articoli da ANAART. Read-only.

        Non modifica nessun dato nella sorgente.
        Normalizzazioni tecniche consentite (EASY_ARTICOLI.md §Technical Normalization):
        - trim spazi iniziali e finali
        - stringa vuota → None per i campi nullable
        - parsing di ART_DTMO a datetime
        - valori numerici mantenuti senza arrotondamenti business
        """
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[ArticoloRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                records.append(ArticoloRecord(
                    codice_articolo=row.ART_COD.strip() if row.ART_COD else "",
                    descrizione_1=_strip_or_none(row.ART_DES1),
                    descrizione_2=_strip_or_none(row.ART_DES2),
                    unita_misura_codice=_strip_or_none(row.UM_COD),
                    source_modified_at=row.ART_DTMO,
                    categoria_articolo_1=_strip_or_none(row.CAT_ART1),
                    materiale_grezzo_codice=_strip_or_none(row.MAT_COD),
                    quantita_materiale_grezzo_occorrente=(
                        Decimal(str(row.REGN_QT_OCCORR)) if row.REGN_QT_OCCORR is not None else None
                    ),
                    quantita_materiale_grezzo_scarto=(
                        Decimal(str(row.REGN_QT_SCARTO)) if row.REGN_QT_SCARTO is not None else None
                    ),
                    misura_articolo=_strip_or_none(row.ART_MISURA),
                    codice_immagine=_strip_or_none(row.COD_IMM),
                    contenitori_magazzino=_strip_or_none(row.ART_CONTEN),
                    peso_grammi=(
                        Decimal(str(row.ART_KG)) if row.ART_KG is not None else None
                    ),
                ))

        return records


class FakeArticoloSource(ArticoloSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale.

    Accetta una lista di ArticoloRecord alla costruzione.
    Non richiede connessione a Easy o a qualsiasi sistema esterno.
    """

    def __init__(self, records: list[ArticoloRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[ArticoloRecord]:
        return list(self._records)
