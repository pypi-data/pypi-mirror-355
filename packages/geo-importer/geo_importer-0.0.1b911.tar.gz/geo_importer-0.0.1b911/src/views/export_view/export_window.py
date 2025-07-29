from __future__ import annotations

import pandas as pd

from src.views.export_view.export_logic import ExportLogic
from src.views.export_view.ui.export_window_ui import Ui_ExportWindow

"""
Export window - maps selected columns to CSV + YAML and packages everything in a ZIP.

The UI definition is in *ui/excel_sheet_window.ui* (see Qt Designer). This
implementation populates the combos, validates inputs, and handles the
complete write/pack process.
"""

import logging
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QWidget

log = logging.getLogger(__name__)


# ==============================================================================
#  ExportView: Last wizard page for exporting data
# ==============================================================================
class ExportView(QWidget):
    """
    Last wizard page: CSV + YAML → ZIP.

    This window handles the final export of processed data, allowing users to:
      1. Select ID and value columns.
      2. Provide metadata about the dataset.
      3. Export the data as a ZIP file containing CSV and YAML files.
    """

    # Signal emitted when export finishes, carrying the absolute path of the saved ZIP
    exportFinished = Signal(str)

    # --------------------------------------------------------------------------
    #  Construction / Wiring
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the export window.

        - Creates an instance of ExportLogic to handle core export operations.
        - Calls internal methods to set up UI widgets and connect signals.
        """
        super().__init__()
        self._logic = ExportLogic()
        self._setup_ui()
        self._wire_signals()

    def _setup_ui(self) -> None:
        """
        Sets up the UI components by loading the Qt Designer form.

        - Instantiates Ui_ExportWindow and applies it to this widget.
        """
        self.ui = Ui_ExportWindow()
        self.ui.setupUi(self)

    def _wire_signals(self) -> None:
        """
        Connects UI signals to their respective handlers.

        - btn_export click → _on_export to start the export routine.
        - combo_id and combo_val changes → _update_status to refresh status label.
        """
        self.ui.btn_export.clicked.connect(self._on_export)
        self.ui.combo_id.currentTextChanged.connect(self._update_status)
        self.ui.combo_val.currentTextChanged.connect(self._update_status)

    # ==============================================================================
    #  Data Initialization (called by MainWindow before page is shown)
    # ==============================================================================
    def load_data(self, df_stats: pd.DataFrame) -> None:
        """
        Populates the dropdowns with column data from the provided DataFrame.

        Steps:
          1. If df_stats is None or empty, set status to indicate no data.
          2. Otherwise, obtain ID and value column lists from ExportLogic.
          3. Block signals on combo boxes to avoid premature status updates.
          4. Clear existing items in combo boxes.
          5. Add display names to combos while storing original column names as data.
          6. Unblock signals and set defaults if available.
          7. Call _update_status to reflect initial combo state.
        """
        if df_stats is None or df_stats.empty:
            self.ui.label_status.setText("No data available for export")
            return

        # Obtain lists of ID and value columns (display names and originals)
        id_display, id_cols, val_display, val_cols = self._logic.load_data(df_stats)

        # Prevent status updates while populating combos
        self.ui.combo_id.blockSignals(True)
        self.ui.combo_val.blockSignals(True)
        self.ui.combo_id.clear()
        self.ui.combo_val.clear()

        # Populate ID combo: display name shown, original name stored as data
        for display, original in zip(id_display, id_cols):
            self.ui.combo_id.addItem(display, original)
        # Populate Value combo similarly
        for display, original in zip(val_display, val_cols):
            self.ui.combo_val.addItem(display, original)

        # Re-enable signals after population
        self.ui.combo_id.blockSignals(False)
        self.ui.combo_val.blockSignals(False)

        # Select the first items if available
        if id_cols:
            self.ui.combo_id.setCurrentIndex(0)
        if val_cols:
            self.ui.combo_val.setCurrentIndex(0)

        # Update status label based on the populated combos
        self._update_status()

    # ==============================================================================
    #  Export Routine
    # ==============================================================================
    def _on_export(self) -> None:
        """
        Handles the export button click event.

        Steps:
          1. Validate that name, description, and source fields are not empty.
             - If any is empty, update status label and return.
          2. Obtain the original column names from combo_id and combo_val.
             - If either is missing or the same, update status and return.
          3. Open a file dialog for the user to choose the ZIP save location.
             - If no path chosen, abort.
          4. Gather metadata from UI fields (name, description, source, year, data_type).
          5. Call ExportLogic to export data and metadata to the selected ZIP path.
          6. On success, set status label to indicate completion and emit exportFinished.
          7. On any exception, log error and update status label accordingly.
        """
        # Validate dataset name
        if not (name := self.ui.edit_name.text().strip()):
            self.ui.label_status.setText("Please enter a name!")
            return
        # Validate description
        if not (descr := self.ui.edit_description.toPlainText().strip()):
            self.ui.label_status.setText("Please enter a description!")
            return
        # Validate source
        if not (source := self.ui.edit_source.text().strip()):
            self.ui.label_status.setText("Please enter a source!")
            return

        # Retrieve selected ID and value columns (original names stored as data)
        id_col = self.ui.combo_id.currentData()
        val_col = self.ui.combo_val.currentData()
        # Validate that both columns are selected and differ
        if not id_col or not val_col:
            self.ui.label_status.setText("Please pick ID and value columns!")
            return
        if id_col == val_col:
            self.ui.label_status.setText("ID and value column must differ!")
            return

        # Prompt user to select target ZIP file location
        file_path, _ = QFileDialog.getSaveFileName(self, "Save ZIP File", str(Path.home() / "exported_data.zip"), "ZIP Files (*.zip)")  # type: ignore[attr-defined]
        # If user canceled the dialog, do nothing
        if not file_path:
            return

        try:
            # Collect metadata from UI fields and combo selections
            metadata = self._logic.get_metadata(
                id_col=id_col,
                val_col=val_col,
                name=name,
                description=descr,
                source=source,
                year=self.ui.spin_year.value(),
                data_type=self.ui.combo_type.currentText(),
            )

            # Perform the export operation (CSV + YAML → ZIP)
            self._logic.export_data(id_col, val_col, metadata, file_path)

            # Indicate success and emit signal
            self.ui.label_status.setText(f"Successfully exported to: {file_path}")
            self.exportFinished.emit(file_path)
        except Exception as exc:
            # Log detailed traceback and set error status
            log.error("Export failed", exc_info=True)
            self.ui.label_status.setText(f"Export failed: {exc}")

    # ==============================================================================
    #  Small UX Helper
    # ==============================================================================
    def _update_status(self) -> None:
        """
        Updates the status label based on current selections.

        - Checks that combo_id has a non-empty text.
        - Checks that combo_val has a non-empty text and is not the same as combo_id.
        - Sets label to "Ready to export" if both are valid, otherwise prompts selection.
        """
        id_ok = bool(self.ui.combo_id.currentText())
        val_ok = bool(self.ui.combo_val.currentText()) and (self.ui.combo_val.currentText() != self.ui.combo_id.currentText())
        # Display appropriate prompt or success readiness
        self.ui.label_status.setText("Ready to export" if id_ok and val_ok else "Select ID / value columns")

    # ==============================================================================
    #  Wizard Navigation Hooks
    # ==============================================================================
    # noinspection PyMethodMayBeStatic
    def can_go_next(self) -> bool:
        """
        Indicates whether the wizard can move forward from this page.

        Always returns False because this is the last page.
        """
        return False

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Indicates whether the wizard can move back to the previous page.

        Always returns True to allow backward navigation.
        """
        return True
