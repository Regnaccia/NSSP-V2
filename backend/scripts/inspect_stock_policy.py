"""
Analisi diagnostica della stock policy V1.

Valuta la qualita dei dati e i parametri dell'algoritmo
`monthly_stock_base_from_sales_v1` sui dati reali del DB.

Esecuzione:
    cd backend
    .venv\\Scripts\\activate
    python scripts/inspect_stock_policy.py

Output (in sequenza):
  [1] Perimetro articoli — quanti articoli, divisi per famiglia
  [2] Distribuzione mesi attivi — quanti articoli "a rotazione lenta"
  [3] Causali movimenti — ci sono causali non-consumo che gonfiano la stima?
  [4] Confronto stime per finestra — quanto divergono P50 a 3/6/12 mesi
  [5] Output algoritmo reale — risultati di list_stock_metrics_v1 (top 30)
  [6] Articoli con monthly_base = None — quanti e perche
"""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import func, text
from nssp_v2.shared.db import SessionLocal
from nssp_v2.core.stock_policy.queries import list_stock_metrics_v1
from nssp_v2.sync.mag_reale.models import SyncMagReale
from nssp_v2.sync.articoli.models import SyncArticolo
from nssp_v2.core.articoli.models import CoreArticoloConfig, ArticoloFamiglia

SEP = "=" * 80
SEP2 = "-" * 80


def _fmt(v, decimals=1):
    if v is None:
        return "None"
    try:
        return f"{float(v):.{decimals}f}"
    except Exception:
        return str(v)


