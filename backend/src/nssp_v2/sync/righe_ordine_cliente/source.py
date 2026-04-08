"""
Source adapter per l'entita `righe_ordine_cliente` (TASK-V2-040).

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/V_TORDCLI) non deve mai essere modificata dalla sync.

Adapter disponibili:
- RigaOrdineClienteSourceAdapter:    ABC — interfaccia obbligatoria
- EasyRigheOrdineClienteSource:      adapter read-only verso V_TORDCLI (EasyJob SQL Server)
- FakeRigheOrdineClienteSource:      implementazione fake fixture-driven per test e sviluppo locale

Campi mappati da EASY_RIGHE_ORDINE_CLIENTE.md:
  DOC_NUM           -> order_reference                  (source identity, parte 1)
  NUM_PROGR         -> line_reference                   (source identity, parte 2)
  DOC_DATA          -> order_date                       (nullable)
  DOC_PREV          -> expected_delivery_date           (nullable)
  CLI_COD           -> customer_code                    (nullable)
  PDES_COD          -> destination_code                 (nullable)
  NUM_PROGR_CLIENTE -> customer_destination_progressive (nullable)
  N_ORDCLI          -> customer_order_reference         (nullable)
  ART_COD           -> article_code                     (nullable)
  ART_DESCR         -> article_description_segment      (nullable)
  ART_MISURA        -> article_measure                  (nullable)
  DOC_QTOR          -> ordered_qty                      (nullable)
  DOC_QTEV          -> fulfilled_qty                    (nullable)
  DOC_QTAP          -> set_aside_qty                    (nullable)
  DOC_PZ_NETTO      -> net_unit_price                   (nullable)
  COLL_RIGA_PREC    -> continues_previous_line          (nullable — bit)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class RigaOrdineClienteRecord:
    """Record di una riga ordine cliente proveniente dalla sorgente (V_TORDCLI).

    Tutti i campi riflettono la sorgente Easy senza arricchimento business.
    I campi nullable vengono passati come None se assenti in sorgente.

    Mapping da EASY_RIGHE_ORDINE_CLIENTE.md:
    - order_reference:                   DOC_NUM — source identity, parte 1
    - line_reference:                    NUM_PROGR — source identity, parte 2
    - order_date:                        DOC_DATA (nullable)
    - expected_delivery_date:            DOC_PREV (nullable)
    - customer_code:                     CLI_COD (nullable)
    - destination_code:                  PDES_COD (nullable)
    - customer_destination_progressive:  NUM_PROGR_CLIENTE (nullable)
    - customer_order_reference:          N_ORDCLI (nullable)
    - article_code:                      ART_COD (nullable: vuoto sulle righe descrittive)
    - article_description_segment:       ART_DESCR (nullable)
    - article_measure:                   ART_MISURA (nullable)
    - ordered_qty:                       DOC_QTOR (nullable)
    - fulfilled_qty:                     DOC_QTEV (nullable)
    - set_aside_qty:                     DOC_QTAP (nullable — quantita inscatolata/appartata)
    - net_unit_price:                    DOC_PZ_NETTO (nullable)
    - continues_previous_line:           COLL_RIGA_PREC (nullable — bit)
    """

    order_reference: str
    line_reference: int
    order_date: datetime | None = None
    expected_delivery_date: datetime | None = None
    customer_code: str | None = None
    destination_code: str | None = None
    customer_destination_progressive: str | None = None
    customer_order_reference: str | None = None
    article_code: str | None = None
    article_description_segment: str | None = None
    article_measure: str | None = None
    ordered_qty: Decimal | None = None
    fulfilled_qty: Decimal | None = None
    set_aside_qty: Decimal | None = None
    net_unit_price: Decimal | None = None
    continues_previous_line: bool | None = None


class RigaOrdineClienteSourceAdapter(ABC):
    """Interfaccia read-only per la sorgente `righe_ordine_cliente`.

    Ogni implementazione concreta deve:
    - leggere solo dalla sorgente esterna
    - non scrivere mai verso la sorgente

    Regola: nessun metodo write e permesso in questa interfaccia (DL-ARCH-V2-007 §2).
    """

    @abstractmethod
    def fetch_all(self) -> list[RigaOrdineClienteRecord]:
        """Restituisce tutte le righe ordine dalla sorgente. Read-only."""
        ...


def _strip_or_none(value: str | None) -> str | None:
    """Trim tecnico: stringa vuota o solo spazi -> None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _to_bool(value) -> bool | None:
    """Converte valore bit SQL Server (0/1/True/False/None) in bool | None."""
    if value is None:
        return None
    return bool(value)


