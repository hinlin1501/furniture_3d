"""Dump real DB structure to schema_report.md (read-only). Run from backend/:
    py scripts\\inspect_schema.py
Reads DATABASE_URL from the environment or from .env."""

import os
import re
from pathlib import Path

from sqlalchemy import create_engine, text


def load_url() -> str:
    url = os.environ.get("DATABASE_URL")
    env = Path(".env")
    if not url and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*DATABASE_URL\s*=\s*(.+?)\s*$", line)
            if m:
                url = m.group(1).strip("'\"")
    if not url:
        raise SystemExit("DATABASE_URL not found in environment or .env")
    return url


SYS = "('pg_catalog','information_schema','pg_toast')"

COLUMNS = text(f"""
SELECT table_schema, table_name, column_name,
       CASE WHEN data_type='USER-DEFINED' THEN udt_name
            WHEN data_type='ARRAY' THEN udt_name ELSE data_type END AS dtype,
       character_maximum_length AS len, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema NOT IN {SYS}
ORDER BY table_schema, table_name, ordinal_position""")

CONSTRAINTS = text(f"""
SELECT n.nspname AS sch, c.relname AS tbl, con.conname, pg_get_constraintdef(con.oid) AS def
FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname NOT IN {SYS} ORDER BY 1, 2, con.contype, 3""")

INDEXES = text(f"SELECT indexdef FROM pg_indexes WHERE schemaname NOT IN {SYS} ORDER BY schemaname, tablename, indexname")

ENUMS = text("""
SELECT n.nspname, t.typname, string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder)
FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid JOIN pg_namespace n ON n.oid = t.typnamespace
GROUP BY 1, 2 ORDER BY 1, 2""")

TABLES = text(f"""
SELECT table_schema, table_name FROM information_schema.tables
WHERE table_schema NOT IN {SYS} AND table_type='BASE TABLE' ORDER BY 1, 2""")


def main() -> None:
    out = ["# Schema report\n", "## Enum types\n"]
    with create_engine(load_url()).connect() as c:
        for r in c.execute(ENUMS):
            out.append(f"- `{r[0]}.{r[1]}`: {r[2]}")
        out.append("\n## Row counts\n")
        for sch, tbl in c.execute(TABLES).all():
            n = c.execute(text(f'SELECT count(*) FROM "{sch}"."{tbl}"')).scalar()
            out.append(f"- {sch}.{tbl}: {n}")
        out.append("\n## Columns\n")
        cur = None
        for r in c.execute(COLUMNS):
            key = f"{r.table_schema}.{r.table_name}"
            if key != cur:
                out.append(f"\n### {key}\n\n| column | type | null | default |\n|---|---|---|---|")
                cur = key
            t = f"{r.dtype}({r.len})" if r.len else r.dtype
            out.append(f"| {r.column_name} | {t} | {r.is_nullable} | {r.column_default or ''} |")
        out.append("\n## Constraints\n")
        for r in c.execute(CONSTRAINTS):
            out.append(f"- `{r.sch}.{r.tbl}` **{r.conname}**: {getattr(r, 'def')}")
        out.append("\n## Indexes\n")
        for r in c.execute(INDEXES):
            out.append(f"- {r[0]}")
    Path("schema_report.md").write_text("\n".join(out), encoding="utf-8")
    print("Wrote schema_report.md")


if __name__ == "__main__":
    main()