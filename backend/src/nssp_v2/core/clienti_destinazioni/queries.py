"""
Query del Core slice `clienti + destinazioni` (DL-ARCH-V2-010, DL-ARCH-V2-012).

Regole:
- legge da sync_clienti e sync_destinazioni (mai modifica)
- legge e scrive core_destinazione_config (solo per dati interni configurabili)
- costruisce i read model applicativi (join, display_label, fallback)
- espone elenco destinazioni unificato: principale (ANACLI) + aggiuntive (POT_DESTDIV)
- non espone dati sync_* grezzi alla UI

Identita della destinazione principale (DL-ARCH-V2-012 §4):
  codice_destinazione = "MAIN:{codice_cli}"
  - unica per cliente
  - stabile nel tempo
  - distinguibile dalle aggiuntive per prefisso
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from nssp_v2.core.clienti_destinazioni.models import CoreDestinazioneConfig
from nssp_v2.core.clienti_destinazioni.read_models import (
    ClienteItem,
    DestinazioneDetail,
    DestinazioneItem,
)
from nssp_v2.sync.clienti.models import SyncCliente
from nssp_v2.sync.destinazioni.models import SyncDestinazione


# ─── Identita della destinazione principale ───────────────────────────────────

PRIMARY_PREFIX = "MAIN:"


def _primary_codice(codice_cli: str) -> str:
    """Genera il codice_destinazione della destinazione principale."""
    return f"{PRIMARY_PREFIX}{codice_cli}"


def _is_primary_codice(codice_destinazione: str) -> bool:
    """True se il codice identifica una destinazione principale."""
    return codice_destinazione.startswith(PRIMARY_PREFIX)


def _codice_cli_from_primary(codice_destinazione: str) -> str:
    """Estrae il codice_cli dall'identita della principale."""
    return codice_destinazione[len(PRIMARY_PREFIX):]


# ─── Helpers display_label ────────────────────────────────────────────────────

def _compute_display_label(
    nickname: str | None,
    indirizzo: str | None,
    codice_destinazione: str,
) -> str:
    """Campo sintetico di presentazione per una destinazione aggiuntiva (DL-ARCH-V2-010 §8).

    Ordine di precedenza:
      1. nickname_destinazione (dato interno configurabile)
      2. indirizzo (dato Easy)
      3. codice_destinazione (fallback tecnico)
    """
    return nickname or indirizzo or codice_destinazione


def _compute_primary_display_label(
    nickname: str | None,
    ragione_sociale: str,
    codice_cli: str,
) -> str:
    """Campo sintetico di presentazione per la destinazione principale.

    Ordine di precedenza:
      1. nickname_destinazione (dato interno configurabile)
      2. ragione_sociale (nome cliente — piu leggibile dell'indirizzo per la principale)
      3. codice_cli (fallback tecnico)
    """
    return nickname or ragione_sociale or codice_cli


# ─── Read model: lista clienti ───────────────────────────────────────────────

def list_clienti(session: Session) -> list[ClienteItem]:
    """Restituisce la lista clienti attivi, ordinata per ragione sociale.

    Sorgente: sync_clienti (attivo=True).
    """
    rows = (
        session.query(SyncCliente)
        .filter(SyncCliente.attivo == True)  # noqa: E712
        .order_by(SyncCliente.ragione_sociale)
        .all()
    )
    return [
        ClienteItem(codice_cli=r.codice_cli, ragione_sociale=r.ragione_sociale)
        for r in rows
    ]


# ─── Read model: destinazioni per cliente ────────────────────────────────────

def list_destinazioni_per_cliente(
    session: Session,
    codice_cli: str,
) -> list[DestinazioneItem]:
    """Restituisce l'elenco unificato delle destinazioni del cliente.

    Ordine:
      1. destinazione principale (derivata da sync_clienti, is_primary=True)
      2. destinazioni aggiuntive attive (da sync_destinazioni, is_primary=False)

    La principale e presente solo se il cliente esiste e e attivo in sync_clienti.
    Le aggiuntive sono filtrate per attivo=True e codice_cli.

    Sorgente: sync_clienti + sync_destinazioni + core_destinazione_config (LEFT JOIN).
    """
    result: list[DestinazioneItem] = []

    # 1. Destinazione principale (DL-ARCH-V2-012 §1–§3)
    cliente = (
        session.query(SyncCliente)
        .filter(
            SyncCliente.codice_cli == codice_cli,
            SyncCliente.attivo == True,  # noqa: E712
        )
        .first()
    )
    if cliente is not None:
        p_codice = _primary_codice(codice_cli)
        config = session.get(CoreDestinazioneConfig, p_codice)
        nickname = config.nickname_destinazione if config is not None else None
        result.append(
            DestinazioneItem(
                codice_destinazione=p_codice,
                codice_cli=codice_cli,
                numero_progressivo_cliente=None,
                indirizzo=cliente.indirizzo,
                citta=None,  # non presente in sync_clienti (ANACLI)
                provincia=cliente.provincia,
                nickname_destinazione=nickname,
                display_label=_compute_primary_display_label(
                    nickname, cliente.ragione_sociale, codice_cli
                ),
                is_primary=True,
            )
        )

    # 2. Destinazioni aggiuntive (DL-ARCH-V2-012 §5)
    rows = (
        session.query(SyncDestinazione, CoreDestinazioneConfig)
        .outerjoin(
            CoreDestinazioneConfig,
            SyncDestinazione.codice_destinazione == CoreDestinazioneConfig.codice_destinazione,
        )
        .filter(
            SyncDestinazione.attivo == True,  # noqa: E712
            SyncDestinazione.codice_cli == codice_cli,
        )
        .order_by(SyncDestinazione.codice_destinazione)
        .all()
    )
    for dest, config in rows:
        nickname = config.nickname_destinazione if config is not None else None
        result.append(
            DestinazioneItem(
                codice_destinazione=dest.codice_destinazione,
                codice_cli=dest.codice_cli,
                numero_progressivo_cliente=dest.numero_progressivo_cliente,
                indirizzo=dest.indirizzo,
                citta=dest.citta,
                provincia=dest.provincia,
                nickname_destinazione=nickname,
                display_label=_compute_display_label(
                    nickname, dest.indirizzo, dest.codice_destinazione
                ),
                is_primary=False,
            )
        )

    return result


