"""
Script manuale per la sync `produzioni_attive` (TASK-V2-028).

Uso:
    cd backend
    python scripts/sync_produzioni_attive.py --source easy
    python scripts/sync_produzioni_attive.py --source fake

Opzioni:
    --source easy   Legge da DPRE_PROD (Easy SQL Server — richiede EASY_CONNECTION_STRING)
    --source fake   Usa 3 record fake per verifica strutturale (nessuna connessione richiesta)
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

# Aggiunge src/ al path per esecuzione diretta senza install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import get_engine, SessionLocal
from nssp_v2.sync.produzioni_attive.unit import ProduzioneAttivaSyncUnit
from nssp_v2.sync.produzioni_attive.source import (
    EasyProduzioneAttivaSource,
    FakeProduzioneAttivaSource,
    ProduzioneAttivaRecord,
)


def _fake_records() -> list[ProduzioneAttivaRecord]:
    return [
        ProduzioneAttivaRecord(
            id_dettaglio=1001,
            cliente_ragione_sociale="ACME SRL",
            codice_articolo="ART001",
            descrizione_articolo="Bullone M8",
            descrizione_articolo_2=None,
            numero_riga_documento=1,
            quantita_ordinata=Decimal("100.00000"),
            quantita_prodotta=Decimal("0.00000"),
            materiale_partenza_codice="MAT001",
            materiale_partenza_per_pezzo=Decimal("0.05000"),
            misura_articolo="M8x20",
            numero_documento="ORD001",
            codice_immagine=None,
            riferimento_numero_ordine_cliente="CLI001",
            riferimento_riga_ordine_cliente=Decimal("1"),
            note_articolo=None,
        ),
        ProduzioneAttivaRecord(
            id_dettaglio=1002,
            cliente_ragione_sociale="BETA SPA",
            codice_articolo="ART002",
            descrizione_articolo="Dado M10",
            descrizione_articolo_2=None,
            numero_riga_documento=2,
            quantita_ordinata=Decimal("50.00000"),
            quantita_prodotta=Decimal("10.00000"),
            materiale_partenza_codice=None,
            materiale_partenza_per_pezzo=None,
            misura_articolo=None,
            numero_documento="ORD002",
            codice_immagine=None,
            riferimento_numero_ordine_cliente=None,
            riferimento_riga_ordine_cliente=None,
            note_articolo="urgente",
        ),
        ProduzioneAttivaRecord(
            id_dettaglio=1003,
            cliente_ragione_sociale=None,
            codice_articolo="ART003",
            descrizione_articolo="Barra 10x10",
            descrizione_articolo_2="C45",
            numero_riga_documento=1,
            quantita_ordinata=Decimal("200.00000"),
            quantita_prodotta=Decimal("200.00000"),
            materiale_partenza_codice="BAR001",
            materiale_partenza_per_pezzo=Decimal("0.20000"),
            misura_articolo="10x10x2000",
            numero_documento="ORD003",
            codice_immagine=None,
            riferimento_numero_ordine_cliente=None,
            riferimento_riga_ordine_cliente=None,
            note_articolo=None,
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync produzioni attive (DPRE_PROD)")
    parser.add_argument("--source", choices=["easy", "fake"], required=True)
    args = parser.parse_args()

    if args.source == "easy":
        import os
        conn_str = os.environ.get("EASY_CONNECTION_STRING")
        if not conn_str:
            # Prova a leggere da .env
            env_file = Path(__file__).parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("EASY_CONNECTION_STRING="):
                        conn_str = line.split("=", 1)[1].strip()
                        break
        if not conn_str:
            print("ERRORE: EASY_CONNECTION_STRING non configurata", file=sys.stderr)
            sys.exit(1)
        source = EasyProduzioneAttivaSource(conn_str)
        print("Sorgente: Easy (DPRE_PROD)")
    else:
        source = FakeProduzioneAttivaSource(_fake_records())
        print("Sorgente: fake (3 record)")

    engine = get_engine()
    with SessionLocal(bind=engine) as session:
        unit = ProduzioneAttivaSyncUnit()
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
