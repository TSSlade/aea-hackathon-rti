#!/usr/bin/env python3
"""Extract Date, Time, Dialled Number and Duration/Volume data from PDF to TSV."""
# This is version 1


import pdfplumber
import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PDF = PROJECT_ROOT / "data/inputs/sample-bill-mock-nums.pdf"
DEFAULT_OUTPUT_TSV = PROJECT_ROOT / "data/outputs/sample-bill.tsv"


def print_sample_rows(rows, table_name, num_samples=3):
    """Print first and last N rows for verification."""
    print(f"\n{table_name} - Sample rows:")
    print(f"  First {num_samples} rows:")
    for i, row in enumerate(rows[:num_samples]):
        print(f"    {i + 1}: {row}")

    if len(rows) > num_samples * 2:
        print(f"  Last {num_samples} rows:")
        for i, row in enumerate(rows[-num_samples:]):
            print(f"    {len(rows) - num_samples + i + 1}: {row}")


def extract_table_data(data_table, table_idx, is_left_table):
    """
    Extract data from a single table.

    Args:
        data_table: The table data from pdfplumber
        table_idx: Table index for logging
        is_left_table: True if this is the left table (skip Safaricom row)

    Returns:
        List of rows with [date, time, target, duration_volume]
    """
    # Find column indices
    header_row = data_table[0]
    date_idx = None
    time_idx = None
    dialled_idx = None
    duration_idx = None

    for idx, col in enumerate(header_row):
        col_str = str(col) if col else ""
        if "Date" in col_str:
            date_idx = idx
        if "Time" in col_str:
            time_idx = idx
        if "Dialled Number" in col_str:
            dialled_idx = idx
        if "Duration" in col_str and "Volume" in col_str:
            duration_idx = idx

    if any(x is None for x in [date_idx, time_idx, dialled_idx, duration_idx]):
        print(f"Skipping table {table_idx}: could not find required columns")
        print(
            f"  Date: {date_idx}, Time: {time_idx}, Dialled: {dialled_idx}, Duration: {duration_idx}"
        )
        return []

    print(
        f"Table {table_idx} ({'LEFT' if is_left_table else 'RIGHT'}): Date={date_idx}, Time={time_idx}, Dialled={dialled_idx}, Duration={duration_idx}"
    )

    rows = []

    # Process data rows (skip header)
    for row_idx, row in enumerate(data_table[1:], start=1):
        if len(row) <= max(date_idx, time_idx, dialled_idx, duration_idx):
            continue

        date_cell = row[date_idx] if row[date_idx] else ""
        time_cell = row[time_idx] if row[time_idx] else ""
        dialled_cell = row[dialled_idx] if row[dialled_idx] else ""
        duration_cell = row[duration_idx] if row[duration_idx] else ""

        # Skip "Safaricom Subscriber" row (only in left table)
        if is_left_table and (
            "Safaricom" in str(dialled_cell)
            or "Subscriber" in str(dialled_cell)
            or "Peak" in str(dialled_cell)
            or "scriber" in str(dialled_cell)
        ):
            print(f"  Skipping Safaricom row in left table")
            continue

        # Split multi-line cells by newlines
        date_values = str(date_cell).strip().split("\n") if date_cell else []
        time_values = str(time_cell).strip().split("\n") if time_cell else []
        dialled_values = str(dialled_cell).strip().split("\n") if dialled_cell else []
        duration_values = (
            str(duration_cell).strip().split("\n") if duration_cell else []
        )

        # Match up the values (they should have equal counts)
        max_len = max(
            len(date_values),
            len(time_values),
            len(dialled_values),
            len(duration_values),
        )

        for i in range(max_len):
            date_val = date_values[i].strip() if i < len(date_values) else "N/A"
            time_val = time_values[i].strip() if i < len(time_values) else "N/A"
            dialled = dialled_values[i].strip() if i < len(dialled_values) else "N/A"
            duration = duration_values[i].strip() if i < len(duration_values) else "N/A"

            # Handle empty values
            if not date_val:
                date_val = "N/A"
            if not time_val:
                time_val = "N/A"
            if not dialled:
                dialled = "N/A"
            if not duration:
                duration = "N/A"

            # Skip completely empty rows
            if all(v == "N/A" for v in [date_val, time_val, dialled, duration]):
                continue

            rows.append([date_val, time_val, dialled, duration])

    return rows


def extract_pdf_to_tsv(pdf_path, output_path, source_value="<callers-number>"):
    """
    Extract table data from PDF and save as TSV.

    Args:
        pdf_path: Path to input PDF file
        output_path: Path to output TSV file
        source_value: Constant value for source column
    """
    # Ensure output directory exists
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Open PDF and extract tables with line-based strategy
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[0]  # Single page PDF

        # Use lines strategy which works well for this PDF
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        }

        tables = page.extract_tables(table_settings)

        if not tables:
            print("No tables found in PDF")
            sys.exit(1)

        # Find all tables with "Date" column (should be 2 side-by-side tables)
        data_tables = []
        for table in tables:
            if table and len(table) > 0:
                header_row = table[0]
                # Check if "Date" appears in any cell of first row
                if any(cell and "Date" in str(cell) for cell in header_row):
                    data_tables.append(table)

        if not data_tables:
            print("Could not find tables with 'Date' column")
            sys.exit(1)

        if len(data_tables) != 2:
            print(
                f"Warning: Expected 2 data tables (left and right), found {len(data_tables)}"
            )

        print(f"\nFound {len(data_tables)} data table(s)")

        # Process left table (first table, has Safaricom row to skip)
        left_rows = []
        if len(data_tables) >= 1:
            left_rows = extract_table_data(data_tables[0], 0, is_left_table=True)
            print(f"Extracted {len(left_rows)} rows from LEFT table")
            print_sample_rows(left_rows, "LEFT TABLE")

        # Process right table (second table, no Safaricom row)
        right_rows = []
        if len(data_tables) >= 2:
            right_rows = extract_table_data(data_tables[1], 1, is_left_table=False)
            print(f"\nExtracted {len(right_rows)} rows from RIGHT table")
            print_sample_rows(right_rows, "RIGHT TABLE")

        # Combine: left table + right table
        combined_rows = left_rows + right_rows
        print(f"\n{'=' * 60}")
        print(
            f"TOTAL: {len(combined_rows)} rows ({len(left_rows)} left + {len(right_rows)} right)"
        )
        print(f"{'=' * 60}")

        # Add source column and format for output
        # Output format: date, time, source, target, duration_volume
        output_rows = []
        for row in combined_rows:
            date_val, time_val, target, duration = row
            output_rows.append([date_val, time_val, source_value, target, duration])

        # Write TSV
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            # Write header
            writer.writerow(["date", "time", "source", "target", "duration_volume"])
            # Write data rows
            writer.writerows(output_rows)

        print(f"\nWrote {len(output_rows)} rows to {output_path}")
        print("\nOutput sample:")
        print_sample_rows(output_rows, "FINAL OUTPUT")


def main() -> None:
    """Run the default extraction workflow."""
    extract_pdf_to_tsv(DEFAULT_INPUT_PDF, DEFAULT_OUTPUT_TSV)


if __name__ == "__main__":
    main()
