"""
Entrypoint on-demand per la sync `clienti`.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/sync_clienti.py

Usa FakeClienteSource con dati fixture per demo e test locali senza Easy online.
Per usare la sorgente Easy reale, sostituire FakeClienteSource con l'adapter
EasyJob quando disponibile.
"""

import sys
from pathlib import Path

# Aggiunge src/ al path per esecuzione diretta senza pip install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.clienti.source import ClienteRecord, FakeClienteSource
from nssp_v2.sync.clienti.unit import ClienteSyncUnit

# ─── Fixture dati demo ────────────────────────────────────────────────────────

DEMO_CLIENTI = [
    ClienteRecord(codice_cli="C001", ragione_sociale="Alfa Srl"),
    ClienteRecord(codice_cli="C002", ragione_sociale="Beta Spa"),
    ClienteRecord(codice_cli="C003", ragione_sociale="Gamma & C"),
]


def main() -> None:
    print("=== Sync clienti — on demand ===")
    print(f"Sorgente: FakeClienteSource ({len(DEMO_CLIENTI)} record demo)")
    print()

    source = FakeClienteSource(DEMO_CLIENTI)
    unit = ClienteSyncUnit()

    with SessionLocal() as session:
        meta = unit.run(session, source)

    print(f"Run ID:       {meta.run_id}")
    print(f"Entity:       {meta.entity_code}")
    print(f"Status:       {meta.status}")
    print(f"Rows seen:    {meta.rows_seen}")
    print(f"Rows written: {meta.rows_written}")
    print(f"Rows deleted: {meta.rows_deleted}")
    print(f"Started at:   {meta.started_at.isoformat()}")
    print(f"Finished at:  {meta.finished_at.isoformat() if meta.finished_at else '-'}")
    if meta.error_message:
        print(f"Error:        {meta.error_message}")
    print()

    if meta.status == "success":
        print("OK — sync completata con successo.")
        sys.exit(0)
    else:
        print("ERRORE — sync fallita.")
        sys.exit(1)


if __name__ == "__main__":
    main()
