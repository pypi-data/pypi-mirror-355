from __future__ import annotations

"""Helper functions used by the DataPrep window."""

# ======================================================================
#  Imports and Logger
# ======================================================================

import logging
from typing import List

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QWidget

logger = logging.getLogger(__name__)


# ======================================================================
#  CSV Export
# ======================================================================


def export_csv(data: List[List[str]], parent: QWidget) -> None:
    """
    Save the current table as a CSV file.

    Steps:
      1. Warn and abort if ``data`` is empty.
      2. Ask the user for a target file path via ``QFileDialog``.
      3. Write ``data`` using :func:`pandas.DataFrame.to_csv`.
      4. Inform the user of success or show a critical message on failure.
    """

    # Warn and abort if data is empty.
    if not data:
        QMessageBox.warning(parent, "Export CSV", "The table is empty. Nothing to export.")
        return

    # Ask the user for a target CSV file path.
    file_path, _ = QFileDialog.getSaveFileName(parent, "Save as CSV", "", "CSV Files (*.csv);;All Files (*)")
    if not file_path:
        return

    try:
        # Create DataFrame and write CSV without index or header.
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, header=False, encoding="utf-8")

        # Inform the user of successful export.
        QMessageBox.information(parent, "Export CSV", f"Successfully exported to:\n{file_path}")
    except Exception as e:  # pragma: no cover - GUI feedback
        # Log the error and inform the user on failure.
        logger.error(f"Error while exporting CSV: {e}")
        QMessageBox.critical(parent, "Export CSV", f"Could not export file:\n{e}")


# ======================================================================
#  Excel Export
# ======================================================================


def export_excel(data: List[List[str]], parent: QWidget) -> None:
    """
    Save the current table as an Excel file.

    Steps:
      1. Warn and abort if ``data`` is empty.
      2. Ask the user for a target ``.xlsx`` path via ``QFileDialog``.
      3. Write ``data`` using :func:`pandas.DataFrame.to_excel`.
      4. Inform the user of success or show a critical message on failure.
    """

    # Warn and abort if data is empty.
    if not data:
        QMessageBox.warning(parent, "Export Excel", "The table is empty. Nothing to export.")
        return

    # Ask the user for a target Excel file path.
    file_path, _ = QFileDialog.getSaveFileName(parent, "Save as Excel", "", "Excel Files (*.xlsx);;All Files (*)")
    if not file_path:
        return

    try:
        # Create DataFrame from data.
        df = pd.DataFrame(data)

        # Ensure file name ends with .xlsx.
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        # Write DataFrame to Excel.
        df.to_excel(file_path, index=False, header=False, engine="openpyxl")

        # Inform the user of successful export.
        QMessageBox.information(parent, "Export Excel", f"Successfully exported to:\n{file_path}")

        # Log the export action.
        logger.info(f"Table exported as Excel to {file_path}")
    except Exception as e:  # pragma: no cover - GUI feedback
        # Log the error and inform the user on failure.
        logger.error(f"Error while exporting Excel: {e}")
        QMessageBox.critical(parent, "Export Excel", f"Could not export file:\n{e}")


# ======================================================================
#  First Row Validation
# ======================================================================


def validate_first_row(table: QTableWidget, parent: QWidget) -> str:
    """
    Check the first row for missing or invalid values.

    Steps:
      1. Gather all values of the first row and detect empty or ``NaN`` strings.
      2. If none found, return ``"ignore"``.
      3. Otherwise, show a dialog offering three choices:
         a. Proceed anyway.
         b. Stay and let the user fix manually.
         c. Autofill missing names with ``col_<index>``.
      4. Return a string describing the chosen action.
    """

    # Return "ignore" if there are no rows to validate.
    row_count = table.rowCount()
    if row_count == 0:
        logger.debug("No rows to validate.")
        return "ignore"

    # Collect values from the first row.
    first_row_values: List[str] = []
    for c in range(table.columnCount()):
        item = table.item(0, c)
        first_row_values.append(item.text() if item else "")

    # Identify indices of empty or NaN cells.
    bad_indices: List[int] = []
    for c, val in enumerate(first_row_values):
        v = val.strip()
        if v == "" or v.lower() == "nan":
            bad_indices.append(c)

    # Return "ignore" if no invalid cells found.
    if not bad_indices:
        logger.debug("First row validation passed.")
        return "ignore"

    # Warn about invalid cells and ask user for action.
    logger.warning(f"Found {len(bad_indices)} invalid cells in first row.")
    msg = QMessageBox(parent)
    msg.setWindowTitle("Missing or Invalid Column Names")
    msg.setText("Some cells in the first row are empty or contain NaN. What would you like to do?")

    # Provide action buttons: ignore, stay, autofill.
    btn_ignore = msg.addButton("Proceed anyway", QMessageBox.AcceptRole)  # type: ignore[arg-type]
    btn_stay = msg.addButton("Stay and fix manually", QMessageBox.RejectRole)  # type: ignore[arg-type]
    btn_autofill = msg.addButton("Auto-fill missing names", QMessageBox.DestructiveRole)  # type: ignore[arg-type]
    msg.setDefaultButton(btn_stay)
    msg.exec()

    # Handle user choice accordingly.
    clicked = msg.clickedButton()
    if clicked is btn_ignore:
        # User chose to proceed anyway.
        logger.info("User chose to proceed anyway.")
        return "ignore"
    elif clicked is btn_autofill:
        # Autofill invalid cells with placeholder names.
        logger.info(f"Auto-filling {len(bad_indices)} invalid cells.")
        for c in bad_indices:
            table.setItem(0, c, QTableWidgetItem(f"col_{c}"))
        table.resizeColumnsToContents()
        return "autofill"
    else:
        # User chose to stay and fix manually.
        return "stay"
