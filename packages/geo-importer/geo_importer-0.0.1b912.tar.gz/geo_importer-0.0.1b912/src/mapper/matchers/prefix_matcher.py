# python/mapper/prefix_matcher.py
"""
Prefix matcher for statistics-to-geo assignments.

This class has been adapted to the structure of other matchers:
  * Direct `setupUi(self)` instead of wrapping in `self.ui` → consistent API.
  * All UI accesses go through `self.<widget>` (instead of `self.ui.<widget>`).
  * Pure formatting/name changes – logic and return values remain the same.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from src.mapper.base.matcher_base import BaseMatcher
from src.mapper.matchers.ui.prefix_matcher_ui import Ui_PrefixMatcher


# ==============================================================================
#  PrefixMatcher: Implements prefix-based matching between stats and geo data
# ==============================================================================
class PrefixMatcher(BaseMatcher, Ui_PrefixMatcher):
    """
    Matcher for prefix-based matching between statistics and geo data.

    Behavior:
      - Takes a prefix of configurable length from the selected columns.
      - Finds unique common prefixes in both tables.
      - Maps exactly one row per common prefix.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, nr: int, stats_cols: List[str], geo_cols: List[str], parent=None) -> None:
        """
        Initialize the prefix matcher widget.

        Steps:
          1. Call BaseMatcher constructor to store identifier and column lists.
          2. Call setupUi(self) to build UI controls from .ui file.
          3. Populate the Excel and geo combo boxes with provided column lists.
          4. Configure the spin box `spinLength` to choose prefix length (range 1–100).
          5. Connect UI signals to the `updated` and `removed` signals.
        """
        super().__init__(nr, stats_cols, geo_cols, parent)

        # Build UI elements from the designer file
        self.setupUi(self)

        # Populate dropdowns with available columns
        self.comboExcel.addItems(stats_cols)
        self.comboGeo.addItems(geo_cols)

        # Configure prefix length spin box
        self.spinLength.setRange(1, 100)
        self.spinLength.setValue(3)

        # Connect UI changes to notify that configuration changed
        self.comboExcel.currentIndexChanged.connect(self.updated)
        self.comboGeo.currentIndexChanged.connect(self.updated)
        self.spinLength.valueChanged.connect(self.updated)
        # Connect remove button to emit removal signal
        self.buttonRemove.clicked.connect(self.removed.emit)

    # --------------------------------------------------------------------------
    #  Matching logic
    # --------------------------------------------------------------------------
    def match(self, stats_df: pd.DataFrame, geo_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[List[int]], Optional[List[int]]]:
        """
        Match records using exact prefix matching.

        Steps:
          1. Retrieve selected column names and prefix length from UI.
          2. If the selected columns are not present, set stats to 0 and return.
          3. Compute prefixes by taking the first `length` characters of string values.
          4. Identify common prefixes between both DataFrames.
          5. For each common prefix, select exactly one statistics row and one geo row.
          6. Build combined result rows via `build_result()`.
          7. Concatenate parts into one DataFrame, update stats label, and return indices.
        """
        stats_col = self.comboExcel.currentText()
        geo_col = self.comboGeo.currentText()
        length = self.spinLength.value()

        # Safety check: ensure selected columns exist
        if stats_col not in stats_df.columns or geo_col not in geo_df.columns:
            self.set_stats(0)
            return None, None, None

        # Build prefixes for each row
        stats_prefixes = stats_df[stats_col].astype(str).str[:length]
        geo_prefixes = geo_df[geo_col].astype(str).str[:length]

        # Find common prefixes
        common_prefixes = pd.Index(stats_prefixes.unique()).intersection(geo_prefixes.unique())
        if common_prefixes.empty:
            self.set_stats(0)
            return None, None, None

        parts: list[pd.DataFrame] = []
        ex_idx: list[int] = []
        ge_idx: list[int] = []
        label = self.description()

        # Map exactly one row per prefix
        for p in common_prefixes:
            ex_row = stats_df[stats_prefixes == p].iloc[[0]]
            ge_row = geo_df[geo_prefixes == p].iloc[[0]]
            parts.append(self.build_result(ex_row, ge_row, label))
            ex_idx.append(ex_row.index[0])
            ge_idx.append(ge_row.index[0])

        # Concatenate matched parts into a single DataFrame
        mapped = pd.concat(parts, ignore_index=True)
        # Update stats label with count of matched rows
        self.set_stats(len(mapped))
        return mapped, ex_idx, ge_idx

    # --------------------------------------------------------------------------
    #  Update column lists when upstream data changes
    # --------------------------------------------------------------------------
    # def update_stats_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the statistics column dropdown when column set changes.
    #
    #     Steps:
    #       1. Call parent method to update internal list.
    #       2. Remember currently selected column.
    #       3. Clear and repopulate the combo box with new columns.
    #       4. Reselect the previously chosen column if still available.
    #     """
    #     super().update_stats_columns(cols)
    #     cur = self.comboExcel.currentText()
    #     self.comboExcel.clear()
    #     self.comboExcel.addItems(cols)
    #     if cur in cols:
    #         self.comboExcel.setCurrentText(cur)

    # def update_geo_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the geo column dropdown when column set changes.
    #
    #     Steps:
    #       1. Call parent method to update internal list.
    #       2. Remember currently selected column.
    #       3. Clear and repopulate the combo box with new columns.
    #       4. Reselect the previously chosen column if still available.
    #     """
    #     super().update_geo_columns(cols)
    #     cur = self.comboGeo.currentText()
    #     self.comboGeo.clear()
    #     self.comboGeo.addItems(cols)
    #     if cur in cols:
    #         self.comboGeo.setCurrentText(cur)

    # --------------------------------------------------------------------------
    #  Stats display helper
    # --------------------------------------------------------------------------
    def set_stats(self, n: int) -> None:
        """
        Update the label that displays number of matches found.

        Steps:
          1. Convert integer `n` to string and set it on `labelStats`.
        """
        self.labelStats.setText(str(n))

    # --------------------------------------------------------------------------
    #  Description provider
    # --------------------------------------------------------------------------
    def description(self) -> str:
        """
        Provide a description of this matcher's configuration.

        Steps:
          1. Combine the matcher ID, selected stats column, selected geo column,
             and prefix length into a string.
          2. Format as "PRE#<nr>:<stats>→<geo>[<length>]".
        """
        return f"PRE#{self._nr}:{self.comboExcel.currentText()}→" f"{self.comboGeo.currentText()}[{self.spinLength.value()}]"
