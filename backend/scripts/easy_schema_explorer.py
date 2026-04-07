"""
Easy Schema Explorer — estrazione schema tabella in formato JSON (read-only).

Uso:
    cd backend
    .venv\\Scripts\\activate
    pip install -e ".[easy]"          # installa pyodbc
    python scripts/easy_schema_explorer.py --table ANACLI

    # oppure con output path esplicito:
    python scripts/easy_schema_explorer.py --table ANACLI --out ../docs/integrations/easy/catalog/ANACLI.json

Output JSON salvato in:
    docs/integrations/easy/catalog/<TABLE_NAME>.json   (default)

Prerequisiti:
    - EASY_CONNECTION_STRING nel file .env (o come variabile d'ambiente)
    - Driver ODBC SQL Server installato sul sistema (Windows: incluso, Linux: msodbcsql18)

Formato EASY_CONNECTION_STRING (vedere .env.example):
    DRIVER={SQL Server};SERVER=SERVER\\SQLEXPRESS;DATABASE=ELFESQL;UID=sa;PWD=<password>

Policy read-only:
    Questo script esegue solo SELECT su INFORMATION_SCHEMA.
    Non esegue INSERT, UPDATE, DELETE ne DDL verso Easy in nessun caso.
    La connessione non viene aperta in modalita write.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default output directory relativo alla root del repo V2
_DEFAULT_CATALOG_DIR = Path(__file__).parent.parent.parent / "docs" / "integrations" / "easy" / "catalog"


def _get_connection_string() -> str:
    """Legge EASY_CONNECTION_STRING da env vars o da .env locale."""
    # Prova prima la variabile d'ambiente diretta
    conn_str = os.environ.get("EASY_CONNECTION_STRING")
    if conn_str:
        return conn_str

    # Prova a leggere .env locale (senza dipendenze: parsing minimale)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("EASY_CONNECTION_STRING="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "EASY_CONNECTION_STRING non trovata.\n"
        "Aggiungila a .env o come variabile d'ambiente.\n"
        "Formato: DRIVER={SQL Server};SERVER=HOST\\INSTANCE;DATABASE=ELFESQL;UID=...;PWD=..."
    )


def explore_table(table_name: str, connection_string: str) -> dict:
    """Estrae lo schema di una tabella da Easy via INFORMATION_SCHEMA (read-only).

    Returns:
        dict con chiavi: table_name, extracted_at, columns, primary_keys
    """
    try:
        import pyodbc
    except ImportError:
        print("ERRORE: pyodbc non installato. Eseguire: pip install -e \".[easy]\"", file=sys.stderr)
        sys.exit(1)

    table_upper = table_name.upper()

    # Connessione in sola lettura — nessuna scrittura verso Easy
    with pyodbc.connect(connection_string, autocommit=True, readonly=True) as conn:
        cursor = conn.cursor()

        # ─── Colonne ──────────────────────────────────────────────────────────
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, table_upper)

        rows = cursor.fetchall()
        if not rows:
            # Prova senza filtro case-sensitive (SQL Server di default case-insensitive)
            cursor.execute("""
                SELECT
                    COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_DEFAULT, ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE UPPER(TABLE_NAME) = ?
                ORDER BY ORDINAL_POSITION
            """, table_upper)
            rows = cursor.fetchall()

        if not rows:
            print(f"ATTENZIONE: tabella '{table_name}' non trovata o senza colonne in INFORMATION_SCHEMA.", file=sys.stderr)

        columns = []
        for row in rows:
            col: dict = {
                "name": row.COLUMN_NAME,
                "data_type": row.DATA_TYPE,
                "nullable": row.IS_NULLABLE == "YES",
                "ordinal_position": row.ORDINAL_POSITION,
            }
            if row.CHARACTER_MAXIMUM_LENGTH is not None:
                col["max_length"] = row.CHARACTER_MAXIMUM_LENGTH
            if row.NUMERIC_PRECISION is not None:
                col["numeric_precision"] = row.NUMERIC_PRECISION
            if row.NUMERIC_SCALE is not None:
                col["numeric_scale"] = row.NUMERIC_SCALE
            if row.COLUMN_DEFAULT is not None:
                col["default"] = row.COLUMN_DEFAULT.strip("()' ") if row.COLUMN_DEFAULT else None
            columns.append(col)

        # ─── Chiavi primarie ──────────────────────────────────────────────────
        cursor.execute("""
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
              ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
              AND UPPER(kcu.TABLE_NAME) = ?
            ORDER BY kcu.ORDINAL_POSITION
        """, table_upper)

        pk_rows = cursor.fetchall()
        primary_keys = [r.COLUMN_NAME for r in pk_rows]

        # Arricchisce le colonne con il flag pk
        pk_set = set(primary_keys)
        for col in columns:
            col["primary_key"] = col["name"] in pk_set

    return {
        "table_name": table_upper,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "source_system": "Easy (EasyJob SQL Server — ELFESQL)",
        "access_mode": "read-only",
        "primary_keys": primary_keys,
        "columns": columns,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Easy Schema Explorer — estrae schema tabella in JSON (read-only)"
    )
    parser.add_argument(
        "--table", required=True,
        help="Nome della tabella Easy da ispezionare (es. ANACLI, V_TORDCLI)"
    )
    parser.add_argument(
        "--out", default=None,
        help=(
            "Path di output del file JSON. "
            "Default: docs/integrations/easy/catalog/<TABLE_NAME>.json"
        )
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="Stampa il JSON su stdout invece di salvare su file"
    )
    args = parser.parse_args()

    try:
        conn_str = _get_connection_string()
    except RuntimeError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connessione a Easy... tabella: {args.table.upper()}", file=sys.stderr)
    schema = explore_table(args.table, conn_str)

    json_output = json.dumps(schema, indent=2, ensure_ascii=False)

    if args.stdout:
        print(json_output)
        return

    if args.out:
        out_path = Path(args.out)
    else:
        _DEFAULT_CATALOG_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _DEFAULT_CATALOG_DIR / f"{args.table.upper()}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json_output, encoding="utf-8")
    print(f"Schema salvato: {out_path}", file=sys.stderr)
    print(f"Colonne trovate: {len(schema['columns'])}", file=sys.stderr)
    if schema["primary_keys"]:
        print(f"Primary keys:   {', '.join(schema['primary_keys'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
