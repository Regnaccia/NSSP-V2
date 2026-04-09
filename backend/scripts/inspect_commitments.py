"""
Estratto leggibile dei commitments attivi nel mirror locale.

Stampa i record presenti in `core_commitments`, raggruppati per source_type.
Utile per verificare il risultato del rebuild dopo una sync ordini o produzioni.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/inspect_commitments.py [--article CODICE] [--source customer_order|production]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.commitments.queries import list_commitments


def main() -> None:
    parser = argparse.ArgumentParser(description="Estratto commitments dal mirror locale")
    parser.add_argument("--article", default=None, help="Filtra per codice articolo")
    parser.add_argument("--source", default=None, help="Filtra per source_type (es. customer_order, production)")
    parser.add_argument("--limit", type=int, default=50, help="Numero massimo di righe (default: 50)")
    args = parser.parse_args()

    with SessionLocal() as session:
        rows = list_commitments(session, source_type=args.source)

    if args.article:
        rows = [r for r in rows if r.article_code == args.article]

    rows = rows[: args.limit]

    if not rows:
        print("Nessun commitment trovato.")
        sys.exit(0)

    print(f"{'article_code':<25}  {'source_type':<20}  {'source_reference':<30}  {'committed_qty':>15}  computed_at")
    print("-" * 110)
    for r in rows:
        print(
            f"{r.article_code:<25}  {r.source_type:<20}  {r.source_reference:<30}  {float(r.committed_qty):>15.3f}  {r.computed_at}"
        )

    print()
    print(f"Totale righe mostrate: {len(rows)}")


if __name__ == "__main__":
    main()
