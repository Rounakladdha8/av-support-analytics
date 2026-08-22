"""
04_build_db_and_run_sql.py

Loads the cleaned CSVs into a SQLite database using sql/01_schema.sql,
then runs sql/02_validation_reconciliation.sql query-by-query and prints
+ saves the results. This makes the SQL layer of the project runnable end
to end rather than just narrative.

Run:
    python3 04_build_db_and_run_sql.py
"""

import sqlite3
import pandas as pd
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE / "data" / "clean"
SQL_DIR = BASE / "sql"
DOCS_DIR = BASE / "docs"
DB_PATH = CLEAN_DIR / "support_analytics.db"


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)

    schema_sql = (SQL_DIR / "01_schema.sql").read_text()
    conn.executescript(schema_sql)

    rides = pd.read_csv(CLEAN_DIR / "clean_rides.csv")
    tickets = pd.read_csv(CLEAN_DIR / "support_tickets.csv")

    rides.to_sql("clean_rides", conn, if_exists="append", index=False)
    tickets.to_sql("support_tickets", conn, if_exists="append", index=False)
    conn.commit()

    # Split the validation SQL file into individual statements (by ';')
    raw_sql = (SQL_DIR / "02_validation_reconciliation.sql").read_text()
    statements = [s.strip() for s in raw_sql.split(";") if s.strip() and not s.strip().startswith("--")]

    # Re-attach leading comments to each statement for labeling
    blocks = re.split(r"(?=-- \d\.)", raw_sql)
    blocks = [b.strip() for b in blocks if b.strip()]

    output_lines = ["# SQL Validation & Reconciliation Results\n"]
    for block in blocks:
        lines = block.split("\n")
        title = lines[0].lstrip("- ").strip()
        body = "\n".join(l for l in lines[1:] if not l.strip().startswith("--")).strip()
        sub_queries = [q.strip() for q in body.split(";") if q.strip()]
        if not sub_queries:
            continue
        output_lines.append(f"## {title}")
        for qi, query in enumerate(sub_queries, 1):
            try:
                result = pd.read_sql_query(query, conn)
            except Exception as e:
                result = pd.DataFrame({"error": [str(e)]})
            label = f"### Query {qi}" if len(sub_queries) > 1 else ""
            if label:
                output_lines.append(label)
            output_lines.append("```")
            output_lines.append(query.strip())
            output_lines.append("```")
            output_lines.append("")
            output_lines.append(result.to_markdown(index=False) if not result.empty else "_(no rows returned)_")
            output_lines.append("")
            print(f"\n=== {title} (query {qi}) ===")
            print(result.to_string(index=False))

    (DOCS_DIR / "sql_validation_results.md").write_text("\n".join(output_lines) + "\n")
    conn.close()
    print(f"\nDB built at {DB_PATH}")
    print(f"Results written to {DOCS_DIR / 'sql_validation_results.md'}")


if __name__ == "__main__":
    main()
