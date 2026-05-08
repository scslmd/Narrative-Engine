#!/usr/bin/env python3
"""Generate Database Schema.md from the current sqlite schema definitions.

Usage:
    python scripts/generate_schema_doc.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from app.persistence.sqlite import OPERATIONS_SCHEMA, PROJECT_SCHEMA


def parse_tables(schema_str: str) -> list[tuple[str, list[str]]]:
    """Parse a schema string into (table_name, column_lines) tuples."""
    tables = []
    current = None
    lines = []
    for raw in schema_str.split('\n'):
        s = raw.strip()
        if s.upper().startswith('CREATE TABLE'):
            if current:
                tables.append((current, lines))
            m = re.search(r'TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[\]]?(\w+)', s, re.I)
            current = m.group(1) if m else None
            lines = []
        elif current:
            if s.endswith(');'):
                tables.append((current, lines))
                current = None
                lines = []
            else:
                lines.append(s.rstrip(','))
    if current and lines:
        tables.append((current, lines))
    return tables


def parse_column(line: str) -> dict | None:
    """Parse a column definition line into structured data."""
    m = re.match(r'(`?(\w+)`?)\s+(.+)', line)
    if not m:
        return None
    name = m.group(2)
    rest = m.group(3).strip()

    type_m = re.match(r'((?:[A-Z_]+(?:\s*\([^)]*\))?\s*)+)', rest)
    col_type = type_m.group(1).strip() if type_m else rest
    constraint_part = rest[type_m.end():].strip() if type_m else ''

    notes = []
    if 'PRIMARY KEY' in line:
        notes.append('PK')
    if 'AUTOINCREMENT' in line:
        notes.append('autoincrement')
    if 'UNIQUE' in constraint_part:
        notes.append('unique')
    if 'NOT NULL' in line:
        notes.append('not null')

    dm = re.search(r"DEFAULT\s+'([^']*)'", line, re.I)
    if dm:
        notes.append(f"default: '{dm.group(1)}'")
    else:
        dm2 = re.search(r'DEFAULT\s+(\S+)', line, re.I)
        if dm2:
            notes.append(f"default: {dm2.group(1)}")

    return {
        'name': name,
        'type': col_type,
        'notes': ', '.join(notes) if notes else '-',
    }


def extract_fks(lines: list[str]) -> list[str]:
    fks = []
    for line in lines:
        if 'FOREIGN KEY' in line:
            fks.append(line)
    return fks


def to_md(tables: list[tuple[str, list[str]]], db_label: str) -> str:
    md = f"### {db_label}\n\n{len(tables)} tables\n\n"
    for name, cols in tables:
        fks = extract_fks(cols)
        non_fk = [c for c in cols if 'FOREIGN KEY' not in c]

        md += f"#### `{name}`\n\n"
        md += "| Column | Type | Notes |\n|--------|------|-------|\n"
        for c in non_fk:
            parsed = parse_column(c)
            if parsed:
                md += f"| `{parsed['name']}` | `{parsed['type']}` | {parsed['notes']} |\n"

        if fks:
            md += "\n**Foreign Keys:**\n\n"
            for fk in fks:
                md += f"- {fk}\n"

        md += "\n"
    return md


def main():
    ops = parse_tables(OPERATIONS_SCHEMA)
    proj = parse_tables(PROJECT_SCHEMA)

    md = "# Narrative Engine Database Schema\n\n"
    md += "Auto-generated schema reference. Extracted from `app/persistence/sqlite.py`.\n\n"
    md += "**Regenerate:** `python scripts/generate_schema_doc.py`\n\n"
    md += "## Overview\n\n"
    md += f"| Database | Path | Tables |\n|----------|------|--------|\n"
    md += f"| Operations DB | `data/state/narrative_ops.db` | {len(ops)} |\n"
    md += f"| Project DB | `data/projects/{{project_id}}/bible.db` | {len(proj)} |\n\n"
    md += "Operations DB is created on first startup via `ensure_operations_db()`. "
    md += "Project DBs are created per-project.\n\n"
    md += "---\n\n"
    md += to_md(ops, "Operations Database")
    md += "---\n\n"
    md += to_md(proj, "Project Database (bible.db)")

    out = root / "docs" / "Database Schema.md"
    out.write_text(md, encoding='utf-8')
    print(f"Wrote {out.relative_to(root)}")
    print(f"  Operations DB: {len(ops)} tables")
    print(f"  Project DB: {len(proj)} tables")


if __name__ == '__main__':
    main()
