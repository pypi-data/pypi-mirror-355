"""
Manual Mapping dialog (pipeline step 5).

Why another dialog?
-------------------
Automatic matchers can never cover every edge-case. This widget therefore
lets the user manually join remaining **statistics rows** with **geo rows**
(one-to-one) or revert previously created matches.

Features
--------
* Tri-pane layout (mapped / remaining statistics / remaining geo).
* Checkbox column for multi-row operations.
* “Map” and “Unmap” buttons only enable when the current selection is valid.
* Search boxes above every table use a case-insensitive proxy filter.

All heavy lifting is pure *pandas* or Qt model manipulation; no external
dependencies.
"""

from __future__ import annotations

import logging
from typing import List

import pandas as pd
from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMainWindow

from src.views.manual_map.ui.manual_mapping_window_ui import Ui_ManualMappingWindow

log = logging.getLogger(__name__)

# Index for the checkbox column in models
CHK = 0


# ==============================================================================
#  ManualMapView: Final resort manual join dialog
# ==============================================================================
class ManualMapView(QMainWindow, Ui_ManualMappingWindow):
    """
    Provides a UI for manually joining statistics rows with geo rows when automatic
    matchers fail to match everything.

    Responsibilities:
      1. Display three panes: mapped rows, remaining statistics, remaining geo.
      2. Allow selecting exactly one stats row and one geo row to map them manually.
      3. Allow selecting one or more mapped rows to unmap them back to the remaining panes.
      4. Update button enablement based on valid selections.
      5. Emit a signal after any mapping or unmapping so downstream steps can refresh.
    """

    # Signal emitted after a manual map/unmap operation, passes the current mapped DataFrame
    manualMappingDone = Signal(pd.DataFrame)

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, parent=None) -> None:
        """
        Initializes the ManualMapView.

        - Loads the UI layout defined in Ui_ManualMappingWindow.
        - Sets up internal DataFrame placeholders for mapped, stats, and geo.
        - Calls internal methods to build models and wire signals.
        """
        super().__init__(parent)
        # Load UI definitions
        self.setupUi(self)

        # ---------------- Internal DataFrames ----------------
        # Will hold rows already mapped (with both _stats and _geodata suffixes)
        self._df_mapped = pd.DataFrame()
        # Will hold statistics rows not yet matched
        self._df_stats = pd.DataFrame()
        # Will hold geo rows not yet matched (already suffixed _geodata)
        self._df_geo = pd.DataFrame()

        # Build QStandardItemModels and proxy filters for each table
        self._init_models()
        # Wire up Qt button clicks, search edits, and item-changed signals
        self._wire()

    # ==============================================================================
    #  Model / Proxy Initialization
    # ==============================================================================
    def _init_models(self) -> None:
        """
        Creates three QStandardItemModel instances (for mapped, stats, geo),
        wraps each in a QSortFilterProxyModel for case-insensitive filtering,
        and attaches them to the respective QTableViews.

        Also configures each table view to resize columns to contents and select full rows.
        """
        # Create raw models for mapped, stats, and geo
        self.mod_map = QStandardItemModel(self)
        self.mod_stats = QStandardItemModel(self)
        self.mod_geo = QStandardItemModel(self)

        # Create proxy filters for each model to enable search by any column
        self.prx_map = QSortFilterProxyModel(self)
        self.prx_stats = QSortFilterProxyModel(self)
        self.prx_geo = QSortFilterProxyModel(self)

        # Attach each proxy to its source model and configure filtering
        for src, prx in ((self.mod_map, self.prx_map), (self.mod_stats, self.prx_stats), (self.mod_geo, self.prx_geo)):
            prx.setSourceModel(src)
            # Enable case-insensitive matching for filter strings
            prx.setFilterCaseSensitivity(Qt.CaseInsensitive)  # type: ignore[arg-type]
            # Allow filtering on all columns
            prx.setFilterKeyColumn(-1)

        # Attach proxies to the table views defined in UI
        self.tableViewMapped.setModel(self.prx_map)
        self.tableViewStatsRest.setModel(self.prx_stats)
        self.tableViewGeoRest.setModel(self.prx_geo)

        # Configure each view for better UX
        for tv in (self.tableViewMapped, self.tableViewStatsRest, self.tableViewGeoRest):
            # Resize columns based on content width
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # type: ignore[arg-type]
            # Select entire rows when clicking
            tv.setSelectionBehavior(QAbstractItemView.SelectRows)  # type: ignore[arg-type]
            # Allow multiple selection
            tv.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[arg-type]

    # ==============================================================================
    #  Signal Wiring
    # ==============================================================================
    def _wire(self) -> None:
        """
        Connects UI elements to their handler methods.

        - 'Map' button triggers manual mapping of one stats row and one geo row.
        - 'Unmap' button triggers moving mapped rows back to remaining lists.
        - Search boxes above each table connect to the filter proxies.
        - Any change in a model’s checkbox triggers a refresh of button states.
        """
        # Connect 'Map' and 'Unmap' buttons
        self.buttonManualMap.clicked.connect(self._map)
        self.buttonUnmap.clicked.connect(self._unmap)

        # Connect search edits to filter proxies
        self.editSearchMappedManual.textChanged.connect(self.prx_map.setFilterFixedString)
        self.editSearchStatsRestManual.textChanged.connect(self.prx_stats.setFilterFixedString)
        self.editSearchGeoRestManual.textChanged.connect(self.prx_geo.setFilterFixedString)

        # Ensure that whenever any item’s checkbox changes, we update button enablement
        for m in (self.mod_map, self.mod_stats, self.mod_geo):
            m.itemChanged.connect(lambda *_: self._update_buttons())

    # ==============================================================================
    #  Public API: Load Data into Models
    # ==============================================================================
    def load_data(self, mapped: pd.DataFrame, stats_rest: pd.DataFrame, geo_rest: pd.DataFrame) -> None:
        """
        Receives DataFrames from the automatic matcher dialog.

        - Mapped: already joined rows (with '_stats' and '_geodata' suffixes).
        - Stats_rest: remaining statistics rows to be matched.
        - Geo_rest: remaining geo rows to be matched.

        Fills each model with the corresponding DataFrame, including a checkbox column.
        Then updates button states and resizes columns for readability.
        Finally emits the manualMappingDone signal with the current mapped DataFrame.
        """
        # Store copies of the input DataFrames
        self._df_mapped = mapped.copy()
        self._df_stats = stats_rest.copy()
        self._df_geo = geo_rest.copy()

        # Populate each model; pass with_checkbox=True to include a checkbox column
        self._fill_model(self.mod_map, self._df_mapped, with_checkbox=True)
        self._fill_model(self.mod_stats, self._df_stats, with_checkbox=True)
        self._fill_model(self.mod_geo, self._df_geo, with_checkbox=True)

        # Update Map/Unmap button enablement based on initial checkboxes
        self._update_buttons()

        # Resize all table views to fit their contents
        for tv in (self.tableViewMapped, self.tableViewStatsRest, self.tableViewGeoRest):
            self._auto_resize(tv)

        # Notify parent that manual mapping data is ready
        self.manualMappingDone.emit(self._df_mapped)

    # ==============================================================================
    #  Mapping / Unmapping Actions
    # ==============================================================================
    def _map(self) -> None:
        """
        Joins exactly one stats row with exactly one geo row manually.

        Steps:
          1. Check that exactly one checkbox is ticked in stats and exactly one in geo.
          2. If not, return without doing anything.
          3. Retrieve the selected stats row, rename its columns by appending '_stats'.
          4. Retrieve the selected geo row (already suffixed '_geodata').
          5. Concatenate these two Series into a single combined row.
          6. Add a column 'matcher' with value 'manual' to indicate manual mapping.
          7. Append the combined row to the mapped DataFrame.
          8. Remove the original rows from _df_stats and _df_geo, reset their indices.
          9. Call load_data() to refresh all models based on updated DataFrames.
        """
        # Get indices of checked stats rows and checked geo rows
        s_rows = self._checked_rows(self.mod_stats)
        g_rows = self._checked_rows(self.mod_geo)
        # Ensure exactly one from each; otherwise skip
        if len(s_rows) != 1 or len(g_rows) != 1:
            return

        # Extract the single selected indices
        i_s, i_g = s_rows[0], g_rows[0]

        # Prepare the stats row, appending '_stats' to each column name
        stats_row = self._df_stats.iloc[i_s].rename(lambda c: f"{c}_stats")
        # Prepare the geo row (columns already have '_geodata' suffix)
        geo_row = self._df_geo.iloc[i_g]
        # Combine into one row and mark as manually matched
        combined = pd.concat([stats_row, geo_row])
        combined["matcher"] = "manual"

        # Append the new combined row to the mapped DataFrame
        self._df_mapped = pd.concat([self._df_mapped, combined.to_frame().T], ignore_index=True)
        # Remove the matched stats and geo rows from their DataFrames
        self._df_stats.drop(index=i_s, inplace=True)
        self._df_geo.drop(index=i_g, inplace=True)
        # Reset indices so row orders remain consistent
        self._df_stats.reset_index(drop=True, inplace=True)
        self._df_geo.reset_index(drop=True, inplace=True)

        # Re-display all data by calling load_data with updated DataFrames
        self.load_data(self._df_mapped, self._df_stats, self._df_geo)

    def _unmap(self) -> None:
        """
        Moves one or more mapped rows back to the remaining stats and geo tables.

        Steps:
          1. Gather all indices of checked rows in the mapped model.
          2. If none are selected, return.
          3. For each selected index (in reverse order):
             a. Extract the row from _df_mapped.
             b. Separate stats part by filtering columns ending in '_stats',
                remove the suffix, and append to _df_stats.
             c. Separate geo part by filtering columns ending in '_geodata'
                and append to _df_geo.
             d. Remove the row from _df_mapped.
          4. Reset indices of _df_mapped.
          5. Call load_data() to refresh all models with updated DataFrames.
        """
        # Find indices of checked rows in the mapped model
        rows = self._checked_rows(self.mod_map)
        if not rows:
            return

        # Process from the highest index down to avoid reindexing issues
        for r in sorted(rows, reverse=True):
            row = self._df_mapped.iloc[r]

            # Extract stats part, drop '_stats' suffix, and append to stats DataFrame
            self._df_stats = pd.concat([self._df_stats, row.filter(like="_stats").rename(lambda c: c[:-6]).to_frame().T], ignore_index=True)

            # Extract geo part (keeps '_geodata' suffix) and append to geo DataFrame
            self._df_geo = pd.concat([self._df_geo, row.filter(like="_geodata").to_frame().T], ignore_index=True)

            # Remove the unmapped row from mapped DataFrame
            self._df_mapped.drop(index=r, inplace=True)

        # Reset indices of mapped DataFrame after removals
        self._df_mapped.reset_index(drop=True, inplace=True)
        # Refresh models by reloading all three DataFrames
        self.load_data(self._df_mapped, self._df_stats, self._df_geo)

    # ==============================================================================
    #  Utility Helpers
    # ==============================================================================
    @staticmethod
    def _fill_model(model: QStandardItemModel, df: pd.DataFrame, *, with_checkbox: bool) -> None:
        """
        Populates the given QStandardItemModel with the contents of the DataFrame.

        - Clears any existing items in the model.
        - If the DataFrame is empty, returns immediately.
        - Otherwise, sets up column headers; if with_checkbox=True, prepends an empty
          header for the checkbox column.
        - Sets the row and column counts to match the DataFrame (plus checkbox column).
        - For each row:
          a. If with_checkbox, create a non-editable, checkable QStandardItem in column CHK.
          b. For each DataFrame column, create a non-editable QStandardItem with the cell’s text.
          c. Insert the item into the model at the correct (row, column) position.
        """
        # Clear any existing data
        model.clear()
        if df.empty:
            return

        # Build headers list: an empty label for the checkbox column plus DataFrame column names
        headers: List[str] = [""] + list(df.columns) if with_checkbox else list(df.columns)
        model.setColumnCount(len(headers))
        model.setRowCount(len(df))
        model.setHorizontalHeaderLabels(headers)

        # Determine starting index for data columns
        start_col = 1 if with_checkbox else 0
        for r in range(len(df)):
            if with_checkbox:
                # Create a checkbox item (unchecked by default)
                chk = QStandardItem()
                chk.setCheckable(True)
                chk.setEditable(False)
                model.setItem(r, CHK, chk)

            # Populate data columns as non-editable items
            for c, col_name in enumerate(df.columns, start_col):
                itm = QStandardItem(str(df.iat[r, c - start_col]))
                itm.setEditable(False)
                model.setItem(r, c, itm)

    @staticmethod
    def _checked_rows(model: QStandardItemModel) -> List[int]:
        """
        Returns a list of row indices where the checkbox column is checked.

        - Iterates over every row in the model.
        - For each row, gets the item at column CHK and checks if its state is Qt.Checked.
        - Collects and returns all row indices meeting that criterion.
        """
        return [r for r in range(model.rowCount()) if (itm := model.item(r, CHK)) and itm.checkState() == Qt.Checked]  # type: ignore[arg-type]

    def _update_buttons(self) -> None:
        """
        Enables or disables the 'Map' and 'Unmap' buttons based on current checkboxes.

        - 'Unmap' is enabled if at least one row is checked in the mapped model.
        - 'Map' is enabled only if exactly one row is checked in stats and exactly
          one row is checked in geo.
        """
        # Enable 'Unmap' if any mapped row is selected
        self.buttonUnmap.setEnabled(bool(self._checked_rows(self.mod_map)))
        # Enable 'Map' only if exactly one stats row and one geo row are selected
        self.buttonManualMap.setEnabled(len(self._checked_rows(self.mod_stats)) == 1 and len(self._checked_rows(self.mod_geo)) == 1)

    @staticmethod
    def _auto_resize(tv) -> None:
        """
        Resizes the columns and rows of the provided QTableView to fit contents.

        - Calls resizeColumnsToContents() to adjust column widths.
        - Sets the horizontal header too Interactive to allow manual resizing.
        - Calls resizeRowsToContents() to adjust row heights.
        """
        tv.resizeColumnsToContents()
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[arg-type]
        tv.resizeRowsToContents()

    # ==============================================================================
    #  Navigation Guard Methods
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Allows navigation to the next step only if there is at least one mapped row.

        Returns True if the mapped DataFrame is not empty.
        """
        return not self._df_mapped.empty

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Always allows navigation back from this view.

        Returns True unconditionally.
        """
        return True
