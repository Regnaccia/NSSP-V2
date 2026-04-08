"""
Source adapter per l'entita `produzioni_storiche`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/SDPRE_PROD) non deve mai essere modificata dalla sync.

Adapter disponibili:
- ProduzioneStoricaSourceAdapter: ABC — interfaccia obbligatoria
- EasyProduzioneStoricaSource:    adapter read-only verso SDPRE_PROD (EasyJob SQL Server)
- FakeProduzioneStoricaSource:    implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_PRODUZIONI.md (identici a produzioni_attive):
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

Differenze tecniche gestite (EASY_PRODUZIONI.md §Structural Check):
  - `scritto` (lowercase in SDPRE_PROD) — campo deferred, non presente nella query
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProduzioneStoricaRecord:
    """Record di una produzione storica proveniente da SDPRE_PROD.

    Struttura identica a ProduzioneAttivaRecord — sorgente diversa (SDPRE_PROD).
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


class ProduzioneStoricaSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `produzioni_storiche`."""

    @abstractmethod
    def fetch_all(self) -> list[ProduzioneStoricaRecord]:
        """Restituisce tutte le produzioni storiche dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class EasyProduzioneStoricaSource(ProduzioneStoricaSourceAdapter):
    """Adapter read-only per SDPRE_PROD (EasyJob SQL Server).

    Identico a EasyProduzioneAttivaSource ma interroga SDPRE_PROD.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars
    """

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
        FROM SDPRE_PROD
    """

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string

    def fetch_all(self) -> list[ProduzioneStoricaRecord]:
        """Legge tutte le produzioni storiche da SDPRE_PROD. Read-only."""
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[ProduzioneStoricaRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                records.append(ProduzioneStoricaRecord(
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


class FakeProduzioneStoricaSource(ProduzioneStoricaSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale."""

    def __init__(self, records: list[ProduzioneStoricaRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[ProduzioneStoricaRecord]:
        return list(self._records)
