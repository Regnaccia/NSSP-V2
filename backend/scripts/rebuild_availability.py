"""
Entrypoint on-demand per il rebuild del fact `availability`.

Ricostruisce completamente `core_availability` a partire dai tre fact canonici:
- core_inventory_positions
- core_customer_set_aside
- core_commitments

Formula: availability_qty = inventory_qty - customer_set_aside_qty - committed_qty
Aggregazione: per codice_articolo.
Valori negativi ammessi (nessun clamp a zero).

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/rebuild_availability.py

Prerequisito: i tre fact sorgente devono essere stati gia calcolati almeno una volta.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.availability.queries import rebuild_availability


def main() -> None:
    print("=== Rebuild availability ===")
    print("Sorgenti: core_inventory_positions, core_customer_set_aside, core_commitments")
    print("Target:   core_availability")
    print()

    with SessionLocal() as session:
        created = rebuild_availability(session)
        session.commit()

    print(f"Posizioni create: {created}")
    print()
    print("OK — rebuild completato con successo.")
    sys.exit(0)


if __name__ == "__main__":
    main()
