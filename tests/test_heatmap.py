"""Tests for heatmap visualization using TDD approach."""

import pytest
import pandas as pd
import altair as alt
from pathlib import Path

from aea_hackathon.visualize_heatmap import (
    create_heatmap,
    load_adjacency_matrix,
    matrix_to_long_format,
    save_heatmap,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data/outputs/adjacency_matrix.csv"
TEST_OUTPUT_PATH = PROJECT_ROOT / "data/outputs/test_heatmap.html"


def require_adjacency_matrix() -> None:
    """Skip tests when generated graph output is not available."""
    if not CSV_PATH.exists():
        pytest.skip("Generated adjacency matrix not found at data/outputs/adjacency_matrix.csv")


# Test 1: Load adjacency matrix from CSV
def test_load_adjacency_matrix():
    """Test that adjacency matrix loads correctly from CSV."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)

    # Check it returns a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Check dimensions (41 phones x 41 phones)
    assert df.shape == (41, 41)

    # Check that index and columns are phone numbers
    assert len(df.index) == 41
    assert len(df.columns) == 41

    # Check that <callers-number> is in the data
    assert "<callers-number>" in df.index


# Test 2: Transform matrix to long format (non-zero only)
def test_matrix_to_long_format():
    """Test transformation from wide matrix to long format."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    # Check it returns a DataFrame
    assert isinstance(df_long, pd.DataFrame)

    # Check required columns exist
    assert "source" in df_long.columns
    assert "target" in df_long.columns
    assert "count" in df_long.columns
    assert "source_idx" in df_long.columns
    assert "target_idx" in df_long.columns

    # Check that zeros are filtered out
    assert all(df_long["count"] > 0)

    # Check we have 40 non-zero interactions (from build_graph.py output)
    assert len(df_long) == 40

    # Check that indices are integers
    assert df_long["source_idx"].dtype == int
    assert df_long["target_idx"].dtype == int


# Test 3: Create basic heatmap
def test_create_heatmap():
    """Test that heatmap chart is created."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)

    # Check it returns an Altair Chart
    assert isinstance(chart, alt.Chart)

    # Check chart uses rect mark
    assert chart.mark == "rect" or "rect" in str(chart.to_dict())


# Test 4: Chart has title
def test_chart_has_title():
    """Test that chart has a descriptive title."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)
    chart_dict = chart.to_dict()

    # Check title exists
    assert "title" in chart_dict
    assert len(chart_dict["title"]) > 0


# Test 5: Chart has proper encodings
def test_chart_has_encodings():
    """Test that chart has x, y, and color encodings."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)
    chart_dict = chart.to_dict()

    # Check encodings exist
    assert "encoding" in chart_dict
    encoding = chart_dict["encoding"]

    # Check x, y, color are present
    assert "x" in encoding
    assert "y" in encoding
    assert "color" in encoding


# Test 6: Chart has tooltips
def test_chart_has_tooltips():
    """Test that chart has rich tooltips."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)
    chart_dict = chart.to_dict()

    # Check tooltip exists in encoding
    encoding = chart_dict["encoding"]
    assert "tooltip" in encoding

    # Tooltip should be a list with multiple fields
    assert isinstance(encoding["tooltip"], list)
    assert len(encoding["tooltip"]) > 0


# Test 7: Chart has appropriate dimensions
def test_chart_dimensions():
    """Test that chart has correct dimensions."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)
    chart_dict = chart.to_dict()

    # Check width and height
    assert chart_dict.get("width") == 800
    assert chart_dict.get("height") == 800


# Test 8: Save heatmap to HTML
def test_save_heatmap():
    """Test that heatmap can be saved to HTML file."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)
    chart = create_heatmap(df_long, width=800, height=800)

    save_heatmap(chart, TEST_OUTPUT_PATH)

    # Check file was created
    assert TEST_OUTPUT_PATH.exists()

    # Check file has content
    assert TEST_OUTPUT_PATH.stat().st_size > 0

    # Clean up test file
    TEST_OUTPUT_PATH.unlink()


# Test 9: Color scale is sequential
def test_color_scale_sequential():
    """Test that color scale is sequential."""
    require_adjacency_matrix()
    df = load_adjacency_matrix(CSV_PATH)
    df_long = matrix_to_long_format(df, include_zeros=False)

    chart = create_heatmap(df_long, width=800, height=800)
    chart_dict = chart.to_dict()

    # Check color encoding has a scale
    color_encoding = chart_dict["encoding"]["color"]
    assert "scale" in color_encoding

    # Check for sequential scheme
    scale = color_encoding["scale"]
    assert "scheme" in scale
