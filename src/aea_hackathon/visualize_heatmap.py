"""Visualize phone number adjacency matrix as an interactive heatmap using Altair."""

import pandas as pd
import altair as alt
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_CSV = PROJECT_ROOT / "data/outputs/adjacency_matrix.csv"
DEFAULT_OUTPUT_HTML = PROJECT_ROOT / "data/outputs/heatmap.html"


def load_adjacency_matrix(csv_path):
    """
    Load adjacency matrix from CSV file.

    Args:
        csv_path: Path to CSV file with adjacency matrix

    Returns:
        pandas DataFrame with phone numbers as index and columns
    """
    # Read CSV with dtype=str to preserve phone numbers as strings
    df = pd.read_csv(csv_path, index_col=0, dtype=str)

    # Convert index and columns to strings
    df.index = df.index.astype(str)
    df.columns = df.columns.astype(str)

    # Convert values to integers
    df = df.astype(int)

    return df


def matrix_to_long_format(df, include_zeros=False):
    """
    Convert wide adjacency matrix to long format for Altair.

    Args:
        df: Wide format DataFrame (phone x phone matrix)
        include_zeros: If True, include zero-count interactions

    Returns:
        Long format DataFrame with columns: source, target, count, source_idx, target_idx
    """
    # Create phone to index mapping (sorted alphabetically)
    phones = sorted(df.index.tolist())
    phone_to_idx = {phone: idx for idx, phone in enumerate(phones)}

    # Convert to long format
    records = []
    for source_phone in df.index:
        for target_phone in df.columns:
            count = int(df.loc[source_phone, target_phone])

            # Skip zeros if requested
            if not include_zeros and count == 0:
                continue

            records.append(
                {
                    "source": source_phone,
                    "target": target_phone,
                    "count": count,
                    "source_idx": phone_to_idx[source_phone],
                    "target_idx": phone_to_idx[target_phone],
                }
            )

    df_long = pd.DataFrame(records)
    return df_long


def create_heatmap(df_long, width=800, height=800):
    """
    Create interactive heatmap using Altair.

    Args:
        df_long: Long format DataFrame with columns: source, target, count, source_idx, target_idx
        width: Chart width in pixels
        height: Chart height in pixels

    Returns:
        altair.Chart object
    """
    # Create the heatmap
    chart = (
        alt.Chart(df_long)
        .mark_rect()
        .encode(
            x=alt.X(
                "target_idx:O", title="Target Phone Index", axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "source_idx:O", title="Source Phone Index", axis=alt.Axis(labelAngle=0)
            ),
            color=alt.Color(
                "count:Q", scale=alt.Scale(scheme="blues"), title="Call Count"
            ),
            tooltip=[
                alt.Tooltip("source_idx:O", title="Source Index"),
                alt.Tooltip("source:N", title="Source Phone"),
                alt.Tooltip("target_idx:O", title="Target Index"),
                alt.Tooltip("target:N", title="Target Phone"),
                alt.Tooltip("count:Q", title="Calls"),
            ],
        )
        .properties(
            width=width,
            height=height,
            title="Phone Number Interaction Heatmap (Non-Zero Interactions Only)",
        )
        .configure_axis(labelFontSize=10, titleFontSize=12)
        .configure_title(fontSize=16, anchor="start")
    )

    return chart


def save_heatmap(chart, output_path):
    """
    Save heatmap to HTML file.

    Args:
        chart: Altair chart object
        output_path: Path to save HTML file
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save as HTML
    chart.save(output_path)
    print(f"Heatmap saved to {output_path}")


def main():
    """Main execution: load, transform, visualize, and save."""
    print("Loading adjacency matrix...")
    csv_path = DEFAULT_INPUT_CSV
    df = load_adjacency_matrix(csv_path)
    print(f"Loaded {df.shape[0]}x{df.shape[1]} matrix")

    print("\nTransforming to long format (non-zero only)...")
    df_long = matrix_to_long_format(df, include_zeros=False)
    print(f"Found {len(df_long)} non-zero interactions")

    print("\nCreating heatmap...")
    chart = create_heatmap(df_long, width=800, height=800)

    print("\nSaving heatmap...")
    output_path = DEFAULT_OUTPUT_HTML
    save_heatmap(chart, output_path)

    print("\n" + "=" * 60)
    print("HEATMAP GENERATION COMPLETE")
    print("=" * 60)
    print(f"Visualization: {output_path}")
    print(f"Total interactions visualized: {len(df_long)}")
    print(f"Dimensions: 800x800 pixels")
    print(f"Color scheme: Sequential (blues)")
    print("=" * 60)


if __name__ == "__main__":
    main()
