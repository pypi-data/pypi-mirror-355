import pandas as pd
import pandas.testing as pdt
import pytest

from src.core.stats_processor import apply_expr, build_header


def test_build_header_no_skip():
    """
    When skip_rows is zero, column names should become string indices and data preserved.
    """
    # Arrange: create a simple DataFrame
    df = pd.DataFrame([[1, 2], [3, 4]])

    # Act: build header with skip_rows=0
    result = build_header(df, skip_rows=0)

    # Assert: columns are '0', '1' and first cell remains 1
    assert list(result.columns) == ["0", "1"]
    assert result.iloc[0, 0] == 1


def test_build_header_with_skip():
    """
    When skip_rows is positive, the specified row values become new headers.
    """
    # Arrange: DataFrame with header row 'a','b' at index 0 and data at index 1
    df = pd.DataFrame([["a", "b"], [1, 2], [5, 6]])

    # Act: skip the first row to use as header
    result = build_header(df, skip_rows=1)

    # Assert: columns are ['a','b'] and first data row is preserved
    assert list(result.columns) == ["a", "b"]
    assert result.iloc[0].tolist() == [1, 2]


def test_build_header_negative_skip_treated_as_zero():
    """
    Negative skip_rows values are clamped to zero, so behave like no skip.
    """
    # Arrange: simple DataFrame
    df = pd.DataFrame([["x", "y"], ["u", "v"]])

    # Act: call with skip_rows < 0
    result = build_header(df, skip_rows=-5)

    # Assert: column names are '0','1' and data unchanged
    assert list(result.columns) == ["0", "1"]
    assert result.iloc[1, 1] == "v"


def test_build_header_skip_equal_length_results_empty():
    """
    skip_rows equal to number of rows uses last row as header and results in empty data.
    """
    # Arrange: DataFrame with two rows
    df = pd.DataFrame([["h1", "h2"], ["d1", "d2"]])

    # Act: skip both rows (skip_rows=2)
    result = build_header(df, skip_rows=2)

    # Assert: header names from second row and no data rows
    assert list(result.columns) == ["d1", "d2"]
    assert result.empty


def test_apply_expr_filters_correctly():
    """
    A non-empty expression should filter rows according to pandas query syntax.
    """
    # Arrange: DataFrame with numeric columns
    df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})

    # Act: apply expression to select a>2 and b<8
    result = apply_expr(df, expr="a > 2 and b < 8")
    expected = pd.DataFrame({"a": [3], "b": [7]})

    # Assert: resulting DataFrame matches expected
    pdt.assert_frame_equal(result, expected)


def test_apply_expr_empty_and_whitespace_returns_copy():
    """
    An empty or whitespace-only expression returns a fresh copy with reset index.
    """
    # Arrange: original DataFrame
    df = pd.DataFrame({"x": [10, 20]})

    # Act: call with empty string
    out1 = apply_expr(df, expr="")
    # Act: call with whitespace-only string
    out2 = apply_expr(df, expr="   ")

    # Assert: both results equal original data, but are new objects
    pdt.assert_frame_equal(out1, df)
    pdt.assert_frame_equal(out2, df)
    assert out1 is not df
    assert out2 is not df


def test_apply_expr_invalid_expression_raises():
    """
    An invalid query expression should raise a Pandas error.
    """
    # Arrange: simple DataFrame
    df = pd.DataFrame({"a": [1, 2]})

    # Act & Assert: invalid syntax raises a ValueError or ParsingError
    with pytest.raises(Exception):
        apply_expr(df, expr="a >> 1")
