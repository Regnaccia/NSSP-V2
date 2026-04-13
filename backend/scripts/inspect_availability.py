"""
Diagnostica completa della disponibilita per un singolo articolo.

Mostra tutti i componenti del calcolo:
  on_hand_qty         (da core_inventory_positions / sync_mag_reale)
  customer_set_aside  (da core_customer_set_aside, per riga)
  committed           (da core_commitments, per riga e per source_type)
  availability_qty    (da core_availability — valore finale)

Confronta con la formula Easy:
  Easy:  giacenza - appartati - da_evadere
  ODE:   on_hand - set_aside - committed(customer_order) - committed(production)

Differenza attesa:
  committed(production) = MM_PEZZO da produzioni attive — Easy NON lo sottrae
  nella sua vista disponibilita.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/inspect_availability.py 18X11X125R
"""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nssp_v2.shared.db import SessionLocal
from nssp_v2.shared.article_codes import normalize_article_code
from nssp_v2.core.inventory_positions.models import CoreInventoryPosition
from nssp_v2.core.customer_set_aside.models import CoreCustomerSetAside
from nssp_v2.core.commitments.models import CoreCommitment
from nssp_v2.core.availability.models import CoreAvailability
from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.righe_ordine_cliente.models import SyncRigaOrdineCliente
from sqlalchemy import func