class EasyRigheOrdineClienteSource(RigaOrdineClienteSourceAdapter):
    """Adapter read-only per V_TORDCLI (EasyJob SQL Server).

    Legge i campi selezionati in EASY_RIGHE_ORDINE_CLIENTE.md tramite pyodbc.
    Non esegue alcuna scrittura verso Easy in nessun caso.

    Prerequisiti:
    - pyodbc installato: pip install -e ".[easy]"
    - EASY_CONNECTION_STRING configurata in .env o env vars

    Righe con DOC_NUM o NUM_PROGR NULL vengono scartate: non possono essere
    identificate univocamente come source identity (order_reference, line_reference).
    """

    _QUERY = """
        SELECT
            DOC_NUM,
            NUM_PROGR,
            DOC_DATA,
            DOC_PREV,
            CLI_COD,
            PDES_COD,
            NUM_PROGR_CLIENTE,
            N_ORDCLI,
            ART_COD,
            ART_DESCR,
            ART_MISURA,
            DOC_QTOR,
            DOC_QTEV,
            DOC_QTAP,
            DOC_PZ_NETTO,
            COLL_RIGA_PREC
        FROM V_TORDCLI
    """

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string

    def fetch_all(self) -> list[RigaOrdineClienteRecord]:
        """Legge tutte le righe ordine da V_TORDCLI. Read-only.

        Normalizzazioni tecniche consentite (EASY_RIGHE_ORDINE_CLIENTE.md):
        - trim spazi iniziali e finali su campi stringa
        - stringa vuota -> None per i campi nullable
        - cast NUM_PROGR (numeric 4,0) a int
        - valori numerici mantenuti senza arrotondamenti business
        - COLL_RIGA_PREC (bit) convertito a bool
        - righe senza DOC_NUM o NUM_PROGR vengono scartate
        """
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc non installato. Eseguire: pip install -e \".[easy]\""
            ) from exc

        records: list[RigaOrdineClienteRecord] = []

        with pyodbc.connect(self._connection_string, autocommit=True, readonly=True) as conn:
            cursor = conn.cursor()
            cursor.execute(self._QUERY)
            for row in cursor.fetchall():
                doc_num = _strip_or_none(row.DOC_NUM)
                if doc_num is None:
                    continue
                if row.NUM_PROGR is None:
                    continue

                records.append(RigaOrdineClienteRecord(
                    order_reference=doc_num,
                    line_reference=int(row.NUM_PROGR),
                    order_date=row.DOC_DATA,
                    expected_delivery_date=row.DOC_PREV,
                    customer_code=_strip_or_none(row.CLI_COD),
                    destination_code=_strip_or_none(row.PDES_COD),
                    customer_destination_progressive=_strip_or_none(row.NUM_PROGR_CLIENTE),
                    customer_order_reference=_strip_or_none(row.N_ORDCLI),
                    article_code=_strip_or_none(row.ART_COD),
                    article_description_segment=_strip_or_none(row.ART_DESCR),
                    article_measure=_strip_or_none(row.ART_MISURA),
                    ordered_qty=Decimal(str(row.DOC_QTOR)) if row.DOC_QTOR is not None else None,
                    fulfilled_qty=Decimal(str(row.DOC_QTEV)) if row.DOC_QTEV is not None else None,
                    set_aside_qty=Decimal(str(row.DOC_QTAP)) if row.DOC_QTAP is not None else None,
                    net_unit_price=Decimal(str(row.DOC_PZ_NETTO)) if row.DOC_PZ_NETTO is not None else None,
                    continues_previous_line=_to_bool(row.COLL_RIGA_PREC),
                ))

        return records


class FakeRigheOrdineClienteSource(RigaOrdineClienteSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale.

    Accetta una lista di RigaOrdineClienteRecord alla costruzione.
    Non richiede connessione a Easy o a qualsiasi sistema esterno.
    """

    def __init__(self, records: list[RigaOrdineClienteRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[RigaOrdineClienteRecord]:
        return list(self._records)
