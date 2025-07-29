from __future__ import annotations

"""Qt entry point that wires all view pages together.

The :class:`MainWindow` hosts every step of the import wizard in a stacked
layout and coordinates the data flow between them. It also provides the
sidebar, progress list and navigation buttons.
"""

import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.core.data_store import DataStore
from src.core.step_descriptions import STEP_DESCRIPTIONS
from src.core.steps import TITLE, Step
from src.views.auto_map.mapping_window import AutoMapView
from src.views.clean_data.dataprep_window import CleanDataView
from src.views.column_filter.filter_window import ColumnFilterView
from src.views.export_view.export_window import ExportView
from src.views.file_load.upload_window import FileLoadView
from src.views.geo_filter.geodata_window import GeoFilterView
from src.views.manual_map.manual_mapping_window import ManualMapView
from src.views.map_preview.preview_window import MapPreviewView
from src.views.pdf_area.pdf_select_window import PdfAreaView
from src.views.sheet_select.excel_sheet_window import SheetSelectView

# ------------------------------------------------------------------------------
# Configure root logger to DEBUG level
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Path to the application icon bundled with the package
ICON_PATH = Path(__file__).with_name("app_icon.png")


class MainWindow(QMainWindow):
    """
    Serves as the container window that embeds every individual view and manages navigation through steps.
    """

    # --------------------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the main window, constructs all sub-pages, builds navigation chrome, and shows the first step.
        """
        super().__init__()

        # Set up the stacked widget that holds each step's page
        self._stack = QStackedWidget(self)
        # Maintain a dictionary that tracks which steps have been completed
        self._steps_done = {step: False for step in Step}
        # Sequence of steps in the workflow; starts with UPLOAD
        self._seq: List[Step] = [Step.UPLOAD]
        # Track the current step (initially None, will be set later)
        self._cur: Step | None = None

        # Build and wire up the UI components
        self._create_pages()
        self._create_chrome()
        self._wire_signals()

        # Show the first step (UPLOAD) to start the workflow
        self._show(Step.UPLOAD)

    # ==========================================================================
    # Page Construction
    # ==========================================================================
    def _create_pages(self) -> None:
        """
        Instantiates every sub-window (view) and adds them to the stacked widget.
        """
        # Create each view in the pipeline
        self.pg_upload = FileLoadView()
        self.pg_pdf = PdfAreaView()
        self.pg_sheet = SheetSelectView()
        self.pg_prep = CleanDataView()
        self.pg_filter = ColumnFilterView()
        self.pg_geo = GeoFilterView()
        self.pg_mapping = AutoMapView()
        self.pg_manual = ManualMapView()
        self.pg_preview = MapPreviewView()
        self.pg_export = ExportView()

        # Add all view widgets to the QStackedWidget in the desired order
        for widget in (
            self.pg_upload,
            self.pg_pdf,
            self.pg_sheet,
            self.pg_prep,
            self.pg_filter,
            self.pg_geo,
            self.pg_mapping,
            self.pg_manual,
            self.pg_preview,
            self.pg_export,
        ):
            # Each widget occupies one index in the stacked widget
            self._stack.addWidget(widget)

    # ==========================================================================
    # Chrome (Navigation Bar and Sidebar) Construction
    # ==========================================================================
    def _create_chrome(self) -> None:
        """
        Builds the navigation buttons (Back/Next), the progress list on the left, and the description pane.
        """
        # Create Back and Next navigation buttons
        self.btn_back = QPushButton("Back")
        self.btn_next = QPushButton("Next")

        # Build the progress list, fixed width, with no focus
        self.lst_steps = QListWidget()
        self.lst_steps.setFixedWidth(400)
        self.lst_steps.setFocusPolicy(Qt.NoFocus)  # type: ignore[attr-defined]

        # Create description text browser below the list, read-only
        self.txt_description = QTextBrowser()
        self.txt_description.setReadOnly(True)
        # Provide an initial hint until a step is active
        self.txt_description.setHtml("<p><i>Select a step to see its description...</i></p>")
        self.txt_description.setFixedWidth(self.lst_steps.width())

        # Info button placed under the description
        self.btn_info = QPushButton("Info")

        # Layout for the right side: stacked widget on top, navigation buttons below
        right_layout = QVBoxLayout()
        right_layout.addWidget(self._stack)
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        right_layout.addLayout(nav_layout)

        # Layout for the left side: progress list, description, and info button
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.lst_steps, 1)  # gives stretch factor to expand list
        left_layout.addWidget(self.txt_description, 1)  # expandable description area
        left_layout.addWidget(self.btn_info)  # info button with no stretch

        # Combine left and right layouts into the root layout
        root_layout = QHBoxLayout()
        root_layout.addLayout(left_layout)
        root_layout.addLayout(right_layout)

        # Wrap layouts into a central QWidget
        wrapper = QWidget()
        wrapper.setLayout(root_layout)
        self.setCentralWidget(wrapper)

        # Set window title, default size, center on screen, and icon
        self.setWindowTitle("Import-Guide")
        self.resize(1500, 1100)
        # Center the window on the primary screen
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
        # Set application icon
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        # Populate the progress list based on the initial sequence
        self._rebuild_list()

    # ==========================================================================
    # Signal Connections
    # ==========================================================================
    def _wire_signals(self) -> None:
        """
        Connects signals from navigation buttons, info button, and child pages to their respective handlers.
        """
        # Navigation button clicks call the _shift method with direction
        self.btn_back.clicked.connect(lambda: self._shift(-1))
        self.btn_next.clicked.connect(lambda: self._shift(+1))
        # Info button shows additional step info
        self.btn_info.clicked.connect(self._on_info_clicked)

        # Connect each page's "ready" signals to the corresponding MainWindow handler
        # After upload, when finished, move to next step
        self.pg_upload.uploadFinished.connect(self._on_uploaded)
        # After PDF extraction is ready
        self.pg_pdf.extractionReady.connect(self._on_pdf_ready)
        # After Excel sheet selection is ready
        self.pg_sheet.selectionReady.connect(self._on_sheet_ready)
        # After DataPrep is done
        self.pg_prep.prepReady.connect(self._on_prep_ready)
        # After filter step is done
        self.pg_filter.filterReady.connect(self._on_filter_ready)
        # After geodata step is done
        self.pg_geo.filterReady.connect(self._on_geo_ready)
        # After mapping step is done
        self.pg_mapping.mappingDone.connect(self._on_mapping_done)
        # After manual mapping is done
        self.pg_manual.manualMappingDone.connect(self._on_manual_ready)
        # After export is finished, mark the EXPORT step as done
        self.pg_export.exportFinished.connect(lambda _: self._steps_done.update({Step.EXPORT: True}))

    # ==========================================================================
    # Navigation Helpers
    # ==========================================================================
    def _show(self, step: Step) -> None:
        """
        Switches the stacked widget to display the specified step and updates the navigation chrome.
        """
        # If this step is not yet in the sequence, append it and rebuild the list
        if step not in self._seq:
            self._seq.append(step)
            self._rebuild_list()

        # Update current step reference and set the stacked widget index
        self._cur = step
        self._stack.setCurrentIndex(list(Step).index(step))
        # Update the left sidebar and buttons to reflect new current step
        self._update_chrome()

    def _shift(self, delta: int) -> None:
        """
        Moves forward or backward in the sequence of steps by delta positions.
        Forwards allowed only if current step is done, except if current step is DATAPREP.
        """
        logger.debug(f"_shift called with delta={delta}, current step={self._cur}")
        # Calculate the target position
        pos = self._seq.index(self._cur) + delta
        # If out of valid range, do nothing
        if not 0 <= pos < len(self._seq):
            return

        # If moving forward and current step is not done, and not DataPrep, block
        if delta > 0 and not self._steps_done[self._cur] and self._cur is not Step.DATAPREP:
            return

        # Identify the next step
        nxt = self._seq[pos]
        logger.debug(f"Switching to step: {nxt}")

        # ----------------------------------------------------------------------
        # Special handling if current step is DataPrep and user clicked Next
        # ----------------------------------------------------------------------
        if self._cur is Step.DATAPREP and delta > 0:
            # Ask DataPrep window to validate first row before proceeding
            choice = self.pg_prep.validate_first_row()
            if choice == "stay":
                # User chose to remain and fix manually: abort shifting
                return
            elif choice == "autofill":
                # User chose to autofill but stay: mark DataPrep as not done and abort shifting
                self._steps_done[Step.DATAPREP] = False
                return
            else:
                # User chose to ignore invalid cells: emit data from DataPrep and continue
                self.pg_prep.emit_data()

        # ----------------------------------------------------------------------
        # Handle data passing between steps for those that require data input
        # ----------------------------------------------------------------------
        elif self._cur is Step.MAPPING and nxt is Step.MANUAL:
            # Pass mapping results (matched/unmatched/available) to manual mapping step
            self.pg_manual.load_data(self.pg_mapping.matched_df, self.pg_mapping.unmatched_df, self.pg_mapping.available_df)
        elif self._cur is Step.MANUAL and nxt is Step.PREVIEW:
            # Prepare preview with mapped DataFrame from DataStore
            df = DataStore.df_mapped if DataStore.df_mapped is not None else pd.DataFrame()
            self.pg_preview.load_data(df)
            # Mark preview as done because data is already available
            self._steps_done[Step.PREVIEW] = True
        elif self._cur is Step.PREVIEW and nxt is Step.EXPORT:
            # Prepare export with mapped DataFrame from DataStore
            df = DataStore.df_mapped if DataStore.df_mapped is not None else pd.DataFrame()
            self.pg_export.load_data(df)

        # Finally, show the target step in the stacked widget
        self._show(nxt)

    # ==========================================================================
    # Sidebar and Button State Updater
    # ==========================================================================
    def _rebuild_list(self) -> None:
        """
        Rebuilds the left-side progress list based on the current sequence of steps.
        """
        self.lst_steps.clear()
        for _ in self._seq:
            # Create a placeholder item for each step in the sequence
            self.lst_steps.addItem(QListWidgetItem())

    def _update_chrome(self) -> None:
        """
        Updates the state of back/next buttons, the step indicators in the sidebar, and the description text.
        """
        # Determine index of current step in the sequence
        idx = self._seq.index(self._cur)
        # Identify the currently visible page widget
        page = self._stack.currentWidget()

        # Determine if Back/Next should be enabled by calling can_go_back / can_go_next on the page
        can_back = getattr(page, "can_go_back", lambda: idx > 0)()
        can_next = getattr(page, "can_go_next", lambda: True)()

        # Enable or disable buttons accordingly
        self.btn_back.setEnabled(can_back)
        self.btn_next.setEnabled(can_next)

        # Update each item in the progress list with a prefix indicating state
        for i, st in enumerate(self._seq):
            if st is self._cur:
                prefix = "► "
            elif self._steps_done[st]:
                prefix = "✓ "
            else:
                prefix = "○ "
            self.lst_steps.item(i).setText(prefix + TITLE[st])

        # Set description text based on current step's HTML snippet
        if self._cur in STEP_DESCRIPTIONS:
            (description_html, _info_html) = STEP_DESCRIPTIONS[self._cur]
            self.txt_description.setHtml(description_html)
        else:
            self.txt_description.setHtml("<p><i>No description available.</i></p>")

    # ==========================================================================
    # Info Button Handler
    # ==========================================================================
    def _on_info_clicked(self) -> None:
        """
        Shows a message box containing the HTML info text for the current step.
        """
        if self._cur in STEP_DESCRIPTIONS:
            (_, info_html) = STEP_DESCRIPTIONS[self._cur]
            # Create a QMessageBox that supports rich text
            msg = QMessageBox(self)
            msg.setWindowTitle("Info")
            msg.setTextFormat(Qt.RichText)  # type: ignore[attr-defined]
            msg.setText(info_html)
            msg.setStandardButtons(QMessageBox.Ok)  # type: ignore[attr-defined]
            msg.exec()
        else:
            # If no info is available, show a simple information dialog
            QMessageBox.information(self, "Info", "<p>No additional information available.</p>")

    # ==========================================================================
    # Callbacks from Child Pages
    # ==========================================================================
    def _on_uploaded(self, path: str) -> None:
        """
        Handles the uploadFinished signal from FileLoadView.
        Sets data in DataStore and determines sequence of steps based on file type.
        """
        # Store the uploaded file path in DataStore
        DataStore.set_upload(path)
        ext = path.lower()

        # Decide next steps based on file extension
        if ext.endswith(".csv"):
            self.pg_prep.load_csv(path)
            seq = [Step.UPLOAD, Step.DATAPREP, Step.FILTER, Step.GEODATA, Step.MAPPING, Step.MANUAL, Step.PREVIEW, Step.EXPORT]
        elif ext.endswith(".pdf"):
            self.pg_pdf.load_pdf(path)
            seq = [Step.UPLOAD, Step.PDF, Step.DATAPREP, Step.FILTER, Step.GEODATA, Step.MAPPING, Step.MANUAL, Step.PREVIEW, Step.EXPORT]
        else:
            # Assume Excel for all other extensions
            self.pg_sheet.load_excel(path)
            seq = [Step.UPLOAD, Step.WORKSHEET, Step.DATAPREP, Step.FILTER, Step.GEODATA, Step.MAPPING, Step.MANUAL, Step.PREVIEW, Step.EXPORT]

        # Update the sequence of steps and mark UPLOAD as done
        self._seq = seq
        self._rebuild_list()
        self._steps_done[Step.UPLOAD] = True
        self._update_chrome()

    def _on_pdf_ready(self, cfg: dict) -> None:
        """
        Handles the extractionReady signal from PdfAreaView.
        Loads the extracted DataFrame into DataPrep and marks PDF step as done.
        """
        self.pg_prep.load_dataframe(cfg["df"])
        self._steps_done[Step.PDF] = True
        self._update_chrome()

    def _on_sheet_ready(self, cfg: dict) -> None:
        """
        Handles the selectionReady signal from SheetSelectView.
        Loads the selected sheet DataFrame into DataPrep and marks WORKSHEET as done.
        """
        self.pg_prep.load_dataframe(cfg["df"])
        self._steps_done[Step.WORKSHEET] = True
        self._update_chrome()

    def _on_prep_ready(self, df: pd.DataFrame) -> None:
        """
        Handles the prepReady signal from CleanDataView.
        Loads the prepared DataFrame into the ColumnFilterView and marks DATAPREP as done.
        """
        logger.debug(f"_on_prep_ready called with DataFrame shape: {df.shape}")
        self.pg_filter.load_dataframe(df)
        self._steps_done[Step.DATAPREP] = True
        self._update_chrome()

    def _on_filter_ready(self, cfg: dict) -> None:
        """
        Handles the filterReady signal from ColumnFilterView.
        Validates that at least one column was selected, updates DataStore, and marks FILTER as done.
        """
        df_raw = cfg["df_filtered"]
        selected_columns = cfg.get("selected_columns", [])

        # If no columns are selected, show a warning and abort
        if not selected_columns:
            QMessageBox.warning(self, "No columns", "Please select at least one column.")
            return

        # Build new DataFrame with the chosen column names
        df = df_raw.copy()
        df.columns = selected_columns

        # Store the filtered DataFrame and selected columns in DataStore
        DataStore.set_selection(df, selected_columns)
        self._steps_done[Step.FILTER] = True
        self._update_chrome()

    def _on_geo_ready(self, cfg: dict) -> None:
        """
        Handles the filterReady signal from GeoFilterView.
        Stores geodata in DataStore and initializes AutoMapView with user and geo DataFrames.
        """
        DataStore.set_geo(cfg["df_filtered"], cfg["meta"])
        self.pg_mapping.load_data(DataStore.df_user, DataStore.df_geo)  # type: ignore[arg-type]
        self._steps_done[Step.GEODATA] = True
        self._update_chrome()

    def _on_mapping_done(self, res: pd.DataFrame) -> None:
        """
        Handles the mappingDone signal from AutoMapView.
        Stores the mapping results in DataStore and marks MAPPING as done.
        """
        DataStore.set_mapping(res)
        self._steps_done[Step.MAPPING] = True
        self._update_chrome()

    def _on_manual_ready(self, df: pd.DataFrame) -> None:
        """
        Handles the manualMappingDone signal from ManualMapView.
        Stores the final mapped DataFrame in DataStore and marks MANUAL as done.
        """
        DataStore.set_mapping(df)
        self._steps_done[Step.MANUAL] = True
        self._update_chrome()

    # ==========================================================================
    # Static Main Entry Point
    # ==========================================================================
    @staticmethod
    def main() -> None:
        """
        Creates the QApplication, configures the application, instantiates MainWindow, and starts the event loop.
        """
        app = QApplication(sys.argv)
        # Configure application metadata so desktop environments display the
        # proper name instead of the python executable when hovering over the
        # dock/taskbar icon.
        app.setApplicationName("GeoImporter")
        app.setApplicationDisplayName("GeoImporter")
        app.setOrganizationName("Friedrich Völkers")
        app.setApplicationVersion("0.0.1b914")
        app.setWindowIcon(QIcon(str(ICON_PATH)))
        # Show the main window
        MainWindow().show()
        # Enter the Qt main loop
        sys.exit(app.exec())


if __name__ == "__main__":
    MainWindow.main()