SEP = "-" * 80
_ZERO = Decimal("0")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python inspect_availability.py <CODICE_ARTICOLO>")
        sys.exit(1)

    raw_code = sys.argv[1]
    article_code = normalize_article_code(raw_code)
    if article_code is None:
        print(f"Codice non valido: {raw_code!r}")
        sys.exit(1)

    print(SEP)
    print(f"  DIAGNOSI DISPONIBILITA: {article_code}")
    print(SEP)

    with SessionLocal() as session:

        # ── 1. Inventory position ─────────────────────────────────────────────
        print("\n[1] GIACENZA (core_inventory_positions)")
        inv = session.query(CoreInventoryPosition).filter(
            CoreInventoryPosition.article_code == article_code
        ).first()
        if inv is None:
            print("  Nessuna posizione inventariale trovata — on_hand = 0")
            on_hand = _ZERO
        else:
            on_hand = Decimal(str(inv.on_hand_qty))
            print(f"  total_load_qty  : {float(inv.total_load_qty):>12.3f}")
            print(f"  total_unload_qty: {float(inv.total_unload_qty):>12.3f}")
            print(f"  on_hand_qty     : {float(on_hand):>12.3f}  ← giacenza netta")
            print(f"  movement_count  : {inv.movement_count}")
            print(f"  computed_at     : {inv.computed_at}")

        # ── 2. Riepilogo movimenti grezzi (sanity check) ──────────────────────
        print("\n[2] MOVIMENTI GREZZI (sync_mag_reale) — sanity check")
        mag_row = session.query(
            func.count(SyncMagReale.id).label("cnt"),
            func.sum(func.coalesce(SyncMagReale.quantita_caricata, 0)).label("tot_car"),
            func.sum(func.coalesce(SyncMagReale.quantita_scaricata, 0)).label("tot_sca"),
        ).filter(SyncMagReale.codice_articolo == raw_code).first()

        mag_row_upper = session.query(
            func.count(SyncMagReale.id).label("cnt"),
            func.sum(func.coalesce(SyncMagReale.quantita_caricata, 0)).label("tot_car"),
            func.sum(func.coalesce(SyncMagReale.quantita_scaricata, 0)).label("tot_sca"),
        ).filter(SyncMagReale.codice_articolo == article_code).first()

        # Usa il result piu grande (per gestire differenze case)
        if mag_row and mag_row.cnt:
            print(f"  Trovati {mag_row.cnt} movimenti per codice esatto '{raw_code}'")
            print(f"  tot_car={float(mag_row.tot_car):.3f}  tot_sca={float(mag_row.tot_sca):.3f}  "
                  f"netto={float(mag_row.tot_car - mag_row.tot_sca):.3f}")
        if mag_row_upper and mag_row_upper.cnt and mag_row_upper.cnt != (mag_row.cnt if mag_row else 0):
            print(f"  (anche con UPPER '{article_code}': {mag_row_upper.cnt} movimenti, "
                  f"netto={float(mag_row_upper.tot_car - mag_row_upper.tot_sca):.3f})")
        if (not mag_row or not mag_row.cnt) and (not mag_row_upper or not mag_row_upper.cnt):
            print("  Nessun movimento in sync_mag_reale per questo articolo")

        # ── 3. Customer set aside ─────────────────────────────────────────────
        print("\n[3] SET ASIDE (core_customer_set_aside)")
        csa_rows = session.query(CoreCustomerSetAside).filter(
            CoreCustomerSetAside.article_code == article_code
        ).order_by(CoreCustomerSetAside.source_reference).all()

        if not csa_rows:
            print("  Nessun set aside trovato — totale = 0")
            total_set_aside = _ZERO
        else:
            total_set_aside = sum((Decimal(str(r.set_aside_qty)) for r in csa_rows), _ZERO)
            print(f"  {'source_reference':<35}  {'set_aside_qty':>14}")
            print(f"  {'-'*35}  {'-'*14}")
            for r in csa_rows:
                print(f"  {r.source_reference:<35}  {float(r.set_aside_qty):>14.3f}")
            print(f"  {'TOTALE':<35}  {float(total_set_aside):>14.3f}")

        # ── 4. Commitments ────────────────────────────────────────────────────
        print("\n[4] COMMITMENTS (core_commitments)")
        com_rows = session.query(CoreCommitment).filter(
            CoreCommitment.article_code == article_code
        ).order_by(CoreCommitment.source_type, CoreCommitment.source_reference).all()

        if not com_rows:
            print("  Nessun commitment trovato — totale = 0")
            total_committed = _ZERO
            committed_customer = _ZERO
            committed_production = _ZERO
        else:
            committed_customer = sum(
                (Decimal(str(r.committed_qty)) for r in com_rows if r.source_type == "customer_order"),
                _ZERO,
            )
            committed_production = sum(
                (Decimal(str(r.committed_qty)) for r in com_rows if r.source_type == "production"),
                _ZERO,
            )
            total_committed = committed_customer + committed_production

            print(f"  {'source_type':<20}  {'source_reference':<35}  {'committed_qty':>14}")
            print(f"  {'-'*20}  {'-'*35}  {'-'*14}")
            for r in com_rows:
                print(f"  {r.source_type:<20}  {r.source_reference:<35}  {float(r.committed_qty):>14.3f}")
            print(f"  {'TOTALE customer_order':<57}  {float(committed_customer):>14.3f}")
            print(f"  {'TOTALE production':<57}  {float(committed_production):>14.3f}")
            print(f"  {'TOTALE':<57}  {float(total_committed):>14.3f}")

        # ── 5. Disponibilita finale ───────────────────────────────────────────
        print("\n[5] DISPONIBILITA FINALE (core_availability)")
        avail = session.query(CoreAvailability).filter(
            CoreAvailability.article_code == article_code
        ).first()

        if avail is None:
            print("  Nessun record in core_availability per questo articolo")
            computed_avail = None
        else:
            computed_avail = Decimal(str(avail.availability_qty))
            print(f"  inventory_qty          : {float(avail.inventory_qty):>12.3f}")
            print(f"  customer_set_aside_qty : {float(avail.customer_set_aside_qty):>12.3f}")
            print(f"  committed_qty          : {float(avail.committed_qty):>12.3f}")
            print(f"  availability_qty       : {float(computed_avail):>12.3f}  ← valore ODE")
            print(f"  computed_at            : {avail.computed_at}")

        # ── 6. Righe ordine aperte (raw) ──────────────────────────────────────
        print("\n[6] RIGHE ORDINE APERTE (sync_righe_ordine_cliente)")
        ord_rows = session.query(SyncRigaOrdineCliente).filter(
            SyncRigaOrdineCliente.article_code == article_code,
            SyncRigaOrdineCliente.continues_previous_line == False,  # noqa: E712
        ).order_by(
            SyncRigaOrdineCliente.order_reference,
            SyncRigaOrdineCliente.line_reference,
        ).all()

        if not ord_rows:
            print("  Nessuna riga ordine trovata")
            easy_da_evadere = _ZERO
        else:
            print(f"  {'ordine/riga':<25}  {'ordinata':>10}  {'evasa':>10}  {'appartata':>10}  "
                  f"{'da_evadere':>10}  {'open_qty':>10}")
            print(f"  {'-'*25}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")
            easy_da_evadere = _ZERO
            for r in ord_rows:
                qtor = Decimal(str(r.ordered_qty)) if r.ordered_qty is not None else _ZERO
                qtev = Decimal(str(r.fulfilled_qty)) if r.fulfilled_qty is not None else _ZERO
                qtap = Decimal(str(r.set_aside_qty)) if r.set_aside_qty is not None else _ZERO
                da_ev = qtor - qtev  # Easy: non sottrae appartati
                open_q = max(qtor - qtap - qtev, _ZERO)  # ODE
                easy_da_evadere += da_ev
                ref = f"{r.order_reference}/{r.line_reference}"
                print(f"  {ref:<25}  {float(qtor):>10.3f}  {float(qtev):>10.3f}  "
                      f"{float(qtap):>10.3f}  {float(da_ev):>10.3f}  {float(open_q):>10.3f}")
            print(f"  {'TOTALE da_evadere (Easy)':<25}  {'':>10}  {'':>10}  {'':>10}  "
                  f"{float(easy_da_evadere):>10.3f}")

        # ── 7. Riepilogo comparativo ──────────────────────────────────────────
        print(f"\n{SEP}")
        print("  RIEPILOGO COMPARATIVO")
        print(SEP)
        print(f"  Giacenza (on_hand)                : {float(on_hand):>10.3f}")
        print(f"  Set aside (appartati DOC_QTAP)    : {float(total_set_aside):>10.3f}")
        print(f"  Committed customer_order          : {float(committed_customer if com_rows else _ZERO):>10.3f}")
        print(f"  Committed production (MM_PEZZO)   : {float(committed_production if com_rows else _ZERO):>10.3f}")
        print()
        ode_avail = on_hand - total_set_aside - (committed_customer if com_rows else _ZERO) - (committed_production if com_rows else _ZERO)
        easy_avail = on_hand - total_set_aside - easy_da_evadere if ord_rows else on_hand - total_set_aside
        print(f"  ODE availability_qty              : {float(ode_avail):>10.3f}  "
              f"(on_hand - set_aside - committed_co - committed_prod)")
        print(f"  Easy qty_disponibile (stimato)    : {float(easy_avail):>10.3f}  "
              f"(giacenza - appartati - da_evadere)")
        print(f"  Differenza ODE vs Easy            : {float(ode_avail - easy_avail):>10.3f}  "
              f"← dovrebbe essere ≈ -committed_production")
        print()

        if computed_avail is not None:
            check = computed_avail - ode_avail
            status = "OK" if abs(check) < Decimal("0.001") else "ATTENZIONE: discrepanza!"
            print(f"  [CHECK] core_availability vs ricalcolo live: diff={float(check):.3f}  {status}")

        print(SEP)


if __name__ == "__main__":
    main()
