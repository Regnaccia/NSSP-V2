"""
Source adapter per l'entita `clienti`.

Interfaccia read-only: nessun metodo di scrittura (DL-ARCH-V2-007 §2).
La sorgente esterna (Easy/ANACLI) non deve mai essere modificata dalla sync.

Adapter disponibili:
- ClienteSourceAdapter: ABC — interfaccia obbligatoria
- FakeClienteSource:    implementazione fake fixture-driven per test e sviluppo locale

La connessione reale a ANACLI (EasyJob SQL Server) verra implementata
in un task successivo dedicato all'integrazione Easy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClienteRecord:
    """Record di un cliente proveniente dalla sorgente (ANACLI).

    Campi noti da ANACLI (EasyJob):
    - codice_cli:     CLI_COD — source identity key
    - ragione_sociale: CLI_RAG1
    """

    codice_cli: str
    ragione_sociale: str


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


class FakeClienteSource(ClienteSourceAdapter):
    """Sorgente fake fixture-driven per test e sviluppo locale.

    Accetta una lista di ClienteRecord alla costruzione.
    Non richiede connessione a Easy o a qualsiasi sistema esterno.
    """

    def __init__(self, records: list[ClienteRecord]) -> None:
        self._records = list(records)

    def fetch_all(self) -> list[ClienteRecord]:
        return list(self._records)
