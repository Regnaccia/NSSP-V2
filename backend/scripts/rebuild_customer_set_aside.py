"""
Entrypoint on-demand per il rebuild della quota appartata per cliente.

Ricostruisce completamente `core_customer_set_aside` a partire dalle
righe ordine presenti in `sync_righe_ordine_cliente`.

Formula: set_aside_qty = DOC_QTAP per righe con set_aside_qty > 0 e article_code valorizzato.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/rebuild_customer_set_aside.py

Prerequisito: sync_righe_ordine_cliente deve essere gia stata eseguita almeno una volta.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.customer_set_aside.queries import rebuild_customer_set_aside


def main() -> None:
    print("=== Rebuild customer_set_aside ===")
    print("Sorgente: sync_righe_ordine_cliente (mirror locale)")
    print("Target:   core_customer_set_aside")
    print()

    with SessionLocal() as session:
        created = rebuild_customer_set_aside(session)
        session.commit()

    print(f"Record creati: {created}")
    print()
    print("OK — rebuild completato con successo.")
    sys.exit(0)


if __name__ == "__main__":
    main()
