#!/usr/bin/env python3
"""Debug PDF structure."""

import pdfplumber
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = PROJECT_ROOT / "data/inputs/sample-bill-mock-nums.pdf"

with pdfplumber.open(str(PDF_PATH)) as pdf:
    page = pdf.pages[0]

    # Try multiple table extraction strategies
    print("=== Strategy 1: Lines ===")
    tables = page.extract_tables(
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
    )
    print(f"Found {len(tables)} table(s)")
    for i, table in enumerate(tables):
        print(f"\nTable {i}: {len(table)} rows, {len(table[0]) if table else 0} cols")
        if table:
            print(f"Header: {table[0]}")
            print(f"First data row: {table[1] if len(table) > 1 else 'None'}")

    print("\n=== Strategy 2: Text ===")
    tables = page.extract_tables(
        {"vertical_strategy": "text", "horizontal_strategy": "text"}
    )
    print(f"Found {len(tables)} table(s)")
    for i, table in enumerate(tables):
        print(f"\nTable {i}: {len(table)} rows, {len(table[0]) if table else 0} cols")
        if table:
            print(f"Header: {table[0]}")
            print(f"First data row: {table[1] if len(table) > 1 else 'None'}")

    print("\n=== Strategy 3: Explicit ===")
    tables = page.extract_tables(
        {
            "explicit_vertical_lines": page.curves + page.edges,
            "explicit_horizontal_lines": page.curves + page.edges,
        }
    )
    print(f"Found {len(tables)} table(s)")
    for i, table in enumerate(tables):
        print(f"\nTable {i}: {len(table)} rows, {len(table[0]) if table else 0} cols")
        if table:
            print(f"Header: {table[0]}")
            print(f"First 3 data rows:")
            for row in table[1:4]:
                print(f"  {row}")
