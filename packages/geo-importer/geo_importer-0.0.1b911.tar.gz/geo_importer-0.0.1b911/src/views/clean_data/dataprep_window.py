from __future__ import annotations

"""Qt window that provides an interface for cleaning tabular data.

All heavy lifting is done in helper modules. This class mostly wires user
actions to the underlying logic objects.
"""

import logging
from typing import Tuple

import pandas as pd
from PySide6.QtCore import QItemSelection, QItemSelectionModel, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QAbstractItemView, QMainWindow, QMenu, QTableWidgetItem

from .dataprep_helpers import export_csv, export_excel, validate_first_row
from .dataprep_logic import DataPrepLogic
from .table_logic import (
    autosize_columns,
    delete_cols,
    delete_rows,
    fill_table,
    get_table_data,
    insert_col,
    insert_row,
    transpose_table,
    update_table_data,
)
from .ui.dataprep_window_ui import Ui_DataPrepWindow
from .undo_redo_logic import UndoRedoLogic

logger = logging.getLogger(__name__)

Coord = Tuple[int, int]  # (row, col) coordinate pair


# ======================================================================
#  Main Window: CleanDataView
# ======================================================================
class CleanDataView(QMainWindow, Ui_DataPrepWindow):
    """Light-weight window that delegates its functionality to helper modules."""

    prepReady = Signal(pd.DataFrame)

    def __init__(self) -> None:
        """
        Set up widgets, logic helpers and default shortcuts.

        Steps:
          1. Call setupUi to build the interface.
          2. Instantiate DataPrepLogic and UndoRedoLogic.
          3. Configure the table widget and context menu behaviour.
          4. Wire all controls and shortcuts to their handlers.
          5. Create a small demo table and initialise undo history.
        """
        super().__init__()
        self.setupUi(self)

        # Instantiate logic helpers
        self._logic = DataPrepLogic()
        self._undo = UndoRedoLogic(self.tableWidget, self.btnUndo, self.btnRedo)

        # ------------------------------------------------------------------
        #  Table configuration
        # ------------------------------------------------------------------
        # Allow multi-item selection and custom context menus
        self.tableWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # type: ignore[attr-defined]
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectItems)  # type: ignore[attr-defined]
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore[attr-defined]
        self.tableWidget.customContextMenuRequested.connect(self._on_ctx_menu)
        self.tableWidget.itemChanged.connect(self._undo.item_changed)

        # Keyboard shortcuts for copy/paste/cut
        QShortcut(QKeySequence.Copy, self.tableWidget, activated=self._copy)  # type: ignore[attr-defined]
        QShortcut(QKeySequence.Paste, self.tableWidget, activated=self._paste)  # type: ignore[attr-defined]
        QShortcut(QKeySequence.Cut, self.tableWidget, activated=self._cut)  # type: ignore[attr-defined]

        # Spin boxes and mode selector trigger selection update
        for sb in (self.spinRowN, self.spinColN, self.spinRowShift, self.spinColShift):
            sb.valueChanged.connect(self.update_selection)
        self.comboMode.currentTextChanged.connect(self.update_selection)
        self.comboMode.setCurrentText("OR")

        # Buttons for selection controls
        self.btnReset.clicked.connect(self.reset_selection)
        self.btnApply.clicked.connect(self.apply_selection)

        # Buttons for table operations
        self.btnTranspose.clicked.connect(self.transpose_table)
        self.btnExportCsv.clicked.connect(self.export_csv)
        self.btnExportExcel.clicked.connect(self.export_excel)

        # Undo/redo button connections
        self.btnUndo.clicked.connect(self.undo_change)
        self.btnRedo.clicked.connect(self.redo_change)
        self.btnUndo.setEnabled(False)
        self.btnRedo.setEnabled(False)

        # ------------------------------------------------------------------
        #  Initialize demo table and undo history
        # ------------------------------------------------------------------
        self._undo.tracking_enabled = False
        self._initialize_demo_table()
        self._undo.init_state()
        self._undo.tracking_enabled = True

        # Initial selection
        self.update_selection()

    # ==================================================================
    #  Loading Data
    # ==================================================================
    def load_dataframe(self, df: pd.DataFrame) -> None:
        """
        Display the provided DataFrame inside the table widget.

        Steps:
          1. Normalize column names via DataPrepLogic.
          2. Temporarily disable undo tracking and fill the table.
          3. Reset undo history and re-enable tracking.
        """
        df2 = self._logic.load_dataframe(df)
        self._undo.tracking_enabled = False
        fill_table(self.tableWidget, df2.values.tolist())
        self._undo.clear()
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def load_csv(self, path: str) -> None:
        """
        Load a CSV file from disk and display it in the table.

        Steps:
          1. Delegate CSV reading to DataPrepLogic.load_csv.
          2. Forward resulting DataFrame to load_dataframe.
        """
        df = self._logic.load_csv(path)
        self.load_dataframe(df)

    # ==================================================================
    #  Context Menu
    # ==================================================================
    def _on_ctx_menu(self, pos) -> None:
        """
        Show a menu for inserting, deleting and clipboard actions.

        Steps:
          1. Create a QMenu at the cursor position.
          2. Add insertion, copy/paste, cut, and deletion actions.
          3. Execute the menu and invoke the chosen handler.
        """
        m = QMenu(self)
        actions = {
            m.addAction("Insert Row"): self._insert_row,
            m.addAction("Insert Column"): self._insert_col,
            m.addSeparator(): None,
            m.addAction("Copy"): self._copy,
            m.addAction("Paste"): self._paste,
            m.addAction("Cut"): self._cut,
            m.addSeparator(): None,
            m.addAction("Delete Row"): self._del_rows,
            m.addAction("Delete Column"): self._del_cols,
        }
        chosen = m.exec(self.tableWidget.viewport().mapToGlobal(pos))
        if chosen:
            actions[chosen]()

    # ==================================================================
    #  Row/Column Operations
    # ==================================================================
    def _insert_row(self) -> None:
        """
        Insert a new row above the current selection.

        Steps:
          1. Save snapshot for undo.
          2. Disable tracking and call insert_row helper.
          3. Reinitialize undo state and re-enable tracking.
        """
        self._undo.push_snapshot()
        self._undo.tracking_enabled = False
        insert_row(self.tableWidget)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def _insert_col(self) -> None:
        """
        Insert a new column left of the current selection.

        Steps:
          1. Save snapshot for undo.
          2. Disable tracking and call insert_col helper.
          3. Reinitialize undo state and re-enable tracking.
        """
        self._undo.push_snapshot()
        self._undo.tracking_enabled = False
        insert_col(self.tableWidget)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def _del_rows(self) -> None:
        """
        Remove all selected rows.

        Steps:
          1. Gather selected row indices.
          2. If none, return.
          3. Save snapshot, delete rows, refresh undo state.
        """
        rows = {i.row() for i in self.tableWidget.selectedIndexes()}
        if not rows:
            return
        self._undo.push_snapshot()
        self._undo.tracking_enabled = False
        delete_rows(self.tableWidget, rows)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def _del_cols(self) -> None:
        """
        Remove all selected columns.

        Steps:
          1. Gather selected column indices.
          2. If none, return.
          3. Save snapshot, delete columns, refresh undo state.
        """
        cols = {i.column() for i in self.tableWidget.selectedIndexes()}
        if not cols:
            return
        self._undo.push_snapshot()
        self._undo.tracking_enabled = False
        delete_cols(self.tableWidget, cols)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    # ==================================================================
    #  Clipboard Operations
    # ==================================================================
    def _copy(self) -> None:
        """
        Store the current selection in the copy buffer.

        Step:
          1. Collect coordinates of selected cells and delegate to logic.
        """
        coordinates = {(i.row(), i.column()) for i in self.tableWidget.selectedIndexes()}
        self._logic.prepare_copy_data(sorted(coordinates), get_table_data(self.tableWidget))

    def _paste(self) -> None:
        """
        Paste the stored cells starting at the selection anchor.

        Steps:
          1. Determine destination coordinates from current selection.
          2. Verify pattern matches stored copy buffer.
          3. Save snapshot, compute pasted data, update table, refresh undo.
        """
        dest = self.tableWidget.selectedIndexes()
        if not dest:
            return
        coordinates = {(i.row(), i.column()) for i in dest}
        if not self._logic.pattern_matches(coordinates):
            return
        self._undo.push_snapshot()
        anchor_row = min(i.row() for i in dest)
        anchor_col = min(i.column() for i in dest)
        new_data = self._logic.get_paste_data(anchor_row, anchor_col, get_table_data(self.tableWidget))
        self._undo.tracking_enabled = False
        update_table_data(self.tableWidget, new_data)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def _cut(self) -> None:
        """
        Cut the selected cells to the clipboard pattern.

        Steps:
          1. Save snapshot and copy selection.
          2. Replace selected cells with empty strings.
          3. Refresh undo state.
        """
        self._undo.push_snapshot()
        self._copy()
        self._undo.tracking_enabled = False
        for idx in self.tableWidget.selectedIndexes():
            self.tableWidget.setItem(idx.row(), idx.column(), QTableWidgetItem(""))
        self._undo.init_state()
        self._undo.tracking_enabled = True

    def transpose_table(self) -> None:
        """
        Swap rows and columns of the table.

        Steps:
          1. Save snapshot for undo.
          2. Disable tracking and call transpose helper.
          3. Refresh undo state.
        """
        self._undo.push_snapshot()
        self._undo.tracking_enabled = False
        transpose_table(self.tableWidget)
        self._undo.init_state()
        self._undo.tracking_enabled = True

    # ==================================================================
    #  Selection Helpers
    # ==================================================================
    def update_selection(self) -> None:
        """
        Highlight cells based on spin boxes and mode.

        Steps:
          1. Compute coordinates via DataPrepLogic.compute_selection.
          2. Build a QItemSelection for those coordinates.
          3. Apply selection while blocking signals.
        """
        coordinates = self._logic.compute_selection(
            row_n=self.spinRowN.value(),
            col_n=self.spinColN.value(),
            row_shift=self.spinRowShift.value(),
            col_shift=self.spinColShift.value(),
            mode=self.comboMode.currentText(),
            row_count=self.tableWidget.rowCount(),
            col_count=self.tableWidget.columnCount(),
        )
        selection = QItemSelection()
        for r, c in coordinates:
            idx = self.tableWidget.model().index(r, c)
            selection.merge(QItemSelection(idx, idx), QItemSelectionModel.Select)  # type: ignore

        # Apply new selection without triggering signals
        self.tableWidget.blockSignals(True)
        self.tableWidget.setUpdatesEnabled(False)
        self.tableWidget.clearSelection()
        self.tableWidget.selectionModel().select(selection, QItemSelectionModel.Select)  # type: ignore
        self.tableWidget.setUpdatesEnabled(True)
        self.tableWidget.blockSignals(False)

    def reset_selection(self) -> None:
        """
        Clear selection controls and table selection.

        Steps:
          1. Reset spin boxes and mode to 'OR'.
          2. Clear any table selection.
        """
        for sb in (self.spinRowN, self.spinColN, self.spinRowShift, self.spinColShift):
            sb.setValue(0)
        self.comboMode.setCurrentText("OR")
        self.tableWidget.clearSelection()

    def apply_selection(self) -> None:
        """
        Apply the previewed selection to the table widget.

        Steps:
          1. Recompute and highlight selection.
          2. Give the table widget focus.
        """
        self.update_selection()
        self.tableWidget.setFocus()

    # ==================================================================
    #  Export and Validation
    # ==================================================================
    def export_csv(self) -> None:
        """
        Delegate exporting the table to CSV.

        Step:
          1. Gather table data and call export_csv helper.
        """
        export_csv(get_table_data(self.tableWidget), self)

    def export_excel(self) -> None:
        """
        Delegate exporting the table to Excel.

        Step:
          1. Gather table data and call export_excel helper.
        """
        export_excel(get_table_data(self.tableWidget), self)

    def validate_first_row(self) -> str:
        """
        Run first row validation helper.

        Step:
          1. Call validate_first_row and return its result.
        """
        return validate_first_row(self.tableWidget, self)

    # ==================================================================
    #  Undo/Redo Actions
    # ==================================================================
    def undo_change(self) -> None:
        """
        Undo the last table modification.

        Step:
          1. Delegate to UndoRedoLogic.undo.
        """
        self._undo.undo()

    def redo_change(self) -> None:
        """
        Redo the last undone change.

        Step:
          1. Delegate to UndoRedoLogic.redo.
        """
        self._undo.redo()

    # ==================================================================
    #  Emitting Data
    # ==================================================================
    def emit_data(self) -> None:
        """
        Emit the current table as a DataFrame via prepReady signal.

        Steps:
          1. Convert table data to DataFrame.
          2. Emit prepReady with the DataFrame.
        """
        df = self._logic.convert_table_to_dataframe(get_table_data(self.tableWidget), self.tableWidget.columnCount())
        self.prepReady.emit(df)

    _emit_data = emit_data

    def closeEvent(self, event) -> None:
        """
        Emit data before the window closes.

        Steps:
          1. Call emit_data to send final DataFrame.
          2. Delegate to base closeEvent.
        """
        self._emit_data()
        super().closeEvent(event)

    # ==================================================================
    #  Demo Initialization
    # ==================================================================
    def _initialize_demo_table(self) -> None:
        """
        Fill the table with a small sample grid on startup.

        Steps:
          1. Build a 5×5 grid with placeholder strings.
          2. Insert it into the table widget and resize columns.
        """
        demo = [[f"R{r}C{c}" for c in range(5)] for r in range(5)]
        fill_table(self.tableWidget, demo)
        autosize_columns(self.tableWidget)
