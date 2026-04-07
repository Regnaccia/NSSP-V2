"""
Entrypoint on-demand per la sync `destinazioni`.

Modalita:
  --source easy   (default) — legge da POT_DESTDIV via EasyDestinazioneSource
                              richiede EASY_CONNECTION_STRING in .env
  --source fake             — usa FakeDestinazioneSource con record demo

Nota: la sync `destinazioni` dipende da `clienti`.
Assicurarsi che `sync_clienti` sia gia stata eseguita prima di questa.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[dev,easy]"
    python scripts/sync_destinazioni.py
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.destinazioni.source import (
    DestinazioneRecord,
    EasyDestinazioneSource,
    FakeDestinazioneSource,
)
from nssp_v2.sync.destinazioni.unit import DestinazioneSyncUnit

DEMO_DESTINAZIONI = [
    DestinazioneRecord(codice_destinazione="D001", codice_cli="C001", citta="Milano", provincia="MI"),
    DestinazioneRecord(codice_destinazione="D002", codice_cli="C001", citta="Roma", provincia="RM"),
    DestinazioneRecord(codice_destinazione="D003", codice_cli="C002", citta="Torino", provincia="TO"),
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
    parser = argparse.ArgumentParser(description="Sync destinazioni on-demand")
    parser.add_argument(
        "--source", choices=["easy", "fake"], default="easy",
        help="Sorgente dati: 'easy' (default) o 'fake'"
    )
    args = parser.parse_args()

    if args.source == "fake":
        source = FakeDestinazioneSource(DEMO_DESTINAZIONI)
        print("=== Sync destinazioni — on demand (FakeDestinazioneSource) ===")
        print(f"Sorgente: fake ({len(DEMO_DESTINAZIONI)} record demo)")
    else:
        try:
            conn_str = _get_easy_connection_string()
        except RuntimeError as exc:
            print(f"ERRORE: {exc}", file=sys.stderr)
            sys.exit(1)
        source = EasyDestinazioneSource(conn_str)
        print("=== Sync destinazioni — on demand (EasyDestinazioneSource) ===")
        print("Sorgente: Easy POT_DESTDIV (read-only)")
    print()

    unit = DestinazioneSyncUnit()

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