# ─── Read model: dettaglio destinazione ──────────────────────────────────────

def get_destinazione_detail(
    session: Session,
    codice_destinazione: str,
) -> DestinazioneDetail | None:
    """Restituisce il dettaglio completo di una destinazione.

    Supporta sia la destinazione principale (codice "MAIN:{codice_cli}")
    sia le destinazioni aggiuntive (codice PDES_COD da POT_DESTDIV).

    Restituisce None se la destinazione non esiste.
    """
    if _is_primary_codice(codice_destinazione):
        return _get_primary_detail(session, codice_destinazione)
    return _get_aggiuntiva_detail(session, codice_destinazione)


def _get_primary_detail(
    session: Session,
    codice_destinazione: str,
) -> DestinazioneDetail | None:
    """Dettaglio della destinazione principale, derivata da sync_clienti."""
    codice_cli = _codice_cli_from_primary(codice_destinazione)

    cliente = (
        session.query(SyncCliente)
        .filter(SyncCliente.codice_cli == codice_cli)
        .first()
    )
    if cliente is None:
        return None

    config = session.get(CoreDestinazioneConfig, codice_destinazione)
    nickname = config.nickname_destinazione if config is not None else None

    return DestinazioneDetail(
        codice_destinazione=codice_destinazione,
        codice_cli=codice_cli,
        numero_progressivo_cliente=None,
        indirizzo=cliente.indirizzo,
        citta=None,  # non presente in sync_clienti
        provincia=cliente.provincia,
        nazione_codice=cliente.nazione_codice,
        telefono_1=cliente.telefono_1,
        ragione_sociale_cliente=cliente.ragione_sociale,
        nickname_destinazione=nickname,
        display_label=_compute_primary_display_label(
            nickname, cliente.ragione_sociale, codice_cli
        ),
        is_primary=True,
    )


def _get_aggiuntiva_detail(
    session: Session,
    codice_destinazione: str,
) -> DestinazioneDetail | None:
    """Dettaglio di una destinazione aggiuntiva, con join su sync_clienti e config."""
    row = (
        session.query(SyncDestinazione, SyncCliente, CoreDestinazioneConfig)
        .outerjoin(
            SyncCliente,
            SyncDestinazione.codice_cli == SyncCliente.codice_cli,
        )
        .outerjoin(
            CoreDestinazioneConfig,
            SyncDestinazione.codice_destinazione == CoreDestinazioneConfig.codice_destinazione,
        )
        .filter(SyncDestinazione.codice_destinazione == codice_destinazione)
        .first()
    )

    if row is None:
        return None

    dest, cliente, config = row
    nickname = config.nickname_destinazione if config is not None else None

    return DestinazioneDetail(
        codice_destinazione=dest.codice_destinazione,
        codice_cli=dest.codice_cli,
        numero_progressivo_cliente=dest.numero_progressivo_cliente,
        indirizzo=dest.indirizzo,
        citta=dest.citta,
        provincia=dest.provincia,
        nazione_codice=dest.nazione_codice,
        telefono_1=dest.telefono_1,
        ragione_sociale_cliente=cliente.ragione_sociale if cliente is not None else None,
        nickname_destinazione=nickname,
        display_label=_compute_display_label(
            nickname, dest.indirizzo, dest.codice_destinazione
        ),
        is_primary=False,
    )


# ─── Write: set nickname destinazione ────────────────────────────────────────

def set_nickname_destinazione(
    session: Session,
    codice_destinazione: str,
    nickname: str | None,
) -> None:
    """Imposta o aggiorna il nickname interno della destinazione.

    Valido sia per la destinazione principale (codice "MAIN:{codice_cli}")
    sia per le destinazioni aggiuntive.

    Non modifica mai i target sync_*.
    """
    config = session.get(CoreDestinazioneConfig, codice_destinazione)
    now = datetime.now(timezone.utc)

    if config is None:
        config = CoreDestinazioneConfig(
            codice_destinazione=codice_destinazione,
            nickname_destinazione=nickname,
            updated_at=now,
        )
        session.add(config)
    else:
        config.nickname_destinazione = nickname
        config.updated_at = now

    session.flush()
