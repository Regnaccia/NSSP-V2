"""
Entrypoint on-demand per la sync `mag_reale` (incrementale).

Strategia: append_only + cursor — acquisisce solo i movimenti con
ID_MAGREALE > max(id_movimento) gia presente nel mirror locale.
Al primo run (mirror vuoto) esegue il bootstrap completo.

Modalita:
  --source easy   (default) — legge da MAG_REALE via EasyMagRealeSource
                              richiede EASY_CONNECTION_STRING in .env
  --source fake             — usa FakeMagRealeSource con record demo

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[dev,easy]"
    python scripts/sync_mag_reale.py
"""

import argparse
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.mag_reale.source import (
    EasyMagRealeSource,
    FakeMagRealeSource,
    MagRealeRecord,
)
from nssp_v2.sync.mag_reale.unit import MagRealeSyncUnit

DEMO_MOVIMENTI = [
    MagRealeRecord(
        id_movimento=1,
        codice_articolo="ART001",
        quantita_caricata=Decimal("100.000000"),
        data_movimento=datetime(2026, 1, 10),
    ),
    MagRealeRecord(
        id_movimento=2,
        codice_articolo="ART001",
        quantita_scaricata=Decimal("30.000000"),
        data_movimento=datetime(2026, 2, 15),
    ),
    MagRealeRecord(
        id_movimento=3,
        codice_articolo="ART002",
        quantita_caricata=Decimal("50.000000"),
        data_movimento=datetime(2026, 3, 1),
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
    parser = argparse.ArgumentParser(description="Sync mag_reale on-demand (incrementale)")
    parser.add_argument(
        "--source", choices=["easy", "fake"], default="easy",
        help="Sorgente dati: 'easy' (default) o 'fake'"
    )
    args = parser.parse_args()

    if args.source == "fake":
        source = FakeMagRealeSource(DEMO_MOVIMENTI)
        print("=== Sync mag_reale — on demand (FakeMagRealeSource) ===")
        print(f"Sorgente: fake ({len(DEMO_MOVIMENTI)} record demo)")
    else:
        try:
            conn_str = _get_easy_connection_string()
        except RuntimeError as exc:
            print(f"ERRORE: {exc}", file=sys.stderr)
            sys.exit(1)
        source = EasyMagRealeSource(conn_str)
        print("=== Sync mag_reale — on demand (EasyMagRealeSource) ===")
        print("Sorgente: Easy MAG_REALE (read-only, incrementale)")
        print("Nota: nessuna scrittura verso Easy viene eseguita.")
    print()

    unit = MagRealeSyncUnit()

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
