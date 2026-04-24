#!/usr/bin/env python3
"""Build graph model from phone number interactions."""

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_TSV = PROJECT_ROOT / "data/outputs/sample-bill.tsv"
DEFAULT_OUTPUT_TXT = PROJECT_ROOT / "data/outputs/adjacency_matrix.txt"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "data/outputs/adjacency_matrix.csv"


def load_tsv_data(filepath):
    """
    Load interaction data from TSV file.

    Args:
        filepath: Path to TSV file with columns: date, time, source, target, duration_volume

    Returns:
        List of (source, target) tuples
    """
    interactions = []

    with Path(filepath).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            source = row["source"].strip()
            target = row["target"].strip()

            # Skip self-loops and N/A values
            if source == target or source == "N/A" or target == "N/A":
                continue

            interactions.append((source, target))

    return interactions


def build_unique_numbers(interactions):
    """
    Extract unique phone numbers and create mappings.

    Args:
        interactions: List of (source, target) tuples

    Returns:
        Tuple of (unique_numbers_list, phone_to_index, index_to_phone)
    """
    unique_numbers = set()

    for source, target in interactions:
        unique_numbers.add(source)
        unique_numbers.add(target)

    # Sort alphabetically/numerically
    unique_numbers = sorted(list(unique_numbers))

    # Create mappings
    phone_to_index = {phone: idx for idx, phone in enumerate(unique_numbers)}
    index_to_phone = {idx: phone for idx, phone in enumerate(unique_numbers)}

    return unique_numbers, phone_to_index, index_to_phone


def build_adjacency_matrix(interactions, phone_to_index, num_phones):
    """
    Build adjacency matrix from interactions.

    Args:
        interactions: List of (source, target) tuples
        phone_to_index: Dict mapping phone number to index
        num_phones: Total number of unique phones

    Returns:
        2D list (matrix) where matrix[i][j] = count of calls from phone i to phone j
    """
    # Initialize matrix with zeros
    matrix = [[0 for _ in range(num_phones)] for _ in range(num_phones)]

    # Count interactions
    for source, target in interactions:
        source_idx = phone_to_index[source]
        target_idx = phone_to_index[target]
        matrix[source_idx][target_idx] += 1

    return matrix


def format_sparse_list(matrix, index_to_phone):
    """
    Format matrix as sparse list (only non-zero interactions).

    Args:
        matrix: Adjacency matrix
        index_to_phone: Dict mapping index to phone number

    Returns:
        String with sparse list format
    """
    lines = []
    lines.append("Non-zero interactions (sparse format):")
    lines.append("=" * 60)

    for i, row in enumerate(matrix):
        for j, count in enumerate(row):
            if count > 0:
                source_phone = index_to_phone[i]
                target_phone = index_to_phone[j]
                lines.append(
                    f"  [{i:2d}] {source_phone} → [{j:2d}] {target_phone}: {count:3d} calls"
                )

    return "\n".join(lines)


def format_full_grid(matrix, index_to_phone):
    """
    Format matrix as full grid with legend.

    Args:
        matrix: Adjacency matrix
        index_to_phone: Dict mapping index to phone number

    Returns:
        String with full grid format (shows '-' for zeros)
    """
    lines = []
    num_phones = len(matrix)

    lines.append("PHONE NUMBER INTERACTION GRAPH")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total unique numbers: {num_phones}")

    # Count total interactions
    total_interactions = sum(sum(row) for row in matrix)
    lines.append(f"Total interactions: {total_interactions}")
    lines.append("Graph type: Directed (no self-loops)")
    lines.append("")

    # Legend
    lines.append("Legend (Index → Phone Number):")
    lines.append("-" * 40)
    for idx, phone in index_to_phone.items():
        lines.append(f"  [{idx:2d}] {phone}")
    lines.append("")

    # Matrix header
    lines.append("Adjacency Matrix:")
    lines.append("-" * 80)
    lines.append("Matrix[i][j] = number of calls from phone i to phone j")
    lines.append("'-' indicates zero interactions")
    lines.append("")

    # Column headers (showing indices)
    col_width = 4
    header = "     "  # Space for row labels
    for j in range(num_phones):
        header += f"[{j:2d}]".rjust(col_width)
    lines.append(header)
    lines.append("     " + "-" * (col_width * num_phones))

    # Matrix rows
    for i, row in enumerate(matrix):
        row_str = f"[{i:2d}] "
        for count in row:
            if count == 0:
                row_str += "  - ".rjust(col_width)
            else:
                row_str += f"{count:3d}".rjust(col_width)
        lines.append(row_str)

    return "\n".join(lines)


def save_matrix_txt(matrix, index_to_phone, filepath):
    """
    Save full grid ASCII art to text file.

    Args:
        matrix: Adjacency matrix
        index_to_phone: Dict mapping index to phone number
        filepath: Output file path
    """
    content = format_full_grid(matrix, index_to_phone)

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as f:
        f.write(content)


