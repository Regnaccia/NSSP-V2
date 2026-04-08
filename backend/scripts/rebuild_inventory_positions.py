"""
Entrypoint on-demand per il rebuild delle posizioni inventariali.

Ricostruisce completamente `core_inventory_positions` a partire dai
movimenti presenti in `sync_mag_reale`.

Formula: on_hand_qty = sum(quantita_caricata) - sum(quantita_scaricata)
Aggregazione: per codice_articolo (normalizzato).

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/rebuild_inventory_positions.py

Prerequisito: sync_mag_reale deve essere gia stata eseguita almeno una volta.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.inventory_positions.queries import rebuild_inventory_positions


def main() -> None:
    print("=== Rebuild inventory_positions ===")
    print("Sorgente: sync_mag_reale (mirror locale)")
    print("Target:   core_inventory_positions")
    print()

    with SessionLocal() as session:
        created = rebuild_inventory_positions(session)
        session.commit()

    print(f"Posizioni create: {created}")
    print()
    print("OK — rebuild completato con successo.")
    sys.exit(0)


if __name__ == "__main__":
    main()
