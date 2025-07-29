import pytest
from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTableWidgetItem

from src.views.clean_data.table_logic import fill_table, get_table_data
from src.views.clean_data.undo_redo_logic import UndoRedoLogic


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """
    Ensure a QApplication instance exists for the UndoRedoLogic tests.
    """
    return QApplication.instance() or QApplication([])


@pytest.fixture
def table_and_data():
    """
    Provide a 2×3 QTableWidget pre-filled with known string values.
    Returns the widget and its initial data as a list of lists.
    """
    # Create a table with 2 rows and 3 columns
    tbl = QTableWidget(2, 3)
    data = [["A1", "B1", "C1"], ["A2", "B2", "C2"]]
    # Fill the table widget with the sample data
    fill_table(tbl, data)
    return tbl, data


@pytest.fixture
def buttons():
    """
    Provide fresh Undo and Redo QPushButton instances for each test.
    """
    return QPushButton(), QPushButton()


@pytest.fixture
def undo_logic(table_and_data, buttons):
    """
    Initialize UndoRedoLogic with a fresh table and buttons, and record the initial state.
    """
    tbl, _ = table_and_data
    btn_undo, btn_redo = buttons
    logic = UndoRedoLogic(tbl, btn_undo, btn_redo)
    # Capture the initial table snapshot
    logic.init_state()
    return logic


def test_clear_resets_history_and_buttons(undo_logic):
    """
    Test that clear() empties both history stacks and disables action buttons.
    """
    # Act: clear undo/redo history
    undo_logic.clear()

    # Assert: stacks are empty and buttons are disabled
    assert undo_logic._undo_stack == [], "Undo stack must be empty after clear()"
    assert undo_logic._redo_stack == [], "Redo stack must be empty after clear()"
    assert not undo_logic.btnUndo.isEnabled(), "Undo button must be disabled after clear()"
    assert not undo_logic.btnRedo.isEnabled(), "Redo button must be disabled after clear()"


def test_push_snapshot_records_state_and_updates_buttons(undo_logic, table_and_data):
    """
    Test that push_snapshot() saves the current table state to undo stack and updates buttons.
    """
    tbl, original = table_and_data

    # Act: take a snapshot of the original state
    undo_logic.push_snapshot()

    # Assert: undo stack has one entry equal to original data
    assert len(undo_logic._undo_stack) == 1, "Undo stack must have one snapshot"
    assert undo_logic._undo_stack[0] == original, "Snapshot must match original table data"
    assert undo_logic.btnUndo.isEnabled(), "Undo button must be enabled after snapshot"
    assert not undo_logic.btnRedo.isEnabled(), "Redo button must remain disabled after snapshot"


def test_undo_reverts_to_previous_snapshot(undo_logic, table_and_data):
    """
    Test that undo() restores the table to the initial snapshot and toggles button states.
    """
    # Arrange: record the original state before modification
    tbl, original = table_and_data
    undo_logic.push_snapshot()

    # Modify the table to new values
    modified = [["X1", "Y1", "Z1"], ["A2", "B2", "C2"]]
    fill_table(tbl, modified)

    # Act: perform undo to revert to the original snapshot
    undo_logic.undo()

    # Assert: table data matches the original snapshot
    assert get_table_data(tbl) == original, "Table must revert to the original data after undo"
    # After undo, redo should be available and undo may be disabled
    assert undo_logic.btnRedo.isEnabled(), "Redo button must be enabled after undo"
    assert not undo_logic._undo_stack, "Undo stack should be empty after consuming the only snapshot"


def test_redo_reapplies_undone_snapshot(undo_logic, table_and_data):
    """
    Test that redo() reapplies the most recently undone table state.
    """
    tbl, original = table_and_data

    # Arrange: create and snapshot a modified state
    modified = [["M1", "M2", "M3"], ["A2", "B2", "C2"]]
    fill_table(tbl, modified)
    undo_logic.push_snapshot()
    # Undo back to original
    undo_logic.undo()

    # Act: redo the change to restore modified state
    undo_logic.redo()

    # Assert: table data matches modified state
    assert get_table_data(tbl) == modified, "Table must match modified data after redo"
    assert undo_logic.btnUndo.isEnabled(), "Undo button must be enabled after redo"
    assert not undo_logic.btnRedo.isEnabled(), "Redo button must be disabled if no further redo steps"


def test_max_undo_steps_enforced(undo_logic, table_and_data):
    """
    Test that the undo stack never grows beyond MAX_UNDO_STEPS entries.
    """
    tbl, _ = table_and_data

    # Act: push snapshots more times than the maximum allowed
    for i in range(UndoRedoLogic.MAX_UNDO_STEPS + 3):
        fill_table(tbl, [[str(i)] * 3] * 2)
        undo_logic.push_snapshot()

    # Assert: undo stack size does not exceed MAX_UNDO_STEPS
    assert len(undo_logic._undo_stack) <= UndoRedoLogic.MAX_UNDO_STEPS, f"Undo stack must be capped at {UndoRedoLogic.MAX_UNDO_STEPS} entries"


def test_item_changed_records_manual_edit(undo_logic, table_and_data):
    """
    Test that item_changed() pushes the previous state to undo stack and resets redo.
    """
    tbl, original = table_and_data

    # Arrange: modify a cell to simulate a user edit
    tbl.setItem(0, 0, QTableWidgetItem("Edited"))

    # Act: signal that an item changed
    undo_logic.item_changed()

    # Assert: undo stack contains the state before edit
    assert undo_logic._undo_stack[-1] == original, "Undo stack must record the previous state"
    # Last table data should reflect the edit
    assert undo_logic._last_table_data[0][0] == "Edited", "Last recorded data must match edited content"
    # Redo history must be cleared after manual change
    assert undo_logic._redo_stack == [], "Redo stack must be empty after manual edit"
    assert undo_logic.btnUndo.isEnabled(), "Undo button must be enabled after manual edit"
