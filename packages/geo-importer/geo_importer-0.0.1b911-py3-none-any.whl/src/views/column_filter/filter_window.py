"""
Column-selection & row-filter dialog.

Stage in the import pipeline where the user:

1. Assigns *real* column headers (possibly skipping heading rows).
2. Selects which columns are relevant for the project.
3. Optionally writes a pandas-query to filter rows.
4. Optionally performs row down-sampling.

All heavy lifting (header construction / query evaluation / sampling) lives in
python.stats_processor.py. This file focuses purely on **UI logic** and wiring.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QListWidgetItem, QMainWindow

from src.core.constants import ERROR_DURATION, MAX_UNIQUE_VALUES, STATUS_DURATION
from src.core.stats_processor import apply_expr, build_header
from src.views.column_filter.ui.filter_window_ui import Ui_FilterWindow


# ==============================================================================
#  ColumnFilterView: GUI wrapper around stats_processor pipeline
# ==============================================================================
class ColumnFilterView(QMainWindow, Ui_FilterWindow):
    """
    Provides a dialog for selecting real column names, choosing which columns to keep,
    writing an optional query to filter rows, and performing optional down-sampling.

    Responsibilities:
      1. Let the user skip a number of header rows and apply build_header.
      2. Display available fields and allow selecting columns via checkboxes.
      3. Provide a query editor to filter rows with pandas expressions.
      4. Show a preview of the filtered DataFrame.
      5. Emit the filtered DataFrame and selected columns via filterReady signal.
    """

    # Signal emitted when the user finishes filtering. Payload: {"df_filtered": <DataFrame>, "selected_columns": List[str]}
    filterReady = Signal(dict)

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the ColumnFilterView.

        - Loads the UI from Ui_FilterWindow.
        - Sets up the splitter to a 50/50 layout.
        - Configures controls such as spinSkipRows and preview table.
        - Registers runtime variables for raw, header-adjusted, and filtered DataFrames.
        - Wires signals for skip-rows changes, column selection, query editor, and preview button.
        """
        super().__init__()
        # Load UI elements defined in Qt Designer
        self.setupUi(self)

        # ----------------------------------------------------------------------
        #  Splitter and Table Configuration
        # ----------------------------------------------------------------------
        # Ensure the splitter allocates half the space to each pane initially
        self.splitMain.setStretchFactor(0, 1)
        self.splitMain.setStretchFactor(1, 1)
        # Default to skipping the first row as header row
        self.spinSkipRows.setValue(1)
        # Make the preview table read-only so users cannot edit cells directly
        self.tablePreview.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore[arg-type]

        # ----------------------------------------------------------------------
        #  Runtime Data Holders
        # ----------------------------------------------------------------------
        # Holds the raw DataFrame loaded from the previous step
        self._df_base: Optional[pd.DataFrame] = None
        # Holds the DataFrame after applying build_header, with proper headers
        self._df_hdr: Optional[pd.DataFrame] = None
        # Holds the DataFrame after applying query filtering
        self._df_view: Optional[pd.DataFrame] = None
        # Tracks if the current expression is valid
        self._expr_ok: bool = True

        # ----------------------------------------------------------------------
        #  Connect Signals to Handlers
        # ----------------------------------------------------------------------
        # When the skip-rows spinner changes, rebuild headers
        self.spinSkipRows.valueChanged.connect(self._on_skip_changed)
        # When any column checkbox changes, update preview button enablement
        self.listColumns.itemChanged.connect(self._on_column_change)
        # Buttons to select/deselect all columns
        self.btnSelectAll.clicked.connect(self._select_all_columns)
        self.btnDeselectAll.clicked.connect(self._deselect_all_columns)
        # Double-clicking a field inserts it into the query expression
        self.listFields.itemDoubleClicked.connect(self._insert_field)
        # Double-clicking a value inserts it into the query expression
        self.listValues.itemDoubleClicked.connect(self._insert_value)

        # Add common query operators into the expression editor
        for btn, txt in (
            (self.btnEq, " == "),
            (self.btnNe, " != "),
            (self.btnLt, " < "),
            (self.btnGt, " > "),
            (self.btnAnd, " and "),
            (self.btnOr, " or "),
            (self.btnLike, " like "),
            (self.btnIn, " in "),
        ):
            # Connect each operator button to insert its text into the editor
            btn.clicked.connect(lambda _=None, t=txt: self._insert_at_cursor(t))

        # Clear the expression editor when Clear button is clicked
        self.btnClearExpr.clicked.connect(self.textExpr.clear)
        # Apply filtering and emit result when Test/Preview button is clicked
        self.btnTestExpr.clicked.connect(self._apply_and_emit)

    # ==============================================================================
    #  Public API: Load DataFrame from MainWindow
    # ==============================================================================
    def load_dataframe(self, df: pd.DataFrame) -> None:
        """
        Receives the DataFrame from DataPrepWindow, which contains raw data without real headers.

        Steps:
          1. Convert all columns to string type for consistency.
          2. Store a copy as _df_base and reset its index.
          3. Build header using build_header with the current skip-rows value.
          4. Select all columns by default.
          5. Apply the initial filter (no expression) to generate a preview.
          6. Adjust the preview table width to fit content.
        """
        # Convert every column in df to string type to avoid dtype issues
        for col in df.columns:
            df[col] = df[col].astype(str)

        # Copy the cleaned DataFrame and reset its index
        self._df_base = df.copy().reset_index(drop=True)
        # Rebuild headers based on skip-rows setting
        self._rebuild_base()
        # Check all columns by default
        self._select_all_columns()
        # Apply filtering and emit initial preview
        self._apply_and_emit()

        # Adjust the table width to ensure no data is cut off
        self._adjust_table_width()

    # ==============================================================================
    #  Header Handling
    # ==============================================================================
    def _populate_lists(self) -> None:
        """
        Refreshes the Fields and Columns list widgets based on the header-adjusted DataFrame (_df_hdr).

        Steps:
          1. If _df_hdr is not set, do nothing.
          2. Collect column names from _df_hdr as strings.
          3. Preserve which columns were previously checked.
          4. Clear existing items in the Fields and Values lists.
          5. Rebuild the Columns list with checkboxes, restoring previous checked states.
        """
        if self._df_hdr is None:
            return

        # Convert column names to strings
        cols = list(map(str, self._df_hdr.columns))

        # Record which column indices were previously checked
        prev_checked = {i for i in range(self.listColumns.count()) if self.listColumns.item(i).checkState() == Qt.Checked}  # type: ignore[arg-type]

        # Clear the Fields and Values lists
        self.listFields.clear()
        self.listValues.clear()

        # Rebuild the Columns list with checkable items
        self.listColumns.blockSignals(True)
        self.listColumns.clear()

        for idx, col in enumerate(cols):
            # Add the field name to the Fields list
            self.listFields.addItem(col)

            # Create a checkable list item for the column
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # type: ignore[arg-type]
            # Restore checked state if this index was previously checked
            item.setCheckState(Qt.Checked if idx in prev_checked else Qt.Unchecked)  # type: ignore[arg-type]
            self.listColumns.addItem(item)

        self.listColumns.blockSignals(False)

    def _on_column_change(self) -> None:
        """
        Enables or disables the Test/Preview button based on column selection.

        - Scans the Columns list to see if any column is checked.
        - Enables btnTestExpr only if at least one column is selected.
        """
        has_selection = any(self.listColumns.item(i).checkState() == Qt.Checked for i in range(self.listColumns.count()))  # type: ignore[arg-type]
        self.btnTestExpr.setEnabled(has_selection)

    def _rebuild_base(self) -> None:
        """
        Rebuilds the header-adjusted DataFrame (_df_hdr) using build_header.

        Steps:
          1. If _df_base is not set, return immediately.
          2. Call build_header with the raw DataFrame and skip-rows value.
          3. Convert all resulting columns to string type.
          4. Populate the Fields and Columns lists.
        """
        if self._df_base is None:
            return

        # Build a new DataFrame with proper headers, skipping the specified rows
        self._df_hdr = build_header(self._df_base, self.spinSkipRows.value())
        # Ensure every column is string type
        for col in self._df_hdr.columns:
            self._df_hdr[col] = self._df_hdr[col].astype(str)
        # Refresh the UI lists to show updated column names
        self._populate_lists()

    # ==============================================================================
    #  Filtering Logic
    # ==============================================================================
    def _rebuild_view(self) -> None:
        """
        Applies the query expression to _df_hdr and stores the result in _df_view.

        Steps:
          1. If _df_hdr is not set, return immediately.
          2. Retrieve the expression text.
          3. Try to apply apply_expr to filter _df_hdr.
             - On success: set _expr_ok=True and show a status message.
             - On failure: set _expr_ok=False, show an error message, and return.
          4. Store the filtered DataFrame in _df_view.
        """
        if self._df_hdr is None:
            return

        try:
            # Attempt to filter using the pandas expression
            expr = self.textExpr.toPlainText()
            filtered = apply_expr(self._df_hdr, expr)
            self._expr_ok = True
            # Inform the user that filtering succeeded
            self.statusbar.showMessage("Filter applied", STATUS_DURATION)
        except Exception as exc:
            # If the expression fails, record failure and show an error
            self._expr_ok = False
            error_msg = f"Invalid expression: {exc}"
            self.statusbar.showMessage(error_msg, ERROR_DURATION)
            return

        # Store the filtered DataFrame for later preview and emission
        self._df_view = filtered

    # ==============================================================================
    #  Query-Builder Helpers
    # ==============================================================================
    def _insert_field(self, itm: QListWidgetItem) -> None:
        """
        Inserts a protected column name into the query editor when a field is double-clicked.

        Steps:
          1. Get the field name from the item.
          2. Wrap it in backticks to handle special characters/spaces.
          3. Insert the backticked field into the query editor at the cursor.
          4. Populate the Values list with unique values from that column (up to MAX_UNIQUE_VALUES).
        """
        field = itm.text()
        # Insert the field name with backticks for safe referencing
        self._insert_at_cursor(f"`{field}`")

        # If the header DataFrame exists and the field is a column, populate unique values
        if self._df_hdr is not None and field in self._df_hdr.columns:
            # Get unique non-null values from the column
            vals = self._df_hdr[field].dropna().unique()[:MAX_UNIQUE_VALUES]
            self.listValues.clear()
            # Add each unique value as a string to the Values list
            self.listValues.addItems(map(str, vals))

    def _insert_value(self, itm: QListWidgetItem) -> None:
        """
        Inserts a literal value into the query editor when a value is double-clicked.

        - Wraps every inserted value in single quotes to treat as string.
        """
        val = itm.text()
        # Insert the value wrapped in single quotes
        self._insert_at_cursor(f"'{val}'")

    def _insert_at_cursor(self, txt: str) -> None:
        """
        Appends the given text at the current cursor position in the expression editor.

        - Retrieves the current cursor.
        - Inserts the specified text.
        - Updates the cursor position and refocuses the editor.
        """
        cur = self.textExpr.textCursor()
        cur.insertText(txt)
        self.textExpr.setTextCursor(cur)
        self.textExpr.setFocus()

    # ==============================================================================
    #  Preview & Signal Emission
    # ==============================================================================
    def _apply_and_emit(self) -> None:
        """
        Runs filter, updates the preview, and emits the filterReady signal.

        Steps:
          1. Rebuild the filtered view by calling _rebuild_view().
          2. If _df_view is not set, return immediately.
          3. Collect active (checked) column names.
             - If no columns are checked, return.
          4. Create df_sel by selecting only active columns from _df_view.
          5. Update the preview table with df_sel.
          6. Emit the filterReady signal with df_sel and selected columns.
        """
        # Apply query expression to build the filtered DataFrame
        self._rebuild_view()
        if self._df_view is None:
            return

        # Build a list of columns that are currently checked
        active_cols = [
            self.listColumns.item(i).text() for i in range(self.listColumns.count()) if self.listColumns.item(i).checkState() == Qt.Checked  # type: ignore[arg-type]
        ]

        if not active_cols:
            # If no columns are selected, do nothing
            return

        # Extract only the selected columns
        df_sel = self._df_view[active_cols].copy()
        # Render the preview table with the selected DataFrame
        self._update_preview(df_sel)

        # Emit the filtered DataFrame and column list to any listeners
        self.filterReady.emit({"df_filtered": df_sel, "selected_columns": active_cols})

    def _update_preview(self, df: Optional[pd.DataFrame] = None) -> None:
        """
        Renders the preview table on the left half of the splitter using the provided DataFrame.

        If df is None, uses _df_view. If still None, clears the table.
        Otherwise, builds a QStandardItemModel with df's data, sets it on tablePreview,
        and resizes columns to fit content.
        """
        if df is None:
            df = self._df_view
        if df is None:
            # No data to preview, clear the table
            self.tablePreview.setModel(None)
            return

        # Create a new standard item model with the same shape as df
        model = QStandardItemModel(df.shape[0], df.shape[1], self)
        # Set column headers to match df's columns
        model.setHorizontalHeaderLabels(df.columns.tolist())

        # Populate the model with df's cell values as strings
        for r in range(df.shape[0]):
            for c, _name in enumerate(df.columns):
                model.setItem(r, c, QStandardItem(str(df.iat[r, c])))

        # Attach the model to the preview table and adjust column widths
        self.tablePreview.setModel(model)
        self.tablePreview.resizeColumnsToContents()

        # Ensure the table width matches the content
        self._adjust_table_width()

    # ==============================================================================
    #  Table Width Adjustment
    # ==============================================================================
    def _adjust_table_width(self) -> None:
        """
        Adjusts the preview table’s width to fit its contents without cutting off any data.

        Steps:
          1. If _df_view is None or empty, do nothing.
          2. Resize each column to fit content and accumulate total width.
          3. Add padding for scrollbar, margins, and splitter handle.
          4. Compute maximum allowed width as 50% of the window width.
          5. Set splitter sizes so that left pane (preview) and right pane (filters)
             allocate space appropriately, with preview at most 50% wide, and filters at least 400px.
        """
        if self._df_view is None or self._df_view.empty:
            return

        # Reference the preview table
        table = self.tablePreview

        # Calculate total width required by column contents
        total_width = 0
        for i in range(table.model().columnCount()):
            table.resizeColumnToContents(i)
            total_width += table.columnWidth(i)

        # Add padding allowances:
        # - Vertical scrollbar: 20px
        # - Table margins: 2 * 10px
        # - GroupBox margins: 2 * 10px
        # - Splitter handle: 4px
        # - Safety margin: 10px
        total_width += 74

        # Get current window width
        window_width = self.width()
        # Limit preview to at most half the window width
        max_width = window_width * 0.5

        # Determine the preview pane width (cannot exceed half-window)
        splitter_width = min(total_width, max_width)
        # Ensure the filter pane (right side) remains at least 400px
        right_width = max(window_width - splitter_width, 400)

        # Apply sizes to the splitter: [left preview, right filters]
        self.splitMain.setSizes([splitter_width, right_width])

    # --------------------------------------------------------------------------
    #  Column Selection Helpers
    # --------------------------------------------------------------------------
    def _select_all_columns(self) -> None:
        """
        (Button) Checks every column in the Columns list.

        Iterates through all items and sets their check state to Checked,
        then calls _on_column_change() to update Preview button state.
        """
        for i in range(self.listColumns.count()):
            self.listColumns.item(i).setCheckState(Qt.Checked)  # type: ignore[arg-type]
        self._on_column_change()

    def _deselect_all_columns(self) -> None:
        """
        (Button) Unchecks every column in the Columns list.

        Iterates through all items and sets their check state to Unchecked,
        then calls _on_column_change() to update Preview button state.
        """
        for i in range(self.listColumns.count()):
            self.listColumns.item(i).setCheckState(Qt.Unchecked)  # type: ignore[arg-type]
        self._on_column_change()

    # ==============================================================================
    #  Skip-Rows Spinner Handler
    # ==============================================================================
    def _on_skip_changed(self) -> None:
        """
        Triggered when the skip-rows spinner value changes.

        Rebuilds the header-adjusted DataFrame by calling _rebuild_base().
        The preview is not automatically refreshed; the user must click Test/Preview.
        """
        if self._df_base is None:
            return
        # Re-create headers based on the new skip-rows value
        self._rebuild_base()

    # ==============================================================================
    #  Navigation Guard Methods
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Allows navigation to the next step only if:
          - At least one column is checked, AND
          - A valid preview DataFrame (_df_view) exists.

        Returns True if these conditions are met.
        """
        if self._df_view is None:
            return False
        checked = any(self.listColumns.item(i).checkState() == Qt.Checked for i in range(self.listColumns.count()))  # type: ignore[arg-type]
        return checked

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Always allows navigation back from this view.

        Returns True unconditionally.
        """
        return True

    # ==============================================================================
    #  Resize Event Handler
    # ==============================================================================
    def resizeEvent(self, event):
        """
        Ensures the splitter adjusts when the window is resized.

        - Calls the base class resizeEvent.
        - Recalculates table width to keep preview pane properly sized.
        """
        super().resizeEvent(event)
        self._adjust_table_width()
