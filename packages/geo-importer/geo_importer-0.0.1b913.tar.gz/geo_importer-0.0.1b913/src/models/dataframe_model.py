"""
A minimal, read-only Qt TableModel for displaying a pandas DataFrame in a QTableView.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


# ==============================================================================
#  DataFrameModel: Qt model to display pandas DataFrame read-only
# ==============================================================================
class DataFrameModel(QAbstractTableModel):
    """
    Presents a pandas DataFrame in a Qt QTableView without editing capabilities.

    Responsibilities:
      - Report the number of rows and columns based on the DataFrame shape.
      - Provide cell data as strings for display.
      - Supply header labels (column names for horizontal, row numbers for vertical).
      - Allow resetting the underlying DataFrame when data changes.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, df: pd.DataFrame | None = None, parent=None) -> None:
        """
        Initialize the model with an optional DataFrame.

        Steps:
          1. Calls the superclass constructor with the given parent.
          2. If a DataFrame is provided, uses it; otherwise creates an empty DataFrame.
        """
        super().__init__(parent)
        # Store a copy of the DataFrame or initialize an empty one
        self._df = df.copy() if df is not None else pd.DataFrame()

    # --------------------------------------------------------------------------
    #  Required Qt API methods
    # --------------------------------------------------------------------------
    def rowCount(self, _=QModelIndex()) -> int:
        """
        Return the number of rows in the model.

        - Reports the number of rows in the underlying DataFrame.
        - QModelIndex parameter is ignored for simple table models.
        """
        return len(self._df)

    def columnCount(self, _=QModelIndex()) -> int:
        """
        Return the number of columns in the model.

        - Reports the number of columns in the underlying DataFrame.
        - Uses DataFrame's columns attribute to count columns.
        - QModelIndex parameter is ignored for simple table models.
        """
        return len(self._df.columns)

    def data(self, ix: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[attr-defined]
        """
        Provide data for a given cell and role.

        Steps:
          1. Check if the requested role is DisplayRole and the index is valid.
          2. If so, retrieve the value at DataFrame.iat[row, column] and convert it to string.
          3. Otherwise, return None to indicate no data for other roles.
        """
        # Only handle display role and valid index
        if role == Qt.DisplayRole and ix.isValid():  # type: ignore[attr-defined]
            # Convert the DataFrame value to string for display
            value = self._df.iat[ix.row(), ix.column()]
            return str(value)
        return None

    # def headerData(self, sec: int, orient: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[attr-defined]
    #     """
    #     Provide header labels for horizontal and vertical orientations.
    #
    #     Steps:
    #       1. Only handle DisplayRole for headers; return None for other roles.
    #       2. If orientation is Horizontal, return the column name at index `sec`.
    #       3. If orientation is Vertical, return row number as `sec + 1`.
    #     """
    #     if role != Qt.DisplayRole:  # type: ignore[attr-defined]
    #         return None
    #
    #     if orient == Qt.Horizontal:  # type: ignore[attr-defined]
    #         # Return the column name for horizontal headers
    #         return self._df.columns[sec]
    #     else:
    #         # Return 1-based row number for vertical headers
    #         return sec + 1

    # --------------------------------------------------------------------------
    #  Public API for resetting the DataFrame
    # --------------------------------------------------------------------------
    def set_frame(self, df: pd.DataFrame) -> None:
        """
        Replace the underlying DataFrame with a new one and reset the model.

        Steps:
          1. Call beginResetModel() to notify views that the model will change completely.
          2. Store a copy of the new DataFrame (or an empty DataFrame if None is passed).
          3. Call endResetModel() to notify views that reset is finished.
        """
        self.beginResetModel()
        # Safely copy the DataFrame or use empty if None
        self._df = df.copy() if df is not None else pd.DataFrame()
        self.endResetModel()

    # @property
    # def frame(self) -> pd.DataFrame:
    #     """
    #     Return a copy of the current DataFrame stored in the model.
    #
    #     - Provides a read-only interface to retrieve the underlying DataFrame.
    #     - Returns a deep copy to prevent external modification.
    #     """
    #     return self._df.copy()
