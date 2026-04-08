"""
Script manuale per la sync `produzioni_storiche` (TASK-V2-029).

Uso:
    cd backend
    python scripts/sync_produzioni_storiche.py --source easy
    python scripts/sync_produzioni_storiche.py --source fake
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import get_engine, SessionLocal
from nssp_v2.sync.produzioni_storiche.unit import ProduzioneStoricaSyncUnit
from nssp_v2.sync.produzioni_storiche.source import (
    EasyProduzioneStoricaSource,
    FakeProduzioneStoricaSource,
    ProduzioneStoricaRecord,
)


def _fake_records() -> list[ProduzioneStoricaRecord]:
    return [
        ProduzioneStoricaRecord(
            id_dettaglio=5001,
            cliente_ragione_sociale="ACME SRL",
            codice_articolo="ART001",
            descrizione_articolo="Bullone M8",
            quantita_ordinata=Decimal("100.00000"),
            quantita_prodotta=Decimal("100.00000"),
            numero_documento="ORD001",
        ),
        ProduzioneStoricaRecord(
            id_dettaglio=5002,
            cliente_ragione_sociale="BETA SPA",
            codice_articolo="ART002",
            descrizione_articolo="Dado M10",
            quantita_ordinata=Decimal("50.00000"),
            quantita_prodotta=Decimal("50.00000"),
            numero_documento="ORD002",
        ),
        ProduzioneStoricaRecord(
            id_dettaglio=5003,
            codice_articolo="ART003",
            descrizione_articolo="Barra 10x10",
            descrizione_articolo_2="C45",
            quantita_ordinata=Decimal("200.00000"),
            quantita_prodotta=Decimal("200.00000"),
            misura_articolo="10x10x2000",
            numero_documento="ORD003",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync produzioni storiche (SDPRE_PROD)")
    parser.add_argument("--source", choices=["easy", "fake"], required=True)
    args = parser.parse_args()

    if args.source == "easy":
        import os
        conn_str = os.environ.get("EASY_CONNECTION_STRING")
        if not conn_str:
            env_file = Path(__file__).parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("EASY_CONNECTION_STRING="):
                        conn_str = line.split("=", 1)[1].strip()
                        break
        if not conn_str:
            print("ERRORE: EASY_CONNECTION_STRING non configurata", file=sys.stderr)
            sys.exit(1)
        source = EasyProduzioneStoricaSource(conn_str)
        print("Sorgente: Easy (SDPRE_PROD)")
    else:
        source = FakeProduzioneStoricaSource(_fake_records())
        print("Sorgente: fake (3 record)")

    engine = get_engine()
    with SessionLocal(bind=engine) as session:
        unit = ProduzioneStoricaSyncUnit()
        meta = unit.run(session, source)

    print(f"Status:        {meta.status}")
    print(f"Run ID:        {meta.run_id}")
    print(f"Rows seen:     {meta.rows_seen}")
    print(f"Rows written:  {meta.rows_written}")
    print(f"Rows deleted:  {meta.rows_deleted}")
    if meta.error_message:
        print(f"Error:         {meta.error_message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
