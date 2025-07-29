import logging

import pytest

from src.views.clean_data.dataprep_logic import DataPrepLogic


@pytest.fixture
def sample_table():
    """
    Provide a 3×4 table of distinct string values for testing operations.
    Each cell is labeled as 'R<row>C<col>'.
    """
    return [[f"R{r}C{c}" for c in range(4)] for r in range(3)]


@pytest.fixture(autouse=True)
def enable_debug_logging(caplog):
    """
    Enable debug logging for the DataPrepLogic module during tests.
    """
    caplog.set_level(logging.DEBUG, logger="src.views.dataprep.dataprep_logic")
    return caplog


def test_prepare_copy_clears_pattern_when_no_selection():
    """
    Verify that prepare_copy_data clears the internal pattern when no cells are selected.
    """
    # Arrange: initialize logic and populate copy pattern
    logic = DataPrepLogic()
    logic.prepare_copy_data([(0, 0)], [["X"]])
    assert logic._copy_pattern, "Pattern should be populated after copying a cell"

    # Act: call prepare_copy_data with empty selection
    logic.prepare_copy_data([], [["X"]])

    # Assert: the copy pattern list is cleared
    assert logic._copy_pattern == [], "Pattern must be empty when no cells are selected"


def test_single_cell_copy_and_paste(sample_table):
    """
    Test copying a single cell and pasting it to a new location.

    This ensures that only the target cell is overwritten and others remain intact.
    """
    logic = DataPrepLogic()

    # Copy cell at (1, 2)
    selection = [(1, 2)]
    logic.prepare_copy_data(selection, sample_table)

    # Paste to anchor (0, 0)
    result = logic.get_paste_data(0, 0, sample_table)

    # Verify original table remains unchanged
    assert sample_table[0][0] == "R0C0", "Original data should not be modified"

    # Check that the pasted cell has the correct value
    assert result[0][0] == "R1C2", "Pasted cell must match the copied value"

    # Ensure all other cells are unchanged
    for r in range(len(sample_table)):
        for c in range(len(sample_table[0])):
            if (r, c) != (0, 0):
                assert result[r][c] == sample_table[r][c], f"Cell at ({r}, {c}) should remain '{sample_table[r][c]}', got '{result[r][c]}'"


def test_multi_cell_copy_and_paste_with_offset(sample_table):
    """
    Test copying a 2×2 block of cells and pasting it with an offset anchor.

    This checks that relative positions are preserved in the paste.
    """
    logic = DataPrepLogic()

    # Select a 2×2 block: positions (0,1),(0,2),(1,1),(1,2)
    block = [(0, 1), (0, 2), (1, 1), (1, 2)]
    logic.prepare_copy_data(block, sample_table)

    # Paste block so its top-left maps to (1, 0)
    pasted = logic.get_paste_data(1, 0, sample_table)

    # Define expected mappings after paste
    expected = {(1, 0): "R0C1", (1, 1): "R0C2", (2, 0): "R1C1", (2, 1): "R1C2"}

    # Assert each pasted position has correct value
    for coord, value in expected.items():
        r, c = coord
        assert pasted[r][c] == value, f"Expected '{value}' at {coord}, got '{pasted[r][c]}'"

    # Confirm non-target cells are unchanged
    for r in range(len(sample_table)):
        for c in range(len(sample_table[0])):
            if coord not in expected:
                assert pasted[r][c] == sample_table[r][c]


def test_get_paste_data_with_no_pattern_returns_original(sample_table):
    """
    Ensure get_paste_data returns the original table when no copy pattern is stored.
    """
    logic = DataPrepLogic()

    # Without a prior copy, the pattern buffer is empty
    output = logic.get_paste_data(2, 3, sample_table)

    # Expect the same data structure and content
    assert output == sample_table, "Data must be unchanged when no pattern exists"


def test_pattern_matches_for_same_shape_and_size(sample_table):
    """
    Verify that pattern_matches returns True when selection shape matches the stored pattern.
    """
    logic = DataPrepLogic()

    # Copy a 2×2 block at top-left corner
    source = [(0, 0), (0, 1), (1, 0), (1, 1)]
    logic.prepare_copy_data(source, sample_table)

    # Define a destination block shifted by (1,1)
    destination = {(1, 1), (1, 2), (2, 1), (2, 2)}

    # pattern_matches should confirm identical relative layout
    assert logic.pattern_matches(destination), "Expected pattern to match identical block shape"


def test_pattern_matches_rejects_different_shape(sample_table):
    """
    Ensure that pattern_matches returns False for partial or mismatched selections.
    """
    logic = DataPrepLogic()

    # Case 1: Partial overlap of pattern
    source = [(0, 0), (0, 2)]
    logic.prepare_copy_data(source, sample_table)
    partial_dest = {(1, 1)}
    assert not logic.pattern_matches(partial_dest), "Partial selections must not match the stored pattern"

    # Case 2: Different relative positions
    source2 = [(0, 0), (1, 1)]
    logic.prepare_copy_data(source2, sample_table)
    # Create a destination set that swaps offsets
    swapped = {(2, 1), (3, 2)}
    # Filter out-of-bounds coordinates
    valid_swapped = {(r, c) for r, c in swapped if r < 3 and c < 4}
    assert not logic.pattern_matches(valid_swapped), "Mismatched relative offsets must not match"
