"""
Regex matcher for Excel-to-Geo assignments.

This matcher uses two regular expressions—one for the Excel column and one for
the geo column—to extract a common token from each cell. Only rows where exactly
one token match occurs are paired.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

import pandas as pd

from src.mapper.base.matcher_base import BaseMatcher
from src.mapper.matchers.ui.regex_matcher_ui import Ui_RegexMatcher


# ==============================================================================
#  RegexMatcher: Implements regex-based matching between stats and geo data
# ==============================================================================
class RegexMatcher(BaseMatcher, Ui_RegexMatcher):
    """
    Matcher that applies regex on Excel and geo columns and matches rows when
    both regex patterns yield exactly one identical extracted token.

    Behavior:
      - Retrieves regex patterns from UI fields.
      - Extracts a token from each cell via `re.search`.
      - Only matches rows where the extracted token from both sides is identical
        and occurs exactly once in the geo data.
      - Ensures one-to-one mapping (skips duplicate geo matches).
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, nr: int, excel_cols: List[str], geo_cols: List[str]) -> None:
        """
        Initialize the regex matcher widget.

        Steps:
          1. Call BaseMatcher constructor to store identifier and column lists.
          2. Call setupUi(self) to build UI controls from .ui file.
          3. Populate the Excel and geo combo boxes with available columns.
          4. Connect UI changes (combo and text edits) to the `updated` signal.
          5. Connect remove button to emit the `removed` signal.
        """
        super().__init__(nr, excel_cols, geo_cols)
        self.setupUi(self)

        # Populate dropdowns with column names
        self.comboExcel.addItems(excel_cols)
        self.comboGeo.addItems(geo_cols)

        # Connect UI events to configuration updates
        self.comboExcel.currentIndexChanged.connect(self.updated)
        self.comboGeo.currentIndexChanged.connect(self.updated)
        self.editExcelRegex.textChanged.connect(self.updated)
        self.editGeoRegex.textChanged.connect(self.updated)
        # Connect remove button to emit removal request
        self.buttonRemove.clicked.connect(self.removed.emit)

    # --------------------------------------------------------------------------
    #  Matching logic
    # --------------------------------------------------------------------------
    def match(self, excel_df: pd.DataFrame, geo_df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[List[int]], Optional[List[int]]]:
        """
        Match records when regex extractions from both columns yield exactly one identical token.

        Steps:
          1. Retrieve selected columns and regex patterns from UI.
          2. If any required input is missing, set stats to 0 and return no matches.
          3. Attempt to compile both regex patterns; on error, set stats to 0 and return.
          4. Define helper `extract(s, rex)` to return the first capturing group or whole match.
          5. Map every cell in the selected Excel column to its extracted token.
          6. Map every cell in the selected geo column to its extracted token.
          7. Iterate over each Excel token; skip if None or if resulting matches in geo side are not exactly one.
          8. Ensure no geo token is used more than once to enforce one-to-one mapping.
          9. Build a combined result row for each valid match via `build_result()`.
          10. Concatenate all parts if any, update stats label, and return used row indices.
        """
        ex_col = self.comboExcel.currentText()
        ge_col = self.comboGeo.currentText()
        pattern_ex = self.editExcelRegex.text().strip()
        pattern_ge = self.editGeoRegex.text().strip()

        # Must have both columns and non-empty regex patterns
        if not ex_col or not ge_col or not pattern_ex or not pattern_ge:
            self.set_stats(0)
            return None, None, None

        # Attempt to compile both regex patterns; if invalid, bail out
        try:
            rex_ex = re.compile(pattern_ex)
            rex_ge = re.compile(pattern_ge)
        except re.error:
            self.set_stats(0)
            return None, None, None

        # Helper to extract a token from a string via regex
        def extract(s: str, rex: re.Pattern) -> Optional[str]:
            m = rex.search(str(s))
            if not m:
                return None
            # If there is at least one capturing group, return it; otherwise, return full match
            return m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)

        # Apply extraction to entire columns
        ex_vals = excel_df[ex_col].map(lambda v: extract(v, rex_ex))
        ge_vals = geo_df[ge_col].map(lambda v: extract(v, rex_ge))

        ex_used: List[int] = []
        ge_used: set = set()
        parts: list[pd.DataFrame] = []

        # Iterate each extracted Excel token
        for ex_idx, ex_val in ex_vals.items():
            if ex_val is None:
                continue  # Skip if extraction failed

            # Identify geo rows with the same extracted token
            matches = ge_vals[ge_vals == ex_val]
            if len(matches) != 1:
                continue  # Only map if exactly one geo match

            ge_idx = matches.index[0]
            if ge_idx in ge_used:
                continue  # Skip if that geo row is already matched

            # Build result row and collect indices
            label = self.description()
            part = self.build_result(excel_df.loc[[ex_idx]], geo_df.loc[[ge_idx]], label)
            parts.append(part)
            ex_used.append(ex_idx)
            ge_used.add(ge_idx)

        # If nothing matched, update stats and return
        if not parts:
            self.set_stats(0)
            return None, None, None

        # Concatenate all matched parts
        df_mapped = pd.concat(parts, ignore_index=True)
        # Update stats label with total matches
        self.set_stats(len(df_mapped))
        return df_mapped, ex_used, list(ge_used)

    # --------------------------------------------------------------------------
    #  Update column lists when upstream data changes
    # --------------------------------------------------------------------------
    # def update_excel_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the Excel column dropdown after upstream changes.
    #
    #     Steps:
    #       1. Remember currently selected item.
    #       2. Clear and repopulate the combo box with new `cols`.
    #       3. Reselect previous item if still present.
    #     """
    #     cur = self.comboExcel.currentText()
    #     self.comboExcel.clear()
    #     self.comboExcel.addItems(cols)
    #     if cur in cols:
    #         self.comboExcel.setCurrentText(cur)

    # def update_geo_columns(self, cols: List[str]) -> None:
    #     """
    #     Refresh the geo column dropdown after upstream changes.
    #
    #     Steps:
    #       1. Remember currently selected item.
    #       2. Clear and repopulate the combo box with new `cols`.
    #       3. Reselect previous item if still present.
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
          2. Format as "REGEX#<nr>:<excel>↦<geo>".
        """
        ex = self.comboExcel.currentText()
        ge = self.comboGeo.currentText()
        return f"REGEX#{self._nr}:{ex}↦{ge}"
