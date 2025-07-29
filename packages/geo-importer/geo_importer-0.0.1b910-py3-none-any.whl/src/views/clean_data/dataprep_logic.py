"""Core utilities used by the DataPrep window.
----------------------------------------------

This module contains the logic used by the DataPrep view. It loads table data,
creates repeating selections and manages copy/paste patterns. Everything here
is independent of Qt so the functions can be tested on their own.
"""

from __future__ import annotations

import csv
import logging
from typing import Iterable, Sequence, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ======================================================================
#  Type Aliases
# ======================================================================

Coord = Tuple[int, int]  # (row, col) coordinate pair
PatternEntry = Tuple[int, int, str]  # (row, col, value) for copy pattern entries


# ======================================================================
#  DataPrepLogic: Stateless helper for DataPrep operations
# ======================================================================
class DataPrepLogic:
    """
    Helper object that performs all non-Qt work for DataPrep.

    The object provides small, easily testable methods for loading data,
    calculating "every Nth" selections and keeping a copy buffer for paste
    operations. At the end the table can be turned back into a pandas.DataFrame.

    Attributes:
      _df_source : Internal DataFrame holding the source data.
      _copy_pattern : List of tuples storing copied cell positions and values.
    """

    # ==================================================================
    #  Constructor / Base Data
    # ==================================================================
    def __init__(self) -> None:
        """
        Initialize internal buffers for later operations.

        Steps:
          1. Create an empty DataFrame placeholder for the source table.
          2. Prepare an empty list that stores copied cell patterns.
        """
        # Initialize source DataFrame and copy buffer
        self._df_source: pd.DataFrame = pd.DataFrame()
        self._copy_pattern: list[PatternEntry] = []

    # ==================================================================
    #  Data Sources
    # ==================================================================
    def load_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Copy the incoming DataFrame and give it numeric column names.

        Steps:
          1. Duplicate the provided DataFrame so the original remains unchanged.
          2. Rename the columns sequentially as strings ("0", "1", ...).
          3. Store the sanitized DataFrame for later use.
          4. Return the sanitized copy for display in the table widget.
        """
        # Create a copy to avoid mutating original
        df2 = df.copy()
        # Rename columns to sequential string indices
        df2.columns = [str(i) for i in range(df2.shape[1])]
        self._df_source = df2
        return df2

    def load_csv(self, path: str) -> pd.DataFrame:
        """
        Read a CSV file from disk and convert it into the internal DataFrame.

        Steps:
          1. Try to guess the delimiter by reading a small sample with csv.Sniffer.
          2. If that fails, fall back to ";" or "," based on sample content.
          3. Load the entire file with pandas, forcing all values to strings and disabling header parsing.
          4. Forward the resulting DataFrame to load_dataframe for renaming of columns.
        """
        # Attempt delimiter detection on file sample
        try:
            with open(path, encoding="utf-8") as fh:
                sample = fh.read(4096)
            delimiter = csv.Sniffer().sniff(sample).delimiter
        except csv.Error:
            # Fallback to semicolon or comma
            delimiter = ";" if ";" in sample else ","

        # Read full CSV without header, enforce string dtype
        df = pd.read_csv(path, delimiter=delimiter, dtype=str, encoding="utf-8", header=None)
        return self.load_dataframe(df)

    # ==================================================================
    #  Selection "Every Nth + Shift"
    # ==================================================================
    @staticmethod
    def _shift_and_crop(indices: Iterable[int], shift: int, max_size: int) -> set[int]:
        """
        Shift a set of indices and remove values that would fall outside the table.

        Steps:
          1. Add shift to each index in indices.
          2. Keep only those results that lie between 0 and max_size.
        """
        # Compute shifted indices while filtering out-of-bounds
        return {i + shift for i in indices if 0 <= i + shift < max_size}

    def compute_selection(self, row_n: int, col_n: int, row_shift: int, col_shift: int, mode: str, row_count: int, col_count: int) -> Set[Coord]:
        """
        Build a set of cell coordinates according to the selection settings.

        Steps:
          1. Determine base row and column indices based on row_n and col_n.
          2. Apply row_shift and col_shift while keeping indices within bounds.
          3. Combine rows and columns either with logical 'AND' or 'OR' depending on mode.
          4. Return the resulting coordinate set.
        """
        rows: set[int] = set()
        cols: set[int] = set()

        # Compute base row indices (every Nth) if requested
        if row_n > 0:
            every_n_rows = {r for r in range(row_n - 1, row_count, row_n)}
            rows = self._shift_and_crop(every_n_rows, row_shift, row_count)

        # Compute base column indices (every Nth) if requested
        if col_n > 0:
            every_n_cols = {c for c in range(col_n - 1, col_count, col_n)}
            cols = self._shift_and_crop(every_n_cols, col_shift, col_count)

        # Build final coordinate set based on mode
        result: set[Coord] = set()
        if mode == "AND" and rows and cols:
            # Include only cells where both row and column match
            for r in rows:
                result.update((r, c) for c in cols)
        else:
            # OR mode: include full rows and/or full columns
            if rows:
                for r in rows:
                    result.update((r, c) for c in range(col_count))
            if cols:
                for c in cols:
                    result.update((r, c) for r in range(row_count))

        return result

    # ==================================================================
    #  Copy / Paste
    # ==================================================================
    def prepare_copy_data(self, selected: Sequence[Coord], table_data: Sequence[Sequence[str]]) -> None:
        """
        Remember the currently selected cells for later paste operations.

        Steps:
          1. If selected is empty, clear any existing copy pattern.
          2. Otherwise, build _copy_pattern as a list of (row, col, value) tuples.
        """
        if not selected:
            # Clear stored pattern when nothing selected
            self._copy_pattern.clear()
            return

        # Store coordinates and values of selected cells
        self._copy_pattern = [(r, c, table_data[r][c]) for r, c in selected]
        logger.debug("Copy pattern created (%d cells).", len(self._copy_pattern))

    def get_paste_data(self, anchor_row: int, anchor_col: int, table_data: list[list[str]]) -> list[list[str]]:
        """
        Insert the previously copied cells into a cloned table.

        **Parameters**
        anchor_row (int)
        :   Zero‐based row index at which to begin pasting the copy buffer.
        anchor_col (int)
        :   Zero‐based column index at which to begin pasting the copy buffer.
        table_data (list[list[str]])
        :   The original 2D table data into which the copy buffer will be pasted.

        **Returns**
        list[list[str]]
        :   A deep‐copied version of `table_data` with the copied cells inserted
            at the specified anchor, leaving the original data unmodified.

        **Paste Algorithm**
        1. If the copy buffer is empty, returns the original `table_data` unchanged.
        2. Creates a deep copy of `table_data` for safe in-place modifications.
        3. Determines the minimal row and column indices in the copy buffer
           to compute relative offsets.
        4. For each entry `(r, c, value)` in the copy buffer:
           - Computes target coordinates
             ```python
             target_row = anchor_row + (r - min_row)
             target_col = anchor_col + (c - min_col)
             ```
           - If `(target_row, target_col)` lies within bounds, writes `value` there.
        5. Returns the modified copy.

        **Example**
        ```python
        # Suppose _copy_pattern = [(2,1,"X"), (3,2,"Y")]
        table = [
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
        ]
        # Paste at anchor (0,0) yields:
        # [
        #   ["", "X", ""],
        #   ["", "", "Y"],
        #   ["", "", ""],
        #   ["", "", ""],
        # ]
        new_table = instance.get_paste_data(0, 0, table)
        ```
        """
        if not self._copy_pattern:
            return table_data

        # Make a deep copy so original is untouched
        new_data = [row[:] for row in table_data]

        # Compute minimal offsets in the copy pattern
        min_row = min(r for r, _, _ in self._copy_pattern)
        min_col = min(c for _, c, _ in self._copy_pattern)

        max_rows = len(new_data)
        max_cols = len(new_data[0]) if new_data else 0

        for src_r, src_c, val in self._copy_pattern:
            tgt_r = anchor_row + (src_r - min_row)
            tgt_c = anchor_col + (src_c - min_col)
            if 0 <= tgt_r < max_rows and 0 <= tgt_c < max_cols:
                new_data[tgt_r][tgt_c] = val

        return new_data

    # ==================================================================
    #  Pattern Matching for Paste Validation
    # ==================================================================
    @staticmethod
    def _relative_offsets(coordinates: list[tuple[int, int]]) -> set[tuple[int, int]]:
        """
        Convert absolute coordinates into offsets relative to the top-left cell.

        Steps:
          1. Determine minimum row and column among coordinates.
          2. Subtract those minima from every coordinate.
        """
        if not coordinates:
            return set()
        base_r = min(r for r, _ in coordinates)
        base_c = min(c for _, c in coordinates)
        return {(r - base_r, c - base_c) for r, c in coordinates}

    def pattern_matches(self, dest_coordinates: set[tuple[int, int]]) -> bool:
        """
        Verify that a selection matches the stored copy pattern layout.

        Steps:
          1. Return False immediately if no pattern was stored.
          2. Compare relative offsets of dest_coordinates and _copy_pattern.
          3. Return True only when both offset sets are identical.
        """
        if not self._copy_pattern:
            # No pattern stored, cannot match
            return False

        # Compare source and destination offset sets
        src_offsets = self._relative_offsets([(r, c) for r, c, _ in self._copy_pattern])
        dst_offsets = self._relative_offsets(sorted(dest_coordinates))
        return src_offsets == dst_offsets

    # ==================================================================
    #  Export Helper: Convert Table Data to DataFrame
    # ==================================================================
    @staticmethod
    def convert_table_to_dataframe(table_data: Sequence[Sequence[str]], column_count: int) -> pd.DataFrame:
        """
        Convert the raw table data back into a pandas DataFrame.

        Steps:
          1. Slice each row to column_count elements to drop extras.
          2. Create the DataFrame with numeric column labels as strings.
        """
        df = pd.DataFrame((row[:column_count] for row in table_data), columns=[str(i) for i in range(column_count)])
        return df
