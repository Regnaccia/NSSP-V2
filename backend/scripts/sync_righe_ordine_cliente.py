"""
Entrypoint on-demand per la sync `righe_ordine_cliente` (full_scan).

Strategia: upsert + full_scan — legge tutte le righe da V_TORDCLI a ogni esecuzione.
Per ogni riga: INSERT se non presente, UPDATE se gia presente.
Le righe non piu in sorgente restano nel mirror (no_delete_handling).

Modalita:
  --source easy   (default) — legge da V_TORDCLI via EasyRigheOrdineClienteSource
                              richiede EASY_CONNECTION_STRING in .env
  --source fake             — usa FakeRigheOrdineClienteSource con record demo

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[dev,easy]"
    python scripts/sync_righe_ordine_cliente.py
"""

import argparse
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.righe_ordine_cliente.source import (
    EasyRigheOrdineClienteSource,
    FakeRigheOrdineClienteSource,
    RigaOrdineClienteRecord,
)
from nssp_v2.sync.righe_ordine_cliente.unit import RigheOrdineClienteSyncUnit

DEMO_RIGHE = [
    RigaOrdineClienteRecord(
        order_reference="ORD001",
        line_reference=1,
        order_date=datetime(2026, 3, 10),
        expected_delivery_date=datetime(2026, 4, 15),
        customer_code="CLI001",
        destination_code="DEST01",
        customer_order_reference="REF-CLI-001",
        article_code="ART001",
        article_description_segment="Articolo demo 1",
        article_measure="150x50",
        ordered_qty=Decimal("100.00000"),
        fulfilled_qty=Decimal("20.00000"),
        set_aside_qty=Decimal("10.00000"),
        net_unit_price=Decimal("5.50000"),
        continues_previous_line=False,
    ),
    RigaOrdineClienteRecord(
        order_reference="ORD001",
        line_reference=2,
        order_date=datetime(2026, 3, 10),
        expected_delivery_date=datetime(2026, 4, 15),
        customer_code="CLI001",
        article_code=None,
        article_description_segment="Riga di continuazione descrittiva",
        continues_previous_line=True,
    ),
    RigaOrdineClienteRecord(
        order_reference="ORD002",
        line_reference=1,
        order_date=datetime(2026, 3, 15),
        customer_code="CLI002",
        article_code="ART002",
        ordered_qty=Decimal("50.00000"),
        fulfilled_qty=Decimal("0.00000"),
        set_aside_qty=None,
        net_unit_price=Decimal("12.00000"),
        continues_previous_line=False,
    ),
]


def _get_easy_connection_string() -> str:
    conn_str = os.environ.get("EASY_CONNECTION_STRING")
    if conn_str:
        return conn_str
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("EASY_CONNECTION_STRING="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(
        "EASY_CONNECTION_STRING non trovata.\n"
        "Aggiungila a .env o come variabile d'ambiente."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync righe_ordine_cliente on-demand (full_scan)"
    )
    parser.add_argument(
        "--source", choices=["easy", "fake"], default="easy",
        help="Sorgente dati: 'easy' (default) o 'fake'"
    )
    args = parser.parse_args()

    if args.source == "fake":
        source = FakeRigheOrdineClienteSource(DEMO_RIGHE)
        print("=== Sync righe_ordine_cliente — on demand (FakeRigheOrdineClienteSource) ===")
        print(f"Sorgente: fake ({len(DEMO_RIGHE)} record demo)")
    else:
        try:
            conn_str = _get_easy_connection_string()
        except RuntimeError as exc:
            print(f"ERRORE: {exc}", file=sys.stderr)
            sys.exit(1)
        source = EasyRigheOrdineClienteSource(conn_str)
        print("=== Sync righe_ordine_cliente — on demand (EasyRigheOrdineClienteSource) ===")
        print("Sorgente: Easy V_TORDCLI (read-only, full_scan)")
        print("Nota: nessuna scrittura verso Easy viene eseguita.")
    print()

    unit = RigheOrdineClienteSyncUnit()

    with SessionLocal() as session:
        meta = unit.run(session, source)

    print(f"Run ID:       {meta.run_id}")
    print(f"Entity:       {meta.entity_code}")
    print(f"Status:       {meta.status}")
    print(f"Rows seen:    {meta.rows_seen}")
    print(f"Rows written: {meta.rows_written}")
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
