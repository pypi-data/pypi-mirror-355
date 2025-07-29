# python/mapper/unique_value_matcher.py

"""
Unique value matcher for matching Excel and geographical data.

This module provides a matcher that uses exact matching to find matches between
Excel and geographical data columns. It matches values that are exactly equal
between the two datasets.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from src.mapper.base.matcher_base import BaseMatcher
from src.mapper.matchers.ui.unique_value_matcher_ui import Ui_UniqueValueMatcher


# ==============================================================================
#  UniqueValueMatcher: Implements exact value matching between stats and geo data
# ==============================================================================
class UniqueValueMatcher(BaseMatcher, Ui_UniqueValueMatcher):
    """
    Matcher for exact value matching between Excel and geographical data.

    Behavior:
      - Finds exact matches between selected Excel and geo columns.
      - Ensures one-to-one mapping (skips geo values once used).
      - Normalizes values based on UI checkbox settings.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, nr: int, excel_cols: List[str], geo_cols: List[str]) -> None:
        """
        Initialize the unique value matcher widget.

        Steps:
          1. Call BaseMatcher constructor to store identifier and column lists.
          2. Call setupUi(self) to build UI controls from .ui file.
          3. Populate Excel and geo combo boxes with provided column lists.
          4. Disable normalization checkboxes by default.
          5. Connect UI signals to the `updated` and `removed` signals.
        """
        super().__init__(nr, excel_cols, geo_cols)
        # Build UI elements from the designer file
        self.setupUi(self)

        # Populate dropdowns with available columns
        self.comboExcel.addItems(excel_cols)
        self.comboGeo.addItems(geo_cols)

        # Set default state for normalization checkboxes
        self.cbIgnoreCase.setChecked(False)
        self.cbIgnoreWhitespace.setChecked(False)
        self.cbIgnorePunctuation.setChecked(False)

        # Connect UI changes to notify that configuration changed
        self.comboExcel.currentIndexChanged.connect(self.updated)
        self.comboGeo.currentIndexChanged.connect(self.updated)
        self.cbIgnoreCase.stateChanged.connect(self.updated)
        self.cbIgnoreWhitespace.stateChanged.connect(self.updated)
        self.cbIgnorePunctuation.stateChanged.connect(self.updated)
        # Connect remove button to emit removal request
        self.buttonRemove.clicked.connect(self.removed.emit)

    # --------------------------------------------------------------------------
    #  Matching logic
    # --------------------------------------------------------------------------
    def match(self, excel_df: pd.DataFrame, geo_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[List[int]], Optional[List[int]]]:
        """
        Match records using exact matching on normalized values.

        Steps:
          1. Retrieve selected columns from UI.
          2. If either column is missing, set stats to 0 and return no matches.
          3. Normalize values from both columns using `normalize()`:
             a. Convert to string.
             b. Optionally lowercase, strip whitespace, remove punctuation.
          4. Iterate over each Excel normalized value:
             a. Find geo values that exactly match.
             b. If none, skip; if multiple, take the first.
             c. Skip if that geo index is already used.
             d. Build combined row via `build_result()`.
          5. Concatenate all matched parts into one DataFrame.
          6. Update stats label with count of matched rows.
        """
        ex_col = self.comboExcel.currentText()
        ge_col = self.comboGeo.currentText()
        # Bail out if columns not selected
        if not ex_col or not ge_col:
            self.set_stats(0)
            return None, None, None

        # Normalize column values according to UI checkbox settings
        ex_values = excel_df[ex_col].astype(str).map(self.normalize)
        ge_values = geo_df[ge_col].astype(str).map(self.normalize)

        ex_used_labels: List[int] = []
        ge_used_labels: set = set()
        mapped_parts: List[pd.DataFrame] = []

        # Iterate each normalized Excel value
        for ex_pos, ex_val in enumerate(ex_values):
            # Find matching geo rows for the same normalized value
            matches = ge_values[ge_values == ex_val]
            if matches.empty:
                continue  # No match found; skip
            ge_pos = matches.index[0]
            if ge_pos in ge_used_labels:
                continue  # Already matched that geo row; skip

            # Build result for this matching pair
            label = self.description()
            part = self.build_result(excel_df.iloc[[ex_pos]], geo_df.iloc[[ge_pos]], label)
            mapped_parts.append(part)
            ex_used_labels.append(excel_df.index[ex_pos])
            ge_used_labels.add(ge_pos)

        # If no mappings were found, update stats and return
        if not mapped_parts:
            self.set_stats(0)
            return None, None, None

        # Concatenate all result parts
        mapped_df = pd.concat(mapped_parts, ignore_index=True)
        # Update the UI with number of mappings
        self.set_stats(len(mapped_df))
        return mapped_df, ex_used_labels, list(ge_used_labels)

    # --------------------------------------------------------------------------
    #  Normalization helper
    # --------------------------------------------------------------------------
    def normalize(self, s: str) -> str:
        """
        Normalize a string value based on UI checkboxes.

        Steps:
          1. If "Ignore Case" is checked, convert to lowercase.
          2. If "Ignore Whitespace" is checked, remove all whitespace.
          3. If "Ignore Punctuation" is checked, remove punctuation characters.
        """
        if self.cbIgnoreCase.isChecked():
            s = s.lower()
        if self.cbIgnoreWhitespace.isChecked():
            s = "".join(s.split())
        if self.cbIgnorePunctuation.isChecked():
            import re

            # Remove any non-alphanumeric or whitespace characters
            s = re.sub(r"[^\w\s]", "", s)
        return s

    # --------------------------------------------------------------------------
    #  Update column lists when upstream data changes
    # --------------------------------------------------------------------------
    # def update_excel_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the Excel column dropdown after upstream data changes.
    #
    #     Steps:
    #       1. Remember the currently selected column.
    #       2. Clear and repopulate the combo box with new `cols`.
    #       3. Reselect previous column if still available.
    #     """
    #     cur = self.comboExcel.currentText()
    #     self.comboExcel.clear()
    #     self.comboExcel.addItems(cols)
    #     if cur in cols:
    #         self.comboExcel.setCurrentText(cur)

    # def update_geo_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the geo column dropdown after upstream data changes.
    #
    #     Steps:
    #       1. Remember the currently selected column.
    #       2. Clear and repopulate the combo box with new `cols`.
    #       3. Reselect previous column if still available.
    #     """
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
        Update the label showing number of matches found.

        Steps:
          1. Set `labelStats` text to "Mappings: n".
        """
        self.labelStats.setText(f"Mappings: {n}")

    # --------------------------------------------------------------------------
    #  Description provider
    # --------------------------------------------------------------------------
    def description(self) -> str:
        """
        Provide a description of this matcher’s configuration.

        Steps:
          1. Retrieve current selections for Excel and geo columns.
          2. Format as "UVM#<nr>:<excel>→<geo>".
        """
        return f"UVM#{self._nr}:{self.comboExcel.currentText()}→{self.comboGeo.currentText()}"
