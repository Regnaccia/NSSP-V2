"""
Contratto minimo per le sync unit della V2 (DL-ARCH-V2-009).

Ogni sync unit deve dichiarare esplicitamente:
- ENTITY_CODE
- SOURCE_IDENTITY_KEY
- ALIGNMENT_STRATEGY
- CHANGE_ACQUISITION
- DELETE_HANDLING
- DEPENDENCIES
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RunMetadata:
    """Metadati di una singola esecuzione di sync (DL-ARCH-V2-009 §6).

    Prodotti da ogni sync unit al termine dell'esecuzione.
    Devono essere persistiti nel log di run.
    """

    run_id: str
    entity_code: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str = "running"      # running | success | error
    rows_seen: int = 0
    rows_written: int = 0
    rows_deleted: int = 0
    error_message: str | None = None


# ─── Costanti valide per i campi del contratto ───────────────────────────────

ALIGNMENT_STRATEGIES = frozenset({
    "full_replace",
    "upsert",
    "upsert_with_delete_reconciliation",
    "append_only",
})

CHANGE_ACQUISITION_STRATEGIES = frozenset({
    "full_scan",
    "watermark",
    "cursor",
    "external_change_token",
})

DELETE_HANDLING_POLICIES = frozenset({
    "hard_delete",
    "soft_delete",
    "mark_inactive",
    "no_delete_handling",
})
