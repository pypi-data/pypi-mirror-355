from __future__ import annotations

"""Undo/Redo management for DataPrep tables."""

# ======================================================================
#  Imports and Logger Setup
# ======================================================================

import copy
import logging
from typing import List

from PySide6.QtWidgets import QPushButton, QTableWidget

from .table_logic import fill_table, get_table_data

logger = logging.getLogger(__name__)


class UndoRedoLogic:
    """Track changes of a table widget to allow undo and redo."""

    MAX_UNDO_STEPS = 5  # Maximum history depth for undo/redo

    def __init__(self, table: QTableWidget, btn_undo: QPushButton, btn_redo: QPushButton) -> None:
        """
        Initialize stacks and connect to UI buttons.

        Steps:
          1. Store references to the table widget and the two control buttons.
          2. Create empty undo/redo stacks and remember the current table state.
          3. Enable change tracking by default.
        """
        # Store widget and control buttons
        self.table = table
        self.btnUndo = btn_undo
        self.btnRedo = btn_redo

        # Initialize history stacks and last-known state
        self._undo_stack: List[List[List[str]]] = []
        self._redo_stack: List[List[List[str]]] = []
        self._last_table_data: List[List[str]] = []

        # Enable snapshot tracking
        self.tracking_enabled = True

    def init_state(self) -> None:
        """
        Remember the current table as the initial state.

        Step 1: Capture the table content via get_table_data and store it
               for later comparisons.
        """
        # Capture initial table snapshot
        self._last_table_data = get_table_data(self.table)

    def clear(self) -> None:
        """
        Reset all history and disable the buttons.

        Steps:
          1. Empty both undo and redo stacks.
          2. Disable the Undo and Redo buttons.
        """
        # Clear history
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Disable controls
        self.btnUndo.setEnabled(False)
        self.btnRedo.setEnabled(False)

    # ------------------------------------------------------------------
    #  Snapshots
    # ------------------------------------------------------------------
    def push_snapshot(self) -> None:
        """
        Store the current table in the undo stack.

        Steps:
          1. If tracking is disabled, do nothing.
          2. Append a deep copy of the current table to _undo_stack.
          3. Trim the stack to MAX_UNDO_STEPS entries.
          4. Clear the redo stack and update button states.
        """
        if not self.tracking_enabled:
            logger.debug("Tracking disabled – no snapshot.")
            return

        # Take snapshot of current table
        current = get_table_data(self.table)
        self._undo_stack.append(copy.deepcopy(current))

        # Enforce maximum history length
        if len(self._undo_stack) > self.MAX_UNDO_STEPS:
            self._undo_stack.pop(0)

        # Reset redo history and enable undo button
        self._redo_stack.clear()
        self.btnUndo.setEnabled(True)
        self.btnRedo.setEnabled(False)

    def _apply_state(self, state: List[List[str]]) -> None:
        """
        Replace the table contents with state without recording it.

        Steps:
          1. Temporarily disable tracking so no snapshot is taken.
          2. Fill the table with state and remember it as _last_table_data.
          3. Re-enable tracking.
        """
        # Suspend tracking to avoid recursive snapshots
        self.tracking_enabled = False

        # Apply the given table state
        fill_table(self.table, state)
        self._last_table_data = copy.deepcopy(state)

        # Restore tracking
        self.tracking_enabled = True

    # ------------------------------------------------------------------
    #  Public API: Undo / Redo / Change Notification
    # ------------------------------------------------------------------
    def undo(self) -> None:
        """
        Restore the previous snapshot if available.

        Steps:
          1. If the undo stack is empty, disable the button and return.
          2. Push the current table onto the redo stack.
          3. Pop the last snapshot from the undo stack and apply it.
          4. Update button enablement based on remaining history.
        """
        if not self._undo_stack:
            # Nothing to undo
            self.btnUndo.setEnabled(False)
            return

        # Save current state for redo
        current = get_table_data(self.table)
        self._redo_stack.append(copy.deepcopy(current))
        if len(self._redo_stack) > self.MAX_UNDO_STEPS:
            self._redo_stack.pop(0)

        # Restore last undo snapshot
        prev = self._undo_stack.pop()
        self._apply_state(prev)

        # Enable redo, disable undo if no more history
        self.btnRedo.setEnabled(True)
        if not self._undo_stack:
            self.btnUndo.setEnabled(False)

    def redo(self) -> None:
        """
        Reapply a snapshot that was previously undone.

        Steps:
          1. If the redo stack is empty, disable the button and return.
          2. Push the current table onto the undo stack.
          3. Pop the next snapshot from the redo stack and apply it.
          4. Update button enablement based on remaining history.
        """
        if not self._redo_stack:
            # Nothing to redo
            self.btnRedo.setEnabled(False)
            return

        # Save current state for undo
        current = get_table_data(self.table)
        self._undo_stack.append(copy.deepcopy(current))
        if len(self._undo_stack) > self.MAX_UNDO_STEPS:
            self._undo_stack.pop(0)

        # Restore next redo snapshot
        nxt = self._redo_stack.pop()
        self._apply_state(nxt)

        # Enable undo, disable redo if no more history
        self.btnUndo.setEnabled(True)
        if not self._redo_stack:
            self.btnRedo.setEnabled(False)

    def item_changed(self) -> None:
        """
        Record manual edits made by the user.

        Steps:
          1. If tracking is disabled, ignore the change.
          2. Push the last stored table onto the undo stack and clear redo.
          3. Store the new table state as _last_table_data and enable Undo.
        """
        if not self.tracking_enabled:
            return

        # Add previous state to undo history
        self._undo_stack.append(copy.deepcopy(self._last_table_data))

        # Clear redo history after new change
        self._redo_stack.clear()

        # Update last-known state to current
        self._last_table_data = copy.deepcopy(get_table_data(self.table))

        # Enable undo button
        self.btnUndo.setEnabled(True)
        self.btnRedo.setEnabled(False)
