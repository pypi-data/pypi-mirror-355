"""
Fuzzy matcher for matching Excel and geographical data.

This module provides a matcher that uses fuzzy string matching to find similar
values between Excel and geographical data columns. It uses the RapidFuzz library
to find the best match for each Excel value in the geographical data, subject to
a minimum similarity threshold.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from src.mapper.base.matcher_base import BaseMatcher
from src.mapper.matchers.ui.fuzzy_matcher_ui import Ui_FuzzyMatcher


# ==============================================================================
#  FuzzyMatcher: Implements fuzzy string matching between Excel and geo data
# ==============================================================================
class FuzzyMatcher(BaseMatcher, Ui_FuzzyMatcher):
    """
    Matcher for fuzzy string matching between Excel and geographical data.

    Behavior:
      - Uses RapidFuzz to extract the best match for each Excel value from geo values.
      - Only accepts matches above a configurable similarity threshold.
      - Ensures one-to-one matching (no duplicate matches on geo side).

    Signals:
      updated: Emitted when the matcher configuration changes.
      removed: Emitted when the matcher is removed.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, nr: int, excel_cols: List[str], geo_cols: List[str]) -> None:
        """
        Initialize the fuzzy matcher UI and internal state.

        Steps:
          1. Call BaseMatcher constructor to store identifier and column lists.
          2. Call setupUi(self) to create UI controls from the .ui file.
          3. Populate the Excel and geo combo boxes with available columns.
          4. Connect UI signals to notify when configuration changes or removal is requested.
        """
        super().__init__(nr, excel_cols, geo_cols)
        # Build UI elements from the designer file
        self.setupUi(self)

        # Populate dropdowns with available columns
        self.comboExcel.addItems(excel_cols)
        self.comboGeo.addItems(geo_cols)

        # Connect dropdown and spinbox changes to the updated signal
        self.comboExcel.currentIndexChanged.connect(self.updated)
        self.comboGeo.currentIndexChanged.connect(self.updated)
        self.spinThreshold.valueChanged.connect(self.updated)
        # Connect remove button to emit the removed signal when clicked
        self.buttonRemove.clicked.connect(self.removed.emit)

    # --------------------------------------------------------------------------
    #  Matching logic
    # --------------------------------------------------------------------------
    def match(self, excel_df: pd.DataFrame, geo_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[List[int]], Optional[List[int]]]:
        """
        Match records between Excel and geographical data using fuzzy string matching.

        Steps:
          1. Retrieve selected columns and threshold from UI.
          2. If threshold ≤ 1, scale it to percentage (multiply by 100).
          3. If either combo is empty, reset stats display and return no matches.
          4. Convert both column values to strings for comparison.
          5. Use RapidFuzz `extractOne` to find the best geo match for each Excel value,
             scoring with WRatio and discarding choices below threshold.
          6. Skip matches where the geo value was already used to enforce 1:1 mapping.
          7. For each accepted match, build a result row with a label containing the score.
          8. Concatenate all matched parts into one DataFrame.
          9. Update the stats label with the number of matched rows.
        """
        # Retrieve column names and threshold
        ex_col = self.comboExcel.currentText()
        ge_col = self.comboGeo.currentText()
        threshold = self.spinThreshold.value()
        if threshold <= 1:
            threshold *= 100

        # Bail out if no column is selected
        if not ex_col or not ge_col:
            self.set_stats(0)
            return None, None, None

        # Convert selected column values to string lists
        ex_values = excel_df[ex_col].astype(str).tolist()
        ge_values = geo_df[ge_col].astype(str).tolist()

        # Track used indices to enforce 1:1 mapping
        ex_used_labels: List[int] = []
        ge_used_labels: set = set()
        mapped_parts: List[pd.DataFrame] = []

        # Iterate each Excel value and attempt to find a fuzzy match in geo values
        for ex_pos, ex_val in enumerate(ex_values):
            # Find best match above threshold, scoring with WRatio
            choice = process.extractOne(ex_val, ge_values, scorer=fuzz.WRatio, score_cutoff=threshold)  # type: ignore[attr-defined]
            if not choice:
                continue  # Skip if no valid match found

            match_str, score, ge_pos = choice
            ge_label = geo_df.index[ge_pos]
            # Skip if that geo value is already matched
            if ge_label in ge_used_labels:
                continue

            # Build descriptive label including match score
            label = f"{self.description()}@{score:.1f}"
            # Build result DataFrame for this match
            part = self.build_result(excel_df.iloc[[ex_pos]], geo_df.iloc[[ge_pos]], label)
            mapped_parts.append(part)
            # Record the actual row indices used
            ex_used_labels.append(excel_df.index[ex_pos])
            ge_used_labels.add(ge_label)

        # If no parts were matched, indicate zero and return
        if not mapped_parts:
            self.set_stats(0)
            return None, None, None

        # Concatenate all matched DataFrames into one
        mapped_df = pd.concat(mapped_parts, ignore_index=True)
        # Update the UI to show how many mappings occurred
        self.set_stats(len(mapped_df))
        return mapped_df, ex_used_labels, list(ge_used_labels)

    # --------------------------------------------------------------------------
    #  Column update helpers
    # --------------------------------------------------------------------------
    # def update_excel_columns(self, cols: List[str]) -> None:
    #     """
    #     Update available Excel columns when upstream data changes.
    #
    #     Steps:
    #       1. Remember the currently selected column (if any).
    #       2. Clear the combo box and repopulate with new `cols`.
    #       3. If the previously selected column still exists, reselect it.
    #     """
    #     cur = self.comboExcel.currentText()
    #     self.comboExcel.clear()
    #     self.comboExcel.addItems(cols)
    #     if cur in cols:
    #         self.comboExcel.setCurrentText(cur)

    # def update_geo_columns(self, cols: List[str]) -> None:
    #     """
    #     Update available geo columns when upstream data changes.
    #
    #     Steps:
    #       1. Remember the currently selected column (if any).
    #       2. Clear the combo box and repopulate with new `cols`.
    #       3. If the previously selected column still exists, reselect it.
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
        Update the statistics label to reflect the number of matched rows.

        Steps:
          1. Set the text of `labelStats` to show "Mappings: n".
        """
        self.labelStats.setText(f"Mappings: {n}")

    # --------------------------------------------------------------------------
    #  Description provider
    # --------------------------------------------------------------------------
    def description(self) -> str:
        """
        Return a description of this matcher’s configuration.

        Steps:
          1. Combine the matcher ID, selected Excel column, and selected geo column.
          2. Format as "FUZZ#<nr>:<excel>→<geo>".
        """
        return f"FUZZ#{self._nr}:{self.comboExcel.currentText()}→{self.comboGeo.currentText()}"
