"""
Re-bootstrap completo di sync_mag_reale (TASK-V2-073).

Esegue la sequenza:
  1. Truncate sync_mag_reale (reset del mirror)
  2. Re-sync da cursor=0 (tutti i movimenti da Easy)
  3. Rebuild core_inventory_positions
  4. Rebuild core_customer_set_aside
  5. Rebuild core_commitments
  6. Rebuild core_availability
  7. Verifica post-fix per articolo campione

ATTENZIONE: durante l'esecuzione il mirror e in stato inconsistente.
Eseguire preferibilmente fuori orario operativo.

Background:
  Il sync mag_reale usa append_only + no_delete_handling. Se Easy elimina o
  rettifica movimenti gia importati, il mirror diverge. Questo script azzera e
  reimporta tutto da zero, riportando il mirror a un allineamento preciso.
  Vedi: docs/reviews/BUG-MAG-REALE-DELETE-HANDLING-2026-04-10.md

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[dev,easy]"
    python scripts/rebootstrap_mag_reale.py [--verify-article 18X11X125R]
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from nssp_v2.shared.db import SessionLocal
from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.mag_reale.source import EasyMagRealeSource
from nssp_v2.sync.mag_reale.unit import MagRealeSyncUnit
from nssp_v2.core.inventory_positions.queries import rebuild_inventory_positions
from nssp_v2.core.customer_set_aside.queries import rebuild_customer_set_aside
from nssp_v2.core.commitments.queries import rebuild_commitments
from nssp_v2.core.availability.queries import rebuild_availability
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.shared.article_codes import normalize_article_code


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
        description="Re-bootstrap completo sync_mag_reale + rebuild chain (TASK-V2-073)"
    )
    parser.add_argument(
        "--verify-article",
        default="18X11X125R",
        help="Codice articolo da verificare post-fix (default: 18X11X125R)",
    )
    parser.add_argument(
        "--skip-confirm",
        action="store_true",
        help="Salta la conferma interattiva (per automazione)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  RE-BOOTSTRAP sync_mag_reale (TASK-V2-073)")
    print("=" * 70)
    print()
    print("ATTENZIONE: questa operazione:")
    print("  - elimina TUTTE le righe da sync_mag_reale")
    print("  - reimporta tutti i movimenti da Easy (read-only)")
    print("  - ricostruisce la chain: inventory -> set_aside -> commitments -> availability")
    print()

    if not args.skip_confirm:
        answer = input("Continuare? [s/N] ").strip().lower()
        if answer not in ("s", "si", "y", "yes"):
            print("Operazione annullata.")
            sys.exit(0)

    try:
        conn_str = _get_easy_connection_string()
    except RuntimeError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        sys.exit(1)

    source = EasyMagRealeSource(conn_str)

    # ── Step 1: Truncate sync_mag_reale ──────────────────────────────────────
    print()
    print("[1/6] Truncate sync_mag_reale...")
    with SessionLocal() as session:
        count_before = session.query(SyncMagReale).count()
        session.query(SyncMagReale).delete(synchronize_session=False)
        session.commit()
    print(f"      Eliminati {count_before} record dal mirror.")

    # ── Step 2: Re-sync da cursor=0 ──────────────────────────────────────────
    print()
    print("[2/6] Re-sync da Easy (cursor=0 — tutti i movimenti)...")
    unit = MagRealeSyncUnit()

    # Forza cursor=0 bypassando il max(id_movimento) che sarebbe 0 dopo il truncate
    # (gia 0 dopo il truncate, quindi il comportamento normale e corretto)
    with SessionLocal() as session:
        meta = unit.run(session, source)

    if meta.status != "success":
        print(f"ERRORE durante sync mag_reale: {meta.error_message}", file=sys.stderr)
        sys.exit(1)
    print(f"      seen={meta.rows_seen}  written={meta.rows_written}  status={meta.status}")

    # ── Step 3: Rebuild inventory positions ──────────────────────────────────
    print()
    print("[3/6] Rebuild core_inventory_positions...")
    with SessionLocal() as session:
        n = rebuild_inventory_positions(session)
        session.commit()
    print(f"      Posizioni inventariali create: {n}")

    # ── Step 4: Rebuild customer_set_aside ───────────────────────────────────
    print()
    print("[4/6] Rebuild core_customer_set_aside...")
    with SessionLocal() as session:
        n = rebuild_customer_set_aside(session)
        session.commit()
    print(f"      Record set_aside creati: {n}")

    # ── Step 5: Rebuild commitments ───────────────────────────────────────────
    print()
    print("[5/6] Rebuild core_commitments...")
    with SessionLocal() as session:
        n = rebuild_commitments(session)
        session.commit()
    print(f"      Commitment records creati: {n}")

    # ── Step 6: Rebuild availability ──────────────────────────────────────────
    print()
    print("[6/6] Rebuild core_availability...")
    with SessionLocal() as session:
        n = rebuild_availability(session)
        session.commit()
    print(f"      Posizioni availability create: {n}")

    # ── Verifica post-fix ─────────────────────────────────────────────────────
    if args.verify_article:
        article_code = normalize_article_code(args.verify_article)
        print()
        print(f"Verifica post-fix per articolo: {article_code}")

        with SessionLocal() as session:
            avail = session.query(CoreAvailability).filter(
                CoreAvailability.article_code == article_code
            ).first()

        if avail is None:
            print(f"  Nessun record availability per {article_code}")
        else:
            print(f"  inventory_qty     : {float(avail.inventory_qty):>10.3f}")
            print(f"  set_aside_qty     : {float(avail.customer_set_aside_qty):>10.3f}")
            print(f"  committed_qty     : {float(avail.committed_qty):>10.3f}")
            print(f"  availability_qty  : {float(avail.availability_qty):>10.3f}")

        # Confronto con Easy in diretta
        try:
            import pyodbc
            with pyodbc.connect(conn_str, autocommit=True, readonly=True) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT ISNULL(SUM(QTA_CAR),0)-ISNULL(SUM(QTA_SCA),0) as netto "
                    "FROM MAG_REALE WHERE ART_COD = ?",
                    (args.verify_article,),
                )
                easy_netto = float(cur.fetchone().netto)
            ode_netto = float(avail.inventory_qty) if avail else 0.0
            diff = ode_netto - easy_netto
            status = "OK" if abs(diff) < 0.001 else "ATTENZIONE: divergenza residua!"
            print(f"  Easy giacenza     : {easy_netto:>10.3f}")
            print(f"  Differenza ODE-Easy: {diff:>9.3f}  [{status}]")
        except Exception as exc:
            print(f"  (confronto Easy non disponibile: {exc})")

    print()
    print("=" * 70)
    print("  Re-bootstrap completato.")
    print("=" * 70)


if __name__ == "__main__":
    main()
