"""
Pure *viewer* for multi-sheet Excel workbooks.

Why it exists
-------------
* Other parts of the pipeline always operate on **single** sheets.
* This widget therefore lets the user pick one sheet and displays a read-only
  preview, nothing more.

Where it is used
----------------
The main state-machine (``MainWindow``) shows this dialog after the user has
selected a ``.xlsx`` / ``.xls`` file.  The chosen sheet is forwarded downstream
via `selectionReady` as soon as it is selected.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTableView

from src.views.sheet_select.ui.excel_sheet_window_ui import Ui_ExcelSheetWindow


# ==============================================================================
#  SheetSelectView: Sheet-selector with preview for Excel workbooks
# ==============================================================================
class SheetSelectView(QMainWindow, Ui_ExcelSheetWindow):
    """
    Displays a dropdown of sheet names and shows a preview of the selected sheet.

    This window allows the user to select exactly one sheet from a multi-sheet
    Excel file.  The sheet’s contents appear in a read-only table.  When a sheet
    is chosen, the DataFrame and sheet name are emitted via selectionReady.
    """

    # Signal emitted when the user selects a sheet. Payload: {"df": DataFrame, "sheet": sheet_name}
    selectionReady = Signal(dict)

    # --------------------------------------------------------------------------
    #  Construction
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the SheetSelectView.

        - Calls Ui_ExcelSheetWindow.setupUi to build the interface.
        - Configures the preview table to be read-only.
        - Connects the sheet-selection combo box to the internal handler.
        - Sets up runtime placeholders for the Excel file and DataFrame.
        """
        super().__init__()
        # Load UI components from the Qt Designer file
        self.setupUi(self)

        # ----------------------------------------------------------------------
        #  Preview Table Configuration
        # ----------------------------------------------------------------------
        # Prevent editing in the preview table so users cannot modify data
        self.tablePreview.setEditTriggers(QTableView.NoEditTriggers)  # type: ignore[arg-type]

        # ----------------------------------------------------------------------
        #  GUI Signal Wiring
        # ----------------------------------------------------------------------
        # When the selected sheet changes, call _on_sheet_changed
        self.comboSheet.currentTextChanged.connect(self._on_sheet_changed)

        # ----------------------------------------------------------------------
        #  Runtime Data Holders
        # ----------------------------------------------------------------------
        # Holds the loaded ExcelFile object after load_excel
        self._xls: Optional[pd.ExcelFile] = None
        # Holds the DataFrame for the currently displayed sheet
        self._df_current: Optional[pd.DataFrame] = None

    # ==============================================================================
    #  Public API: Load Excel File
    # ==============================================================================
    def load_excel(self, path: str) -> None:
        """
        Opens the Excel file at the given path and populates the sheet dropdown.

        Steps:
          1. Attempts to load the Excel file via pandas.ExcelFile.
             - On failure, shows a QMessageBox with error details and returns.
          2. Clears any existing items in the sheet combo box.
          3. Adds all sheet names from the Excel file to the combo box.
          4. If at least one sheet exists, triggers _on_sheet_changed for the first sheet.
        """
        try:
            # Try to open the workbook; pandas.ExcelFile handles multiple sheets
            self._xls = pd.ExcelFile(path)
        except Exception as exc:
            # Display a critical error dialog if the file cannot be opened
            QMessageBox.critical(self, "Error", f"Failed to open Excel file:\n{exc}")
            return

        # Clear existing sheet names and add new ones
        self.comboSheet.clear()
        self.comboSheet.addItems(self._xls.sheet_names)
        # Automatically select and display the first sheet if available
        if self.comboSheet.count():
            self._on_sheet_changed(self.comboSheet.currentText())

    # ==============================================================================
    #  Internal Helpers
    # ==============================================================================
    def _on_sheet_changed(self, sheet: str) -> None:
        """
        Handles the event when the user selects a different sheet from the combo.

        Steps:
          1. If no sheet is provided or the ExcelFile is not loaded, do nothing.
          2. Parse the selected sheet into a DataFrame with no header row.
          3. Store the DataFrame in _df_current.
          4. Call _update_preview to render the DataFrame in the table view.
          5. Call _emit to notify downstream listeners of the new selection.
        """
        if not (sheet and self._xls):
            # Do nothing if no valid sheet or Excel file is available
            return

        # Read the selected sheet into a DataFrame, treating all cells as strings
        df = self._xls.parse(sheet, dtype=str, header=None).reset_index(drop=True)
        # Save a reference to the current DataFrame
        self._df_current = df
        # Update the preview table with the newly loaded DataFrame
        self._update_preview(df)
        # Emit the selection to any connected listeners
        self._emit()

    def _update_preview(self, df: pd.DataFrame) -> None:
        """
        Renders the given DataFrame in the read-only QTableView.

        Steps:
          1. Creates a QStandardItemModel with the same dimensions as df.
          2. Iterates through each cell of df, placing its string value into the model.
          3. Attaches the model to tablePreview.
          4. Calls resizeColumnsToContents to adjust column widths for readability.
        """
        # Create a standard item model matching df’s shape
        model = QStandardItemModel(df.shape[0], df.shape[1], self)
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                # Convert each cell to string and place into the model
                model.setItem(r, c, QStandardItem(str(df.iat[r, c])))
        # Set the model on the preview table and adjust column sizes
        self.tablePreview.setModel(model)
        self.tablePreview.resizeColumnsToContents()

    def _emit(self) -> None:
        """
        Emits the selectionReady signal with the current sheet’s DataFrame and name.

        Steps:
          1. If _df_current is not set, do nothing.
          2. Otherwise, emit a dictionary containing a copy of the DataFrame and the selected sheet name.
        """
        if self._df_current is None:
            # No DataFrame to emit, so skip
            return

        # Emit the payload for any connected slots
        self.selectionReady.emit({"df": self._df_current.copy(), "sheet": self.comboSheet.currentText()})

    # ==============================================================================
    #  Navigation Hooks
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Indicates whether the wizard can proceed to the next step.

        Returns True only if a sheet has been successfully loaded and is not empty.
        """
        return self._df_current is not None and not self._df_current.empty

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Indicates whether the wizard can go back to the previous step.

        Always returns True, allowing backward navigation.
        """
        return True
