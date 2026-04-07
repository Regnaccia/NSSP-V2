"""
Entrypoint on-demand per la sync `articoli`.

Modalita:
  --source easy   (default) — legge da ANAART via EasyArticoloSource
                              richiede EASY_CONNECTION_STRING in .env
  --source fake             — usa FakeArticoloSource con record demo

Nota: la sync `articoli` non ha dipendenze da altre sync unit.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[dev,easy]"
    python scripts/sync_articoli.py
"""

import argparse
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.articoli.source import (
    ArticoloRecord,
    EasyArticoloSource,
    FakeArticoloSource,
)
from nssp_v2.sync.articoli.unit import ArticoloSyncUnit

DEMO_ARTICOLI = [
    ArticoloRecord(
        codice_articolo="ART001",
        descrizione_1="Articolo Demo Uno",
        unita_misura_codice="PZ",
        categoria_articolo_1="CAT01",
    ),
    ArticoloRecord(
        codice_articolo="ART002",
        descrizione_1="Articolo Demo Due",
        descrizione_2="Riga 2",
        unita_misura_codice="KG",
        peso_grammi=Decimal("250.00000"),
    ),
    ArticoloRecord(
        codice_articolo="ART003",
        descrizione_1="Articolo Demo Tre",
        materiale_grezzo_codice="MAT01",
        quantita_materiale_grezzo_occorrente=Decimal("1.50000"),
        quantita_materiale_grezzo_scarto=Decimal("0.10000"),
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
    parser = argparse.ArgumentParser(description="Sync articoli on-demand")
    parser.add_argument(
        "--source", choices=["easy", "fake"], default="easy",
        help="Sorgente dati: 'easy' (default) o 'fake'"
    )
    args = parser.parse_args()

    if args.source == "fake":
        source = FakeArticoloSource(DEMO_ARTICOLI)
        print("=== Sync articoli — on demand (FakeArticoloSource) ===")
        print(f"Sorgente: fake ({len(DEMO_ARTICOLI)} record demo)")
    else:
        try:
            conn_str = _get_easy_connection_string()
        except RuntimeError as exc:
            print(f"ERRORE: {exc}", file=sys.stderr)
            sys.exit(1)
        source = EasyArticoloSource(conn_str)
        print("=== Sync articoli — on demand (EasyArticoloSource) ===")
        print("Sorgente: Easy ANAART (read-only)")
        print("Nota: nessuna scrittura verso Easy viene eseguita.")
    print()

    unit = ArticoloSyncUnit()

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