def save_matrix_csv(matrix, index_to_phone, filepath):
    """
    Save full adjacency matrix as CSV.

    Args:
        matrix: Adjacency matrix
        index_to_phone: Dict mapping index to phone number
        filepath: Output file path
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row: empty corner cell + phone numbers
        header = [""] + [index_to_phone[i] for i in range(len(matrix))]
        writer.writerow(header)

        # Data rows: phone number + counts
        for i, row in enumerate(matrix):
            row_data = [index_to_phone[i]] + row
            writer.writerow(row_data)


def print_statistics(matrix, index_to_phone):
    """
    Print summary statistics to console.

    Args:
        matrix: Adjacency matrix
        index_to_phone: Dict mapping index to phone number
    """
    num_phones = len(matrix)
    total_interactions = sum(sum(row) for row in matrix)

    # Count non-zero interactions
    non_zero_count = sum(1 for row in matrix for count in row if count > 0)

    # Find most active caller (most outgoing calls)
    outgoing_counts = [(i, sum(row)) for i, row in enumerate(matrix)]
    outgoing_counts.sort(key=lambda x: x[1], reverse=True)

    # Find most called number (most incoming calls)
    incoming_counts = [
        (j, sum(matrix[i][j] for i in range(num_phones))) for j in range(num_phones)
    ]
    incoming_counts.sort(key=lambda x: x[1], reverse=True)

    # Find top connections
    connections = []
    for i, row in enumerate(matrix):
        for j, count in enumerate(row):
            if count > 0:
                connections.append((i, j, count))
    connections.sort(key=lambda x: x[2], reverse=True)

    print("\n" + "=" * 80)
    print("GRAPH STATISTICS")
    print("=" * 80)
    print(f"Total unique phone numbers: {num_phones}")
    print(f"Total interactions: {total_interactions}")
    print(f"Non-zero connections: {non_zero_count}")
    print(
        f"Sparsity: {non_zero_count}/{num_phones * num_phones} = {non_zero_count / (num_phones * num_phones) * 100:.2f}%"
    )

    print(f"\nTop 5 Most Active Callers (outgoing):")
    for idx, (phone_idx, count) in enumerate(outgoing_counts[:5]):
        print(
            f"  {idx + 1}. [{phone_idx:2d}] {index_to_phone[phone_idx]}: {count} calls"
        )

    print(f"\nTop 5 Most Called Numbers (incoming):")
    for idx, (phone_idx, count) in enumerate(incoming_counts[:5]):
        print(
            f"  {idx + 1}. [{phone_idx:2d}] {index_to_phone[phone_idx]}: {count} calls"
        )

    print(f"\nTop 10 Most Frequent Connections:")
    for idx, (source_idx, target_idx, count) in enumerate(connections[:10]):
        source_phone = index_to_phone[source_idx]
        target_phone = index_to_phone[target_idx]
        print(
            f"  {idx + 1}. [{source_idx:2d}] {source_phone} → [{target_idx:2d}] {target_phone}: {count} calls"
        )

    print("=" * 80)


def main():
    """Main execution function."""
    # File paths
    input_tsv = DEFAULT_INPUT_TSV
    output_txt = DEFAULT_OUTPUT_TXT
    output_csv = DEFAULT_OUTPUT_CSV

    print(f"Loading data from {input_tsv}")
    interactions = load_tsv_data(input_tsv)
    print(f"Found {len(interactions)} interactions (excluding self-loops)")

    print("\nBuilding unique phone numbers list...")
    unique_numbers, phone_to_index, index_to_phone = build_unique_numbers(interactions)
    print(f"Unique phone numbers: {len(unique_numbers)}")

    print(
        f"\nBuilding adjacency matrix ({len(unique_numbers)}x{len(unique_numbers)})..."
    )
    matrix = build_adjacency_matrix(interactions, phone_to_index, len(unique_numbers))

    # Print statistics
    print_statistics(matrix, index_to_phone)

    # Save outputs
    print(f"\nSaving outputs...")
    print(f"  Writing ASCII visualization to {output_txt}")
    save_matrix_txt(matrix, index_to_phone, output_txt)

    print(f"  Writing CSV matrix to {output_csv}")
    save_matrix_csv(matrix, index_to_phone, output_csv)

    # Print sparse list to console
    print("\n")
    print(format_sparse_list(matrix, index_to_phone))

    print(f"\n{'=' * 80}")
    print("FILES SAVED:")
    print(f"  - {output_txt} (ASCII visualization with full grid)")
    print(f"  - {output_csv} (Full matrix CSV)")
    print("=" * 80)


if __name__ == "__main__":
    main()
