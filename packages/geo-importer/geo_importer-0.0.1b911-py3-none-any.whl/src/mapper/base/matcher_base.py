"""
Common base class for all matcher widgets.

Provides:
  • Qt signals `updated` / `removed`
  • `build_result()` – combines a statistics row and a geo row
  • Placeholder methods that subclasses must override
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


# ==============================================================================
#  BaseMatcher: Shared functionality for all matcher widgets
# ==============================================================================
class BaseMatcher(QWidget):
    # --------------------------------------------------------------------------
    #  Public Qt signals
    # --------------------------------------------------------------------------
    updated = Signal()  # Emitted when configuration changes
    removed = Signal()  # Emitted to request removal of this matcher

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, nr: int, stats_cols: List[str], geo_cols: List[str], parent=None) -> None:
        """
        Initialize the base matcher widget.

        Steps:
          1. Call the superclass constructor with the given parent.
          2. Store the unique identifier `nr` and lists of available statistics and geo columns.
        """
        super().__init__(parent)
        # Store identifier and column lists for use by subclasses
        self._nr = nr
        self._stats_cols = stats_cols
        self._geo_cols = geo_cols

    # --------------------------------------------------------------------------
    #  Helper routine used by subclasses
    # --------------------------------------------------------------------------
    @staticmethod
    def build_result(stats_df: pd.DataFrame, geo_df: pd.DataFrame, label: str | None = None) -> pd.DataFrame:
        """
        Combine exactly one statistics row and one geo row into a single result record.

        Steps:
          1. Reset indices on both DataFrames and make copies to avoid side effects.
          2. Rename statistics columns to have suffix `_stats`.
          3. Rename geo columns to have suffix `_geodata`.
          4. Concatenate the two side by side (axis=1).
          5. If a label is provided, append a column `matcher` with that label.
        """
        # Prepare statistics DataFrame
        st = stats_df.reset_index(drop=True).copy()
        st.columns = [f"{c}_stats" for c in st.columns]

        # Prepare geo DataFrame
        ge = geo_df.reset_index(drop=True).copy()
        ge.columns = [f"{c}_geodata" for c in ge.columns]

        # Concatenate results horizontally
        res = pd.concat([st, ge], axis=1)
        # Optionally record which matcher produced this row
        if label is not None:
            res["matcher"] = label
        return res

    # --------------------------------------------------------------------------
    #  Abstract API – SUBCLASSES MUST OVERRIDE
    # --------------------------------------------------------------------------
    def match(self, stats_df: pd.DataFrame, geo_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[List[int]], Optional[List[int]]]:
        """
        Execute the actual matching logic between statistics and geo data.

        Steps:
          1. Subclass should identify which rows from `stats_df` and `geo_df` match.
          2. Build a DataFrame of combined rows using `build_result()`.
          3. Return the combined DataFrame and lists of used row indices from both tables.
        """
        raise NotImplementedError("match() must be implemented in the subclass")

    def description(self) -> str:
        """
        Provide a brief text description of the current matcher configuration.

        Steps:
          1. Subclass should return a string summarizing which columns or criteria are used.
        """
        raise NotImplementedError("description() must be implemented in the subclass")

    # --------------------------------------------------------------------------
    #  Optional hooks – SUBCLASSES CAN OVERRIDE
    # --------------------------------------------------------------------------
    def update_stats_columns(self, cols: List[str]) -> None:
        """
        Update the list of available statistics columns.

        Steps:
          1. Replace the internal `_stats_cols` list with the new `cols`.
        """
        self._stats_cols = cols

    def update_geo_columns(self, cols: List[str]) -> None:
        """
        Update the list of available geo columns.

        Steps:
          1. Replace the internal `_geo_cols` list with the new `cols`.
        """
        self._geo_cols = cols
