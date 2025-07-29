# ==============================================================================
#  Worker Thread for Upload
# ==============================================================================
import os

from PySide6.QtCore import QThread, Signal


class UploadWorker(QThread):
    """
    Worker thread for file upload with progress tracking.

    This thread reads the file in chunks, updates progress,
    and signals when finished or on error.
    """

    # Signal emitting the current upload progress as an integer percentage
    progress = Signal(int)
    # Signal emitted when upload finishes successfully, passing the file path
    finished = Signal(str)
    # Signal emitted if an error occurs, passing the error message
    error = Signal(str)

    def __init__(self, file_path: str):
        """
        Initializes the upload worker with the given file path.

        Stores the file path and sets up the QThread.
        """
        super().__init__()
        # Store the path of the file to be uploaded
        self.file_path = file_path

    def run(self):
        """
        Runs in a separate thread to perform the upload simulation.

        Reads the file in 1MB chunks, updates progress percentage,
        and emits finished or error signals accordingly.
        """
        try:
            # Determine total size of the file for progress calculation
            file_size = os.path.getsize(self.file_path)
            # Define chunk size of 1 MB
            chunk_size = 1024 * 1024
            bytes_read = 0

            # Open the file in binary read mode
            with open(self.file_path, 'rb') as f:
                while True:
                    # Read a chunk of data
                    chunk = f.read(chunk_size)
                    if not chunk:
                        # End of file reached, break out of loop
                        break
                    # Update total bytes read so far
                    bytes_read += len(chunk)
                    # Calculate progress as integer percentage
                    progress = int((bytes_read / file_size) * 100)
                    # Emit progress signal to update UI
                    self.progress.emit(progress)

            # Once fully read, emit finished signal with file path
            self.finished.emit(self.file_path)
        except Exception as e:
            # On any exception, emit error signal with message
            self.error.emit(str(e))
