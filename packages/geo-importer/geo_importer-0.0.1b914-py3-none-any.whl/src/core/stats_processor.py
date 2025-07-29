"""
Pure-Pandas helper functions for statistics tables (**no Qt imports**),
hence 100 % unit-testable.

Functions
---------
build_header(df, skip_rows)
    Promote the *(skip_rows – 1)*-th row to column headers.
apply_expr(df, expr)
    Apply a ``DataFrame.query`` expression.
"""

from __future__ import annotations

import pandas as pd


# ======================================================================= #
#  Header Construction
# ======================================================================= #
def build_header(df: pd.DataFrame, skip_rows: int = 0) -> pd.DataFrame:
    """
    Replace column names by the values of row *(skip_rows – 1)*.

    If skip_rows is 0, the function simply ensures that the column labels
    are numeric and represented as strings (e.g., "0", "1", ...).
    """
    # Clamp skip_rows into valid range [0, len(df)]
    skip_rows = max(0, min(skip_rows, len(df)))

    # If no skipping is requested, just rename columns to "0", "1", ...
    if skip_rows == 0:
        # Copy the DataFrame to avoid mutating the original
        out = df.copy()
        # Assign column indices as strings
        out.columns = [str(i) for i in range(out.shape[1])]
        return out

    # Otherwise, use the values in the row at index skip_rows - 1 as headers
    # Convert each cell in that header row to string for consistency
    header_row = df.iloc[skip_rows - 1].astype(str).tolist()

    # Slice off all rows before the data (including the header row)
    out = df.iloc[skip_rows:].reset_index(drop=True).copy()
    # Assign the header row values as new column names
    out.columns = header_row
    return out


# ======================================================================= #
#  Expression Application
# ======================================================================= #
def apply_expr(df: pd.DataFrame, expr: str = "") -> pd.DataFrame:
    """
    Apply a **pandas query** expression (string) to filter rows.

    An empty string means *no filtering*. The function always returns
    a fresh copy so callers can safely modify the result in-place.
    """
    # Trim whitespace from the expression
    expr = expr.strip()

    # If the expression is empty, simply return a copy of the DataFrame
    if not expr:
        # Reset index so that the returned DataFrame has a clean index
        return df.copy().reset_index(drop=True)

    # Use pandas' query method with the Python engine to evaluate the expression
    # Reset index afterward to provide a contiguous integer index
    return df.query(expr, engine="python").reset_index(drop=True)
