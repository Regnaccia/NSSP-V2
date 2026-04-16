"""Global proposal logic config and closed registry."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from nssp_v2.core.production_proposals.models import CoreProposalLogicConfig

KNOWN_PROPOSAL_LOGICS: list[str] = [
    "proposal_target_pieces_v1",
    "proposal_required_qty_total_v1",  # alias legacy compatibile
    "proposal_full_bar_v1",
    "proposal_full_bar_v2_capacity_floor",  # ceil → floor → fallback (TASK-V2-127)
]

_DEFAULT_LOGIC_KEY = "proposal_target_pieces_v1"
_DEFAULT_PARAMS_BY_KEY: dict[str, dict] = {
    "proposal_target_pieces_v1": {},
    "proposal_required_qty_total_v1": {},
    "proposal_full_bar_v1": {},
    "proposal_full_bar_v2_capacity_floor": {},
}


class ProposalLogicConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_logic_key: str
    logic_params_by_key: dict[str, dict]
    is_default: bool
    updated_at: datetime | None = None


def get_proposal_logic_config(session: Session) -> ProposalLogicConfig:
    try:
        row = session.scalar(select(CoreProposalLogicConfig))
    except OperationalError:
        row = None
    if row is None:
        return ProposalLogicConfig(
            default_logic_key=_DEFAULT_LOGIC_KEY,
            logic_params_by_key=dict(_DEFAULT_PARAMS_BY_KEY),
            is_default=True,
            updated_at=None,
        )
    return ProposalLogicConfig(
        default_logic_key=row.default_logic_key,
        logic_params_by_key=dict(row.logic_params_by_key_json),
        is_default=False,
        updated_at=row.updated_at,
    )


def set_proposal_logic_config(
    session: Session,
    default_logic_key: str,
    logic_params_by_key: dict[str, dict],
) -> ProposalLogicConfig:
    if default_logic_key not in KNOWN_PROPOSAL_LOGICS:
        raise ValueError(
            f"Logic non ammessa: '{default_logic_key}'. Ammesse: {KNOWN_PROPOSAL_LOGICS}"
        )
    unknown = [k for k in logic_params_by_key.keys() if k not in KNOWN_PROPOSAL_LOGICS]
    if unknown:
        raise ValueError(f"Logic params non ammessi: {unknown}")

    now = datetime.now(timezone.utc)
    row = session.scalar(select(CoreProposalLogicConfig))
    if row is None:
        row = CoreProposalLogicConfig(
            default_logic_key=default_logic_key,
            logic_params_by_key_json=dict(logic_params_by_key),
            updated_at=now,
        )
        session.add(row)
    else:
        row.default_logic_key = default_logic_key
        row.logic_params_by_key_json = dict(logic_params_by_key)
        row.updated_at = now
    session.commit()
    return ProposalLogicConfig(
        default_logic_key=default_logic_key,
        logic_params_by_key=dict(logic_params_by_key),
        is_default=False,
        updated_at=now,
    )
