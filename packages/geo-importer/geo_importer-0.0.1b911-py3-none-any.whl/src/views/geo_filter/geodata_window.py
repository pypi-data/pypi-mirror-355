"""
Geographical CSV selection & filtering dialog.

The logic is very similar to FilterWindow but operates on a predefined
directory layout (BASE_DIR/<type>/<version>/<level>.csv). This widget fills
four roles:

1. Let the user browse geo files by type, version, and level.
2. Offer the same row-filter and down-sampling features as the statistics dialog.
3. Allow column sub-selection (geo files often contain >50 columns).
4. Return both the filtered DataFrame and metadata about the chosen geo
   file so that later steps (mapping / export) can re-identify the source.

All UI-centric code lives here; all frame manipulation is delegated to
python.stats_processor.py.
"""

from __future__ import annotations

import csv
import os
from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QListWidgetItem, QMainWindow, QMessageBox

from src.core.constants import MAX_UNIQUE_VALUES, SAMPLE_SIZE
from src.views.geo_filter.ui.load_geodata_window_ui import Ui_GeoDataWindow

# ==============================================================================
#  Typed config container (used by MainWindow.export etc.)
# ==============================================================================
# @dataclass
# class GeoDataConfig:
#     """Container describing the chosen file and its logical category."""
#
#     type: str
#     version: str
#     level: str
#     file_path: str