def main() -> None:

    with SessionLocal() as session:

        # ─── [1] Perimetro articoli ───────────────────────────────────────────
        print(f"\n{SEP}")
        print("  [1] PERIMETRO ARTICOLI CON SCORTE ATTIVE (per famiglia)")
        print(SEP)

        rows = session.execute(text("""
            SELECT
                f.code                                                              AS famiglia,
                COUNT(*)                                                            AS n_articoli,
                COUNT(CASE WHEN ac.override_stock_months IS NOT NULL THEN 1 END)    AS con_override_mesi,
                ROUND(AVG(COALESCE(ac.override_stock_months, f.stock_months)::numeric), 2)         AS avg_stock_months,
                ROUND(AVG(COALESCE(ac.override_stock_trigger_months, f.stock_trigger_months)::numeric), 2) AS avg_trigger_months
            FROM sync_articoli sa
            JOIN core_articolo_config ac ON sa.codice_articolo = ac.codice_articolo
            JOIN articolo_famiglie f     ON ac.famiglia_code   = f.code
            WHERE sa.attivo = TRUE
              AND COALESCE(ac.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) = TRUE
              AND COALESCE(ac.override_gestione_scorte_attiva,       f.gestione_scorte_attiva)       = TRUE
            GROUP BY f.code
            ORDER BY n_articoli DESC
        """)).fetchall()

        if not rows:
            print("  Nessun articolo nel perimetro stock policy.")
        else:
            total = sum(r.n_articoli for r in rows)
            print(f"  {'Famiglia':<20}  {'N art':>6}  {'Override mesi':>13}  {'Avg stock_months':>16}  {'Avg trigger_months':>18}")
            print(f"  {'-'*20}  {'-'*6}  {'-'*13}  {'-'*16}  {'-'*18}")
            for r in rows:
                print(f"  {r.famiglia:<20}  {r.n_articoli:>6}  {r.con_override_mesi:>13}  "
                      f"{_fmt(r.avg_stock_months):>16}  {_fmt(r.avg_trigger_months):>18}")
            print(f"  {'TOTALE':<20}  {total:>6}")

        # ─── [2] Distribuzione mesi attivi (12 mesi) ─────────────────────────
        print(f"\n{SEP}")
        print("  [2] DISTRIBUZIONE MESI CON USCITE (ultimi 12 mesi)")
        print("      Mostra quanti articoli hanno dati sparsi vs. continui")
        print(SEP)

        rows2 = session.execute(text("""
            WITH perimetro AS (
                SELECT UPPER(TRIM(sa.codice_articolo)) AS code
                FROM sync_articoli sa
                JOIN core_articolo_config ac ON sa.codice_articolo = ac.codice_articolo
                JOIN articolo_famiglie f     ON ac.famiglia_code   = f.code
                WHERE sa.attivo = TRUE
                  AND COALESCE(ac.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) = TRUE
                  AND COALESCE(ac.override_gestione_scorte_attiva,       f.gestione_scorte_attiva)       = TRUE
            ),
            movimenti AS (
                SELECT
                    UPPER(TRIM(codice_articolo)) AS code,
                    COUNT(DISTINCT DATE_TRUNC('month', data_movimento))  AS mesi_con_uscite,
                    COUNT(*)                                             AS n_righe,
                    SUM(quantita_scaricata)                              AS tot_pezzi
                FROM sync_mag_reale
                WHERE data_movimento >= NOW() - INTERVAL '12 months'
                  AND quantita_scaricata > 0
                GROUP BY UPPER(TRIM(codice_articolo))
            )
            SELECT
                COALESCE(m.mesi_con_uscite, 0)               AS mesi_attivi,
                COUNT(*)                                      AS n_articoli,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct,
                ROUND(AVG(COALESCE(m.n_righe, 0)), 1)        AS avg_righe,
                ROUND(AVG(COALESCE(m.tot_pezzi, 0)), 0)      AS avg_pezzi
            FROM perimetro p
            LEFT JOIN movimenti m ON p.code = m.code
            GROUP BY COALESCE(m.mesi_con_uscite, 0)
            ORDER BY mesi_attivi
        """)).fetchall()

        if rows2:
            print(f"  {'Mesi attivi':>11}  {'N art':>6}  {'%':>5}  {'Avg righe':>9}  {'Avg pezzi':>10}  Note")
            print(f"  {'-'*11}  {'-'*6}  {'-'*5}  {'-'*9}  {'-'*10}  {'-'*30}")
            total2 = sum(r.n_articoli for r in rows2)
            for r in rows2:
                note = ""
                if r.mesi_attivi == 0:
                    note = "<-- ZERO dati: monthly_base = None"
                elif r.mesi_attivi <= 2:
                    note = "<-- dati scarsi: finestre corte potrebbero non passare"
                elif r.mesi_attivi >= 10:
                    note = "<-- dati ricchi"
                print(f"  {r.mesi_attivi:>11}  {r.n_articoli:>6}  {float(r.pct):>4.1f}%  "
                      f"{_fmt(r.avg_righe, 1):>9}  {_fmt(r.avg_pezzi, 0):>10}  {note}")
            print(f"  {'TOTALE':<11}  {total2:>6}")

        # ─── [3] Causali movimenti ────────────────────────────────────────────
        print(f"\n{SEP}")
        print("  [3] CAUSALI MOVIMENTI (ultimi 12 mesi — solo scarichi)")
        print("      Verifica se ci sono causali non-consumo che gonfiano la stima")
        print(SEP)

        rows3 = session.execute(text("""
            SELECT
                COALESCE(causale_movimento_codice, 'NULL')              AS causale,
                COUNT(*)                                                AS n_righe,
                ROUND(SUM(quantita_scaricata)::numeric, 0)              AS tot_qty_scaricata,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)     AS pct_righe
            FROM sync_mag_reale
            WHERE data_movimento >= NOW() - INTERVAL '12 months'
              AND quantita_scaricata > 0
            GROUP BY COALESCE(causale_movimento_codice, 'NULL')
            ORDER BY n_righe DESC
        """)).fetchall()

        if rows3:
            print(f"  {'Causale':<10}  {'N righe':>8}  {'Tot qty scaricata':>18}  {'%':>6}")
            print(f"  {'-'*10}  {'-'*8}  {'-'*18}  {'-'*6}")
            for r in rows3:
                print(f"  {r.causale:<10}  {r.n_righe:>8}  "
                      f"{_fmt(r.tot_qty_scaricata, 0):>18}  {float(r.pct_righe):>5.1f}%")

        # ─── [4] Confronto P50 per finestra ──────────────────────────────────
        print(f"\n{SEP}")
        print("  [4] CONFRONTO STIME P50 PER FINESTRA (3m / 6m / 12m) — top 40 per volume")
        print("      Mostra quanto divergono le finestre: alta divergenza = trend in corso")
        print(SEP)

        rows4 = session.execute(text("""
            WITH perimetro AS (
                SELECT UPPER(TRIM(sa.codice_articolo)) AS code
                FROM sync_articoli sa
                JOIN core_articolo_config ac ON sa.codice_articolo = ac.codice_articolo
                JOIN articolo_famiglie f     ON ac.famiglia_code   = f.code
                WHERE sa.attivo = TRUE
                  AND COALESCE(ac.override_aggrega_codice_in_produzione, f.aggrega_codice_in_produzione) = TRUE
                  AND COALESCE(ac.override_gestione_scorte_attiva,       f.gestione_scorte_attiva)       = TRUE
            ),
            monthly_agg AS (
                SELECT
                    UPPER(TRIM(codice_articolo))         AS code,
                    DATE_TRUNC('month', data_movimento)  AS mese,
                    SUM(quantita_scaricata)               AS qty
                FROM sync_mag_reale
                WHERE data_movimento >= NOW() - INTERVAL '12 months'
                  AND quantita_scaricata > 0
                GROUP BY UPPER(TRIM(codice_articolo)), DATE_TRUNC('month', data_movimento)
            )
            SELECT
                p.code,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY qty) FILTER (
                    WHERE mese >= DATE_TRUNC('month', NOW() - INTERVAL '3 months')
                )::numeric, 1)  AS p50_3m,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY qty) FILTER (
                    WHERE mese >= DATE_TRUNC('month', NOW() - INTERVAL '6 months')
                )::numeric, 1)  AS p50_6m,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY qty)::numeric, 1)  AS p50_12m,
                COUNT(DISTINCT mese)       AS mesi_totali,
                ROUND(SUM(qty)::numeric, 0) AS pezzi_12m
            FROM perimetro p
            LEFT JOIN monthly_agg m ON p.code = m.code
            GROUP BY p.code
            HAVING COUNT(DISTINCT mese) > 0
            ORDER BY pezzi_12m DESC NULLS LAST
            LIMIT 40
        """)).fetchall()

        if rows4:
            print(f"  {'Codice':<18}  {'P50 3m':>8}  {'P50 6m':>8}  {'P50 12m':>9}  "
                  f"{'Mesi':>5}  {'Tot 12m':>9}  {'Trend':>30}")
            print(f"  {'-'*18}  {'-'*8}  {'-'*8}  {'-'*9}  {'-'*5}  {'-'*9}  {'-'*30}")
            for r in rows4:
                p3 = float(r.p50_3m) if r.p50_3m is not None else None
                p12 = float(r.p50_12m) if r.p50_12m is not None else None
                # Valuta il trend: se P50 3m >> P50 12m c'e' un trend crescente
                if p3 is not None and p12 is not None and p12 > 0:
                    ratio = p3 / p12
                    if ratio > 1.5:
                        trend = f"CRESCENTE (3m/12m={ratio:.1f}x)"
                    elif ratio < 0.5:
                        trend = f"DECRESCENTE (3m/12m={ratio:.1f}x)"
                    else:
                        trend = "stabile"
                else:
                    trend = ""
                print(f"  {r.code:<18}  {_fmt(r.p50_3m, 1):>8}  {_fmt(r.p50_6m, 1):>8}  "
                      f"{_fmt(r.p50_12m, 1):>9}  {r.mesi_totali:>5}  "
                      f"{_fmt(r.pezzi_12m, 0):>9}  {trend}")

        # ─── [5] Output algoritmo reale ───────────────────────────────────────
        print(f"\n{SEP}")
        print("  [5] OUTPUT ALGORITMO REALE (list_stock_metrics_v1) — top 30 per monthly_base")
        print(SEP)

        metrics = list_stock_metrics_v1(session)
        metrics_with_base = [m for m in metrics if m.monthly_stock_base_qty is not None]
        metrics_without_base = [m for m in metrics if m.monthly_stock_base_qty is None]

        metrics_with_base.sort(key=lambda m: m.monthly_stock_base_qty, reverse=True)

        if metrics_with_base:
            print(f"  Parametri usati: {metrics_with_base[0].params_snapshot}")
            print()
            print(f"  {'Codice':<18}  {'Base/mese':>9}  {'Capacity':>9}  {'Target':>9}  {'Trigger':>9}")
            print(f"  {'-'*18}  {'-'*9}  {'-'*9}  {'-'*9}  {'-'*9}")
            for m in metrics_with_base[:30]:
                print(f"  {m.article_code:<18}  "
                      f"{_fmt(m.monthly_stock_base_qty, 1):>9}  "
                      f"{_fmt(m.capacity_effective_qty, 1):>9}  "
                      f"{_fmt(m.target_stock_qty, 1):>9}  "
                      f"{_fmt(m.trigger_stock_qty, 1):>9}")

        # ─── [6] Articoli con monthly_base = None ────────────────────────────
        print(f"\n{SEP}")
        print("  [6] ARTICOLI CON monthly_base = None (dati insufficienti)")
        print(SEP)

        print(f"  Totale nel perimetro    : {len(metrics)}")
        print(f"  Con monthly_base        : {len(metrics_with_base)}")
        print(f"  Senza monthly_base      : {len(metrics_without_base)}")
        print()

        if metrics_without_base:
            # Per ognuno mostriamo quanti mesi di dati hanno realmente
            codes_without = [m.article_code for m in metrics_without_base]
            # Query per capire il motivo (0 mesi vs qualche mese ma sotto la soglia)
            rows6 = session.execute(text("""
                SELECT
                    UPPER(TRIM(codice_articolo))                                AS code,
                    COUNT(DISTINCT DATE_TRUNC('month', data_movimento))         AS mesi_con_uscite,
                    COUNT(*)                                                    AS n_righe,
                    ROUND(SUM(quantita_scaricata)::numeric, 0)                  AS tot_pezzi
                FROM sync_mag_reale
                WHERE data_movimento >= NOW() - INTERVAL '12 months'
                  AND quantita_scaricata > 0
                  AND UPPER(TRIM(codice_articolo)) = ANY(:codes)
                GROUP BY UPPER(TRIM(codice_articolo))
            """), {"codes": codes_without}).fetchall()

            has_some_data = {r.code: r for r in rows6}
            zero_data = [c for c in codes_without if c not in has_some_data]
            has_data_but_none = [c for c in codes_without if c in has_some_data]

            print(f"  Senza NESSUN movimento negli ultimi 12m: {len(zero_data)}")
            if zero_data:
                for c in zero_data[:10]:
                    print(f"    {c}")
                if len(zero_data) > 10:
                    print(f"    ... e altri {len(zero_data) - 10}")

            print(f"\n  Con movimenti ma monthly_base = None (sotto soglia min_nonzero_months): {len(has_data_but_none)}")
            if has_data_but_none:
                print(f"  {'Codice':<18}  {'Mesi':>5}  {'Righe':>6}  {'Tot pezzi':>10}")
                print(f"  {'-'*18}  {'-'*5}  {'-'*6}  {'-'*10}")
                for c in has_data_but_none[:20]:
                    r = has_some_data[c]
                    print(f"  {c:<18}  {r.mesi_con_uscite:>5}  {r.n_righe:>6}  {_fmt(r.tot_pezzi, 0):>10}")
                if len(has_data_but_none) > 20:
                    print(f"  ... e altri {len(has_data_but_none) - 20}")

        print(f"\n{SEP}")
        print("  ANALISI COMPLETATA")
        print(SEP)
        print()


if __name__ == "__main__":
    main()
