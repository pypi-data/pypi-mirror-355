from __future__ import annotations

"""Utility functions for manipulating the QTableWidget used in DataPrep."""

from typing import List

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

# ======================================================================
#  Basic Table Utilities
# ======================================================================


def fill_table(widget: QTableWidget, data: List[List[str]]) -> None:
    """
    Replace the entire table with the provided 2D list.

    Steps:
      1. Clear any existing contents from widget.
      2. Resize the table to match data.
      3. Insert each cell value into the table widget.
      4. Resize columns so values are fully visible.
    """
    # Determine dimensions of new table
    rows = len(data)
    cols = len(data[0]) if rows else 0

    # Clear existing contents and set new size
    widget.clear()
    widget.setRowCount(rows)
    widget.setColumnCount(cols)
    widget.setHorizontalHeaderLabels([str(i) for i in range(cols)])

    # Populate each cell with the provided value
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            widget.setItem(r, c, QTableWidgetItem(val))

    # Adjust column widths to fit content
    widget.resizeColumnsToContents()


def get_table_data(widget: QTableWidget) -> List[List[str]]:
    """
    Return the table contents as a list of rows.

    Steps:
      1. Iterate over every row and column of widget.
      2. Collect the text of each cell (empty string if no item).
      3. Assemble and return the resulting two-dimensional list.
    """
    data: List[List[str]] = []
    rows = widget.rowCount()
    cols = widget.columnCount()

    # Extract text from each cell
    for r in range(rows):
        row_vals: List[str] = []
        for c in range(cols):
            item = widget.item(r, c)
            row_vals.append(item.text() if item else "")
        data.append(row_vals)

    return data


def update_table_data(widget: QTableWidget, data: List[List[str]]) -> None:
    """
    Update the table in place to match the given data.

    Steps:
      1. Iterate through data row by row.
      2. Create missing QTableWidgetItem objects as needed.
      3. Update text of existing items only when it differs to avoid flicker.
      4. Call 'autosize_columns' afterward to adjust column widths.
    """
    # Synchronize each cell with the new data
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            itm = widget.item(r, c)
            if itm is None:
                itm = QTableWidgetItem()
                widget.setItem(r, c, itm)
            if itm.text() != val:
                itm.setText(val)

    # Adjust columns after updates
    autosize_columns(widget)


def autosize_columns(widget: QTableWidget) -> None:
    """Resize all columns so that cell contents become visible."""
    widget.resizeColumnsToContents()


def transpose_data(data: List[List[str]]) -> List[List[str]]:
    """
    Return a transposed copy of the provided data.

    Steps:
      1. Use zip(*data) to swap rows and columns.
      2. Convert the tuples back into lists.
    """
    # Return empty list if no data
    if not data:
        return []

    # Transpose via unpacking and re-listing
    return [list(col) for col in zip(*data)]


def insert_row(widget: QTableWidget) -> None:
    """
    Insert an empty row at the current position.

    Steps:
      1. Determine the current row index; append to bottom if no selection.
      2. Insert a new empty row and resize columns.
    """
    # Choose insertion index
    r = widget.currentRow()
    widget.insertRow(r if r >= 0 else widget.rowCount())

    # Ensure columns fit after insertion
    autosize_columns(widget)


def insert_col(widget: QTableWidget) -> None:
    """
    Insert an empty column at the current position.

    Steps:
      1. Determine the current column index; append to end if none selected.
      2. Insert a new empty column and resize columns.
    """
    # Choose insertion index
    c = widget.currentColumn()
    widget.insertColumn(c if c >= 0 else widget.columnCount())

    # Ensure columns fit after insertion
    autosize_columns(widget)


def delete_rows(widget: QTableWidget, rows: set[int]) -> None:
    """
    Remove all rows listed in rows.

    Steps:
      1. Iterate over rows in reverse order so indices remain valid.
      2. Remove each row from the widget.
      3. Resize columns afterward for cleanliness.
    """
    # Remove each specified row
    for r in sorted(rows, reverse=True):
        widget.removeRow(r)

    # Adjust columns after deletion
    autosize_columns(widget)


def delete_cols(widget: QTableWidget, cols: set[int]) -> None:
    """
    Remove all columns listed in cols.

    Steps:
      1. Iterate over cols in reverse order so indices remain valid.
      2. Remove each column from the widget.
      3. Resize columns afterward for cleanliness.
    """
    # Remove each specified column
    for c in sorted(cols, reverse=True):
        widget.removeColumn(c)

    # Adjust columns after deletion
    autosize_columns(widget)


def transpose_table(widget: QTableWidget) -> None:
    """
    Transpose the table if it contains any data.

    Steps:
      1. Extract current data with get_table_data.
      2. If the table is not empty, fill it again with the transposed data.
    """
    # Read current table contents
    data = get_table_data(widget)
    if not data:
        return

    # Refill with transposed data
    fill_table(widget, transpose_data(data))