# ==============================================================================
#  GeoFilterView: Geo-CSV selector with row & column filtering
# ==============================================================================
class GeoFilterView(QMainWindow, Ui_GeoDataWindow):
    """
    Provides a UI for selecting and filtering geographic CSV data.

    Responsibilities:
      1. Allow browsing of geo CSV files organized by type, version, and level.
      2. Load the chosen CSV, preview it, and enable filtering via a query expression.
      3. Let users pick which columns to include in the output.
      4. Emit the filtered DataFrame along with selected columns and file metadata.
    """

    # Signal emitted when filtering is complete; carries filtered DataFrame, column list, and metadata
    filterReady = Signal(dict)

    # Base directory where geo CSV files are stored
    BASE_DIR = os.path.join(os.path.dirname(__file__), "../../geodata")

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the GeoFilterView.

        - Loads the UI from Ui_GeoDataWindow.
        - Initializes runtime state variables for file path, raw/preview DataFrames, and expression validity.
        - Sets up UI elements that do not depend on data.
        - Wires Qt signals to their handlers.
        - Populates the geo type combo box based on directory structure.
        - Updates UI state based on initial conditions.
        """
        super().__init__()
        self.setupUi(self)

        # ---------------- Runtime State Variables ----------------
        # Holds the absolute path to the selected CSV; None if none chosen
        self._pending_fn: Optional[str] = None
        # Holds the raw DataFrame loaded from CSV; None if not yet loaded
        self._df_raw: Optional[pd.DataFrame] = None
        # Holds the DataFrame after applying filters and column selection
        self._df_view: Optional[pd.DataFrame] = None
        # True if the filter expression is valid; used to disable/enable controls
        self._expr_valid: bool = True

        # ---------------- UI Initialization ----------------
        self._init_ui()
        # Set up connections between signals and their handler methods
        self._connect_signals()
        # Fill the geo type combo box from the BASE_DIR directory listing
        self._populate_geo_types()
        # Adjust UI elements based on initial state (no file loaded)
        self._update_ui_state()

    # ==============================================================================
    #  UI Initialization Helpers
    # ==============================================================================
    def _init_ui(self) -> None:
        """
        Performs widget tweaks that are independent from runtime data.

        For example, sets the preview table to be read-only.
        """
        # Prevent editing in the preview table; only allow viewing
        self.tablePreview.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore[arg-type]

    # ==============================================================================
    #  Signal Wiring
    # ==============================================================================
    def _connect_signals(self) -> None:
        """
        Connects Qt signals from UI elements to their handler methods.

        - Dropdowns for type, version, and level call corresponding methods when changed.
        - 'Load Geo' button invokes CSV loading.
        - 'Test Expression' button applies filters and emits results.
        - Column list changes trigger validation of preview button.
        - Double-click on field/value lists inserts text into the query editor.
        - Operators buttons insert text snippets into the query editor.
        - 'Clear Expression' button clears the query editor.
        """
        # Populate version combo when type changes
        self.comboGeoType.currentTextChanged.connect(self._on_geo_type)
        # Populate level combo when version changes
        self.comboGeoVersion.currentTextChanged.connect(self._on_geo_version)
        # Remember the CSV path when level changes
        self.comboGeoLevel.currentTextChanged.connect(self._on_geo_level)
        # Load the CSV when 'Load Geo' is clicked
        self.buttonLoadGeo.clicked.connect(self._load_csv)

        # Apply filters and emit results when 'Test Expression' is clicked
        self.btnTestExpr.clicked.connect(self._apply_and_emit)
        # Validate column selection when any column checkbox changes
        self.listColumns.itemChanged.connect(self._validate_selection)

        # Insert field name into query when field is double-clicked
        self.listFields.itemDoubleClicked.connect(self._insert_field)
        # Insert value literal into query when value is double-clicked
        self.listValues.itemDoubleClicked.connect(self._insert_value)
        # Set up operator shortcut buttons (==, !=, <, >, etc.)
        self._setup_query_operators()

        # Clear the query editor when 'Clear Expression' is clicked
        self.btnClearExpr.clicked.connect(self.textExpr.clear)

    # ==============================================================================
    #  Operator Shortcut Buttons
    # ==============================================================================
    def _setup_query_operators(self) -> None:
        """
        Connects operator buttons (Eq, Ne, Lt, Gt, Le, Ge, And, Or, Like, In, Not)
        to insert corresponding text into the query editor at the cursor position.
        """
        ops = [
            (self.btnEq, " == "),
            (self.btnNe, " != "),
            (self.btnLt, " < "),
            (self.btnGt, " > "),
            (self.btnLe, " <= "),
            (self.btnGe, " >= "),
            (self.btnAnd, " and "),
            (self.btnOr, " or "),
            (self.btnLike, " like "),
            (self.btnIn, " in "),
            (self.btnNot, " not "),
        ]
        for btn, txt in ops:
            # Insert the operator text into the query editor when clicked
            btn.clicked.connect(lambda _=None, t=txt: self._insert_text(t))

    # ==============================================================================
    #  Directory Navigation Helpers
    # ==============================================================================
    def _populate_geo_types(self) -> None:
        """
        Fills the 'Type' combo box with subdirectories of BASE_DIR.

        Lists only directories, sorted alphabetically. If at least one type
        exists, triggers _on_geo_type for the first type.
        """
        self.comboGeoType.clear()
        # List all directories under BASE_DIR
        types = sorted(d for d in os.listdir(self.BASE_DIR) if os.path.isdir(os.path.join(self.BASE_DIR, d)))
        self.comboGeoType.addItems(types)
        if self.comboGeoType.count():
            # If at least one type, populate versions for the first entry
            self._on_geo_type(self.comboGeoType.currentText())

    def _on_geo_type(self, gtype: str) -> None:
        """
        Populates the 'Version' combo box when a 'Type' is selected.

        - Lists subdirectories under BASE_DIR/gtype.
        - If at least one version exists, triggers _on_geo_version for the first version.
        """
        path = os.path.join(self.BASE_DIR, gtype)
        self.comboGeoVersion.clear()
        # List directories under the selected type
        versions = sorted(d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)))
        self.comboGeoVersion.addItems(versions)
        if self.comboGeoVersion.count():
            # If at least one version, populate levels for the first entry
            self._on_geo_version(self.comboGeoVersion.currentText())

    def _on_geo_version(self, version: str) -> None:
        """
        Populates the 'Level' combo box when a 'Version' is selected.

        - Lists CSV files (without .csv extension) under BASE_DIR/type/version.
        - If at least one level exists, triggers _on_geo_level for the first level.
        """
        gtype = self.comboGeoType.currentText()
        folder = os.path.join(self.BASE_DIR, gtype, version)
        self.comboGeoLevel.clear()
        # List all .csv files in the folder and strip their extensions
        levels = [os.path.splitext(f)[0] for f in sorted(f for f in os.listdir(folder) if f.lower().endswith(".csv"))]
        self.comboGeoLevel.addItems(levels)
        if self.comboGeoLevel.count():
            # If at least one level, set the pending file path
            self._on_geo_level(self.comboGeoLevel.currentText())

    def _on_geo_level(self, level: str) -> None:
        """
        Records the final CSV path when a 'Level' is chosen.

        Builds the absolute path BASE_DIR/type/version/level.csv and stores
        it in _pending_fn. Then updates UI state to enable/disable buttons.
        """
        gtype = self.comboGeoType.currentText()
        version = self.comboGeoVersion.currentText()
        # Construct the absolute file path to the chosen CSV
        self._pending_fn = os.path.join(self.BASE_DIR, gtype, version, f"{level}.csv")
        # Enable or disable buttons based on whether this file exists
        self._update_ui_state()

    # ==============================================================================
    #  File Loading & Preview
    # ==============================================================================
    def _load_csv(self) -> None:
        """
        Reads the selected CSV file and bootstraps UI lists for fields, values, and columns.

        Steps:
          1. Check that _pending_fn is valid and file exists; otherwise show an info message.
          2. Use csv.Sniffer to detect delimiter (comma or semicolon) from a sample.
          3. Attempt to read the entire file into _df_raw with dtype=str.
          4. On failure, show a warning message.
          5. If successful, populate field and column lists, update preview, and UI state.
        """
        # Ensure a pending filename is set and exists on disk
        if not (fn := self._pending_fn) or not os.path.exists(fn):
            QMessageBox.information(self, "Geo data", "No valid path selected.")
            return

        # Detect delimiter by reading a sample of the file
        with open(fn, newline="", encoding="utf-8") as fh:
            sample = fh.read(SAMPLE_SIZE)
            try:
                sep = csv.Sniffer().sniff(sample, delimiters=[",", ";"]).delimiter  # type: ignore[arg-type]
            except csv.Error:
                # Default to comma if sniffing fails
                sep = ","

        # Attempt to read the full CSV into a DataFrame with all text columns
        try:
            raw = pd.read_csv(fn, sep=sep, dtype=str, engine="python")
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not read file:\n{exc}")
            return

        # Store the raw DataFrame and set up lists for fields, values, and columns
        self._df_raw = raw
        self._populate_field_and_column_lists()
        # Show the initial raw preview
        self._update_preview()
        # Update UI state now that data is loaded
        self._update_ui_state()

    def _populate_field_and_column_lists(self) -> None:
        """
        Fills the 'Fields' and 'Columns' list widgets after loading a CSV.

        - Fields list shows all column names as clickable items (double-click inserts into query).
        - Columns list shows all column names with checkboxes (checked by default).
        - Disables signals temporarily to prevent validation triggering prematurely.
        """
        cols = list(self._df_raw.columns.astype(str))

        # Populate 'Fields' list with all column names
        self.listFields.clear()
        self.listFields.addItems(cols)

        # Populate 'Columns' list with checkable items
        self.listColumns.blockSignals(True)
        self.listColumns.clear()
        for col in cols:
            item = QListWidgetItem(col)
            # Make each item checkable
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # type: ignore[arg-type]
            # Check all by default so preview shows all columns initially
            item.setCheckState(Qt.Checked)  # type: ignore[arg-type]
            self.listColumns.addItem(item)
        self.listColumns.blockSignals(False)
        # Validate that at least one column is selected
        self._validate_selection()

    def _update_preview(self) -> None:
        """
        Refreshes the right-hand preview table using the current _df_view and selected columns.

        - If _df_view is None, clears the table.
        - Otherwise, gathers checked column names and filters _df_view to those columns.
        - Builds a QStandardItemModel from the filtered DataFrame and sets it on tablePreview.
        """
        if self._df_view is None:
            # No filtered DataFrame to show
            self.tablePreview.setModel(None)
            return

        # Build a list of active columns based on checked state
        selected = [self.listColumns.item(i).text() for i in range(self.listColumns.count()) if self.listColumns.item(i).checkState() == Qt.Checked]  # type: ignore[arg-type]
        if not selected:
            # If no columns are selected, clear the table
            self.tablePreview.setModel(None)
            return

        # Filter _df_view to only the selected columns
        df = self._df_view[selected]
        # Create a new model with the same shape as filtered DataFrame
        model = QStandardItemModel(df.shape[0], df.shape[1], self)
        # Set header labels to column names
        model.setHorizontalHeaderLabels(df.columns.tolist())

        # Populate each cell with its string representation
        for r in range(df.shape[0]):
            for c, col in enumerate(df.columns):
                model.setItem(r, c, QStandardItem(str(df.iat[r, c])))

        # Attach the model to the preview table and adjust column widths
        self.tablePreview.setModel(model)
        self.tablePreview.resizeColumnsToContents()

    # ==============================================================================
    #  Query-Builder Helpers
    # ==============================================================================
    def _insert_field(self, itm: QListWidgetItem) -> None:
        """
        Inserts a protected column name (with backticks) into the query editor when a field is double-clicked.

        Also populates the 'Values' list with unique values from that column (up to a max).
        """
        field = itm.text()
        # Wrap the field name in backticks and insert into the query text
        self._insert_text(f"`{field}`")

        # Build a list of unique values (ignoring NaN) for that field
        uniques = self._df_raw[field].dropna().unique()
        # Populate the values list up to the maximum allowed
        self.listValues.clear()
        for val in uniques[:MAX_UNIQUE_VALUES]:
            self.listValues.addItem(str(val))

    def _insert_value(self, itm: QListWidgetItem) -> None:
        """
        Inserts a literal value into the query editor when a value is double-clicked.

        - If the value is numeric, inserts it as-is.
        - Otherwise, wraps it in single quotes.
        """
        val = itm.text()
        # Check if the value is a number (allowing one decimal point)
        if val.replace(".", "", 1).isdigit():
            self._insert_text(val)
        else:
            # Quote non-numeric strings
            self._insert_text(f"'{val}'")

    def _insert_text(self, txt: str) -> None:
        """
        Appends the given text at the current cursor position in the query editor.

        Moves the cursor to after the inserted text and focuses the editor.
        """
        cur = self.textExpr.textCursor()
        cur.insertText(txt)
        self.textExpr.setTextCursor(cur)
        self.textExpr.setFocus()

    # ==============================================================================
    #  Validation / Enabling Logic
    # ==============================================================================
    def _validate_selection(self) -> None:
        """
        Enables the 'Test Expression' button only when at least one column is checked.

        - Scans the column list for any item with checkState == Checked.
        - Enables btnTestExpr if at least one column is selected; otherwise disables it.
        """
        any_checked = any(self.listColumns.item(i).checkState() == Qt.Checked for i in range(self.listColumns.count()))  # type: ignore[arg-type]
        self.btnTestExpr.setEnabled(any_checked)

    # ==============================================================================
    #  Main Processing – called by "Test / Preview"
    # ==============================================================================
    def _apply_and_emit(self) -> None:
        """
        Applies the query expression and column selection, updates the preview,
        and emits the filtered DataFrame with metadata.

        Steps:
          1. If no raw DataFrame exists, do nothing.
          2. Retrieve the expression from the text editor and strip whitespace.
          3. If an expression is provided, attempt to evaluate it via df.query.
             - On invalid expression, show a warning and return.
          4. Build a list of checked columns.
             - If none are checked, return.
          5. Create a new DataFrame with the filtered rows and selected columns.
          6. Store this in _df_view, update the preview table, and adjust widths.
          7. Emit the filterReady signal with:
             - "df_filtered": the filtered DataFrame,
             - "selected_columns": list of column names,
             - "meta": dict with "type", "version", and "level" from current selections.
        """
        if self._df_raw is None:
            # No data loaded yet
            return

        df = self._df_raw

        # Get the filter expression from the text editor
        expr = self.textExpr.toPlainText().strip()
        if expr:
            try:
                # Attempt to filter using pandas query (Python engine)
                df = df.query(expr, engine="python")
                self._expr_valid = True
            except Exception as exc:
                # If expression is invalid, notify user and abort
                self._expr_valid = False
                QMessageBox.warning(self, "Filter", f"Invalid filter:\n{exc}")
                return

        # Build list of columns that remain checked
        active_cols = [
            self.listColumns.item(i).text() for i in range(self.listColumns.count()) if self.listColumns.item(i).checkState() == Qt.Checked  # type: ignore[arg-type]
        ]
        if not active_cols:
            # No columns selected; cannot proceed
            return

        # Create a DataFrame with selected columns and reset its index
        df_sel = df.reset_index(drop=True)[active_cols].copy()
        self._df_view = df_sel
        # Update the preview table to show filtered data
        self._update_preview()
        # Adjust table width to fit content
        self._adjust_table_width()

        # Emit filtered data, selected columns, and metadata to listeners
        self.filterReady.emit(
            {
                "df_filtered": df_sel,
                "selected_columns": active_cols,
                "meta": {
                    "type": self.comboGeoType.currentText(),
                    "version": self.comboGeoVersion.currentText(),
                    "level": self.comboGeoLevel.currentText(),
                },
            }
        )

    # ==============================================================================
    #  UI State Update Helper
    # ==============================================================================
    def _update_ui_state(self) -> None:
        """
        Enables or disables buttons based on internal state.

        - 'Load Geo' is enabled only when a valid _pending_fn exists.
        - 'Test Expression' is enabled only when a file is loaded (i.e., _df_raw is not None)
          and a valid path exists.
        """
        has_file = bool(self._pending_fn and os.path.exists(self._pending_fn))
        # Enable 'Load Geo' if the selected file path points to an existing file
        self.buttonLoadGeo.setEnabled(has_file)
        # Enable 'Test Expression' only if a file is loaded into _df_raw
        self.btnTestExpr.setEnabled(has_file and self._df_raw is not None)

    # ==============================================================================
    #  Navigation Guard Methods
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Allows navigation to the next step only when a filtered DataFrame exists,
        is non-empty, and at least one column is checked.

        Returns True when:
          - _df_view is not None and not empty.
          - At least one column in listColumns is checked.
        """
        if self._df_view is None or self._df_view.empty:
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
    #  Table Width Adjustment Helper
    # ==============================================================================
    def _adjust_table_width(self) -> None:
        """
        Adjusts the preview table’s width to fit its contents without cutting off any data.

        Steps:
          1. If no filtered DataFrame or it is empty, do nothing.
          2. Resize each column to fit its content and accumulate total width.
          3. Add padding for vertical scrollbar, margins, and splitter handle.
          4. Compute maximum allowed width as 50% of the window width.
          5. Set splitter sizes so that left pane (filters) and right pane (preview)
             share the window appropriately, with the preview at most 50% wide,
             and left pane at least 400px.
        """
        if self._df_view is None or self._df_view.empty:
            return

        # Reference to the preview table
        table = self.tablePreview

        # Calculate total width required to display all columns fully
        total_width = 0
        for i in range(table.model().columnCount()):
            table.resizeColumnToContents(i)
            total_width += table.columnWidth(i)

        # Add padding allowances:
        # - Vertical scrollbar: 20px
        # - Table margins: 2 * 10px
        # - GroupBox margins: 2 * 10px
        # - Splitter handle: 4px
        # - Extra safety: 10px
        total_width += 74

        # Get the current window width
        window_width = self.width()
        # The preview pane should occupy at most half the window width
        max_width = window_width * 0.5

        # Use the lesser of required width and half-window width
        splitter_width = min(total_width, max_width)
        # Ensure the left pane (filter panel) remains at least 400px wide
        left_width = max(window_width - splitter_width, 400)

        # Apply the sizes to the splitter: [left pane, right pane]
        self.splitMain.setSizes([left_width, window_width - left_width])
