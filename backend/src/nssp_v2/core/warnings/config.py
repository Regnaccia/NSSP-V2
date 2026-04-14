"""
Gestione configurazione visibilita warning (TASK-V2-077, TASK-V2-081, DL-ARCH-V2-029).

Struttura:
- WarningTypeConfigItem: read model della configurazione per tipo warning
- KNOWN_WARNING_TYPES: vocabolario canonico dei tipi warning supportati
- KNOWN_AREAS: aree/reparti operativi validi per la configurazione di visibilita
- get_visible_to_areas: risolve visible_to_areas da DB con fallback al default
- list_warning_configs: lista completa config (persistite + default per tipi noti)
- set_warning_config: aggiorna o crea la config per un tipo warning

Regola (DL-ARCH-V2-029 §6):
- la configurazione di visibilita e governata dalla surface admin
- i moduli operativi la leggono ma non la modificano
- se non esiste una riga per un tipo, si usa il default del tipo

Vocabolario aree (TASK-V2-081):
- magazzino
- produzione
- logistica

La surface `Warnings` e un punto trasversale: non dipende da una configurazione
per tipo. Tutti i warning sono sempre visibili nella surface Warnings.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from nssp_v2.core.warnings.config_model import WarningTypeConfig

# ─── Vocabolario e default ─────────────────────────────────────────────────────

# Tipi warning noti in V1
KNOWN_WARNING_TYPES: list[str] = ["INVALID_STOCK_CAPACITY", "NEGATIVE_STOCK"]

# Aree/reparti operativi validi per la configurazione di visibilita (V1)
KNOWN_AREAS: list[str] = ["magazzino", "produzione", "logistica"]

# Default visible_to_areas per tipo — usato se non esiste config in DB
_AREA_DEFAULTS: dict[str, list[str]] = {
    "NEGATIVE_STOCK": ["magazzino", "produzione"],
    "INVALID_STOCK_CAPACITY": ["produzione", "magazzino", "admin"],
}


# ─── Read model ───────────────────────────────────────────────────────────────

class WarningTypeConfigItem(BaseModel):
    """Configurazione di visibilita per un tipo warning.

    is_default=True: nessuna riga in DB — si sta usando il default del tipo.
    is_default=False: riga presente in DB — configurazione esplicita.
    updated_at=None quando is_default=True.
    """

    model_config = ConfigDict(frozen=True)

    warning_type: str
    visible_to_areas: list[str]
    is_default: bool
    updated_at: datetime | None = None


# ─── Query ────────────────────────────────────────────────────────────────────

def get_visible_to_areas(session: Session, warning_type: str) -> list[str]:
    """Risolve visible_to_areas per un tipo warning.

    Se esiste una configurazione in DB, usa quella.
    Altrimenti usa il default del tipo (_AREA_DEFAULTS).
    """
    row = session.scalar(
        select(WarningTypeConfig).where(WarningTypeConfig.warning_type == warning_type)
    )
    if row is not None:
        return list(row.visible_to_areas)
    return list(_AREA_DEFAULTS.get(warning_type, []))


def list_warning_configs(session: Session) -> list[WarningTypeConfigItem]:
    """Lista configurazioni per tutti i tipi warning noti.

    Restituisce un item per ogni tipo in KNOWN_WARNING_TYPES.
    Se la configurazione e presente in DB usa quella, altrimenti usa il default.
    Ordinamento: warning_type alfabetico.
    """
    db_rows: dict[str, WarningTypeConfig] = {
        row.warning_type: row
        for row in session.scalars(select(WarningTypeConfig)).all()
    }

    result = []
    for wt in sorted(KNOWN_WARNING_TYPES):
        row = db_rows.get(wt)
        if row is not None:
            result.append(WarningTypeConfigItem(
                warning_type=wt,
                visible_to_areas=list(row.visible_to_areas),
                is_default=False,
                updated_at=row.updated_at,
            ))
        else:
            result.append(WarningTypeConfigItem(
                warning_type=wt,
                visible_to_areas=list(_AREA_DEFAULTS.get(wt, [])),
                is_default=True,
                updated_at=None,
            ))
    return result


def set_warning_config(
    session: Session,
    warning_type: str,
    visible_to_areas: list[str],
) -> WarningTypeConfigItem:
    """Aggiorna o crea la configurazione di visibilita per un tipo warning.

    Valori non in KNOWN_AREAS sono accettati ma non consigliati.
    Dopo il commit restituisce il read model aggiornato.
    """
    row = session.scalar(
        select(WarningTypeConfig).where(WarningTypeConfig.warning_type == warning_type)
    )
    now = datetime.now(timezone.utc)

    if row is None:
        row = WarningTypeConfig(
            warning_type=warning_type,
            visible_to_areas=list(visible_to_areas),
            updated_at=now,
        )
        session.add(row)
    else:
        row.visible_to_areas = list(visible_to_areas)
        row.updated_at = now

    session.commit()

    return WarningTypeConfigItem(
        warning_type=warning_type,
        visible_to_areas=list(visible_to_areas),
        is_default=False,
        updated_at=now,
    )
