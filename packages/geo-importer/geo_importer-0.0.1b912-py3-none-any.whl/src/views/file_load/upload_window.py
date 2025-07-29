"""
File-picker with real upload progress tracking.

The selected file is processed locally and the progress bar shows the actual
upload progress.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from src.views.file_load.ui.upload_ui import Ui_UploadWindow
from src.views.file_load.upload_worker import UploadWorker


# ==============================================================================
#  Main Upload Window
# ==============================================================================
class FileLoadView(QMainWindow, Ui_UploadWindow):
    """
    File upload widget with real progress tracking.

    Emits a signal with the file path when upload completes successfully.
    """

    # Signal emitted when upload finishes, carrying the file path
    uploadFinished = Signal(str)

    def __init__(self) -> None:
        """
        Sets up the upload window and connects UI elements to handlers.

        Prepares the browse button and initializes worker and file references.
        """
        super().__init__()
        # Set up UI components from the .ui file
        self.setupUi(self)
        # Connect the Browse button to the file dialog handler
        self.buttonBrowse.clicked.connect(self._browse)
        # Placeholder for the UploadWorker thread (will be created on browse)
        self._worker: Optional[UploadWorker] = None
        # Store selected file path
        self._file: Optional[str] = None

    # ==========================================================================
    #  File Browsing and Starting Upload
    # ==========================================================================
    def _browse(self) -> None:
        """
        Opens a file dialog to allow the user to pick a file.

        The filter is determined by which radio button is selected.
        """
        # Determine the file filter based on radio button selection
        if self.radioExcel.isChecked():
            file_name_filter = "Excel files (*.xlsx *.xls)"
        elif self.radioCSV.isChecked():
            file_name_filter = "CSV files (*.csv)"
        elif self.radioPDF.isChecked():
            file_name_filter = "PDF files (*.pdf)"
        else:
            # Fallback to all files if no specific radio is checked
            file_name_filter = "All files (*)"

        # Open the QFileDialog and retrieve the selected path
        path, _ = QFileDialog.getOpenFileName(self, "Pick file", "", file_name_filter)
        if path:
            # If a path was chosen, start the upload process
            self._start_upload(path)

    def _start_upload(self, path: str) -> None:
        """
        Starts the upload process by creating and running the worker thread.

        Disables the browse button, resets the progress bar, and connects worker signals.
        """
        # Store the chosen file path
        self._file = path
        # Display the path in the line edit
        self.lineEditFilePath.setText(path)
        # Reset progress bar to 0
        self.progressBar.setValue(0)
        # Disable the Browse button to prevent multiple uploads
        self.buttonBrowse.setEnabled(False)

        # Create the worker thread with the selected file path
        self._worker = UploadWorker(path)
        # Connect worker's progress signal to update the UI progress bar
        self._worker.progress.connect(self._update_progress)
        # Connect worker's finished signal to handle successful completion
        self._worker.finished.connect(self._upload_finished)
        # Connect worker's error signal to handle failures
        self._worker.error.connect(self._upload_error)
        # Start the worker thread (which invokes run() in a separate thread)
        self._worker.start()

    # ==========================================================================
    #  Progress and Completion Handlers
    # ==========================================================================
    def _update_progress(self, value: int) -> None:
        """
        Updates the progress bar to reflect the current upload percentage.

        Receives integer percentage from the worker.
        """
        # Set the progress bar's value to the emitted percentage
        self.progressBar.setValue(value)

    def _upload_finished(self, path: str) -> None:
        """
        Handles successful upload completion.

        Updates UI to reflect 100% completion and re-enables the browse button.
        Emits uploadFinished signal with the file path.
        """
        # Ensure progress bar shows complete
        self.progressBar.setValue(100)
        # Re-enable the Browse button so user can upload another file
        self.buttonBrowse.setEnabled(True)
        # Emit the finished signal to notify parent that upload is done
        self.uploadFinished.emit(path)

    def _upload_error(self, error_msg: str) -> None:
        """
        Handles errors that occur during upload.

        Resets the UI and shows a critical message box with the error.
        """
        # Re-enable the Browse button so user can retry
        self.buttonBrowse.setEnabled(True)
        # Reset progress bar to 0 to indicate failure
        self.progressBar.setValue(0)
        # Show an error message box with the error details
        QMessageBox.critical(self, "Upload Error", f"Failed to upload file: {error_msg}")

    # ==========================================================================
    #  Navigation Guards
    # ==========================================================================
    def can_go_next(self) -> bool:
        """
        Prevents navigation to the next view until upload is fully complete.

        Returns True only when progress bar reaches 100%.
        """
        return self.progressBar.value() == 100

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Prevents navigation backward from this first page.

        The Upload window is the first page, so going back is not allowed.
        """
        return False
