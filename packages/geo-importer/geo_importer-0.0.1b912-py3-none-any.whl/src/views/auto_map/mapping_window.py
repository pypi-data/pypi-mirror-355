"""
Automatic *Statistics ↔ Geo* mapping dialog (GUI only).

The heavy-lifting is done inside the individual Matcher classes
(`UniqueValueMatcher`, `PrefixMatcher`, etc.). This widget’s responsibilities:

1. Load both data sets and maintain three live views:
   – **matched**, **still-unmatched statistics**, **still-unmatched geo**.
2. Let the user compose an **ordered matcher pipeline** via a toolbox.
3. Run that pipeline and show progress.
4. Emit the resulting *matched* DataFrame to the caller.

A proxy model layer assures case-insensitive, multi-column filtering in each
table view so that large data sets remain navigable.
"""

from __future__ import annotations

from itertools import count
from typing import List

import pandas as pd
from PySide6.QtCore import QPoint, QSortFilterProxyModel, Qt, Signal
from PySide6.QtWidgets import QApplication, QHeaderView, QListWidgetItem, QMainWindow, QMenu

from src.core.data_store import DataStore
from src.mapper.matchers.fuzzy_matcher import FuzzyMatcher
from src.mapper.matchers.prefix_matcher import PrefixMatcher
from src.mapper.matchers.regex_matcher import RegexMatcher
from src.mapper.matchers.unique_value_matcher import UniqueValueMatcher
from src.models.dataframe_model import DataFrameModel
from src.views.auto_map.ui.mapping_ui import Ui_MappingWindow


# ==============================================================================
#  AutoMapView: Interactive matcher-pipeline builder
# ==============================================================================
class AutoMapView(QMainWindow, Ui_MappingWindow):
    """
    Provides a GUI where the user can build and run a pipeline of matching steps
    to join a statistics table with a Geo reference table.

    Responsibilities:
      1. Display five table views: all stats, all geo, remaining stats,
         remaining geo, and matched results.
      2. Allow the user to add, remove, and configure matcher widgets (Unique,
         Prefix, Fuzzy, Regex) in an ordered list.
      3. Execute the pipeline step by step, showing progress and updating views.
      4. Emit the final matched DataFrame via the mappingDone signal.
    """

    # Signal emitted after pipeline finishes; carries the matched DataFrame
    mappingDone = Signal(pd.DataFrame)

    # Internal counter to assign unique IDs to each matcher widget
    _ids = count(1)

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, parent=None) -> None:
        """
        Initializes the AutoMapView.

        - Sets up UI from Ui_MappingWindow.
        - Initializes empty DataFrames for stats, geo, matched, unmatched, available.
        - Creates underlying data models and proxy filters.
        - Wires Qt signals to corresponding slots.
        """
        super().__init__(parent)
        # Load the UI layout and widgets
        self.setupUi(self)

        # ---------------- Data Containers ----------------
        # Holds the full statistics DataFrame loaded from DataStore
        self._stats_df = pd.DataFrame()
        # Holds the full geo reference DataFrame loaded from DataStore
        self._geo_df = pd.DataFrame()
        # Will hold the matched rows after running the pipeline
        self.matched_df = pd.DataFrame()
        # Holds the stats rows not yet matched
        self.unmatched_df = pd.DataFrame()
        # Holds the geo rows not yet matched (with '_geodata' suffix)
        self.available_df = pd.DataFrame()

        # List of matcher widgets that the user has added, in order
        self._matchers: List[UniqueValueMatcher | PrefixMatcher | FuzzyMatcher | RegexMatcher] = []

        # ---------------- Build Model / Proxy Layer ----------------
        self._init_models()
        # ---------------- Wire Qt Signals ----------------
        self._wire()

    # ==============================================================================
    #  Model / Proxy Layer Initialization
    # ==============================================================================
    def _init_models(self) -> None:
        """
        Creates the raw DataFrameModel instances and wraps them in
        QSortFilterProxyModel for case-insensitive, multi-column filtering.

        Attaches the proxies to the five table views:
          - tableViewStatsAll, tableViewGeoAll,
          - tableViewStatsRest, tableViewGeoRest, tableViewMapped.

        Also configures the headers to resize to contents and enables sorting.
        """
        # Create raw models for each view
        self.mod_stats_all = DataFrameModel()
        self.mod_geo_all = DataFrameModel()
        self.mod_stats_rest = DataFrameModel()
        self.mod_geo_rest = DataFrameModel()
        self.mod_mapped = DataFrameModel()

        # Create proxy filters for each raw model
        self.prox_stats_all = QSortFilterProxyModel(self)
        self.prox_geo_all = QSortFilterProxyModel(self)
        self.prox_stats_rest = QSortFilterProxyModel(self)
        self.prox_geo_rest = QSortFilterProxyModel(self)
        self.prox_mapped = QSortFilterProxyModel(self)

        # Configure each proxy: attach source model, set case-insensitive filter,
        # and allow filtering on all columns (keyColumn = -1).
        for src, prox in (
            (self.mod_stats_all, self.prox_stats_all),
            (self.mod_geo_all, self.prox_geo_all),
            (self.mod_stats_rest, self.prox_stats_rest),
            (self.mod_geo_rest, self.prox_geo_rest),
            (self.mod_mapped, self.prox_mapped),
        ):
            prox.setSourceModel(src)
            # Use case-insensitive matching for filter strings
            prox.setFilterCaseSensitivity(Qt.CaseInsensitive)  # type: ignore[arg-type]
            # Allow searching across all columns
            prox.setFilterKeyColumn(-1)

        # Attach each proxy to its corresponding QTableView
        self.tableViewStatsAll.setModel(self.prox_stats_all)
        self.tableViewGeoAll.setModel(self.prox_geo_all)
        self.tableViewStatsRest.setModel(self.prox_stats_rest)
        self.tableViewGeoRest.setModel(self.prox_geo_rest)
        self.tableViewMapped.setModel(self.prox_mapped)

        # Visual tweaks: make headers resize to fit content and allow sorting
        for tv in (self.tableViewStatsAll, self.tableViewGeoAll, self.tableViewStatsRest, self.tableViewGeoRest, self.tableViewMapped):
            # Resize columns based on content width
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # type: ignore[attr-defined]
            # Enable interactive sorting by clicking headers
            tv.setSortingEnabled(True)

    # ==============================================================================
    #  Qt Signal Wiring
    # ==============================================================================
    def _wire(self) -> None:
        """
        Connects UI buttons and text edits to their handler methods.

        - Connects 'Add Matcher' button to show a menu of matcher types.
        - Connects 'Run Pipeline' button to execute the matching pipeline.
        - Connects each search edit (StatsAll, StatsRest, GeoAll, GeoRest, Mapped)
          to set the filter string on the corresponding proxy model.
        - Syncs the selected matcher in the QListWidget to display its settings
          in the stacked widget (stackMatcherSettings).
        """
        # When user clicks "Add Matcher", show the popup menu
        self.buttonAddMatcher.clicked.connect(self._menu_add_matcher)
        # When user clicks "Run Pipeline", execute the pipeline
        self.buttonRunPipeline.clicked.connect(self._run)

        # Connect search boxes to proxy filters
        self.editSearchStatsAll.textChanged.connect(self.prox_stats_all.setFilterFixedString)
        self.editSearchStatsRest.textChanged.connect(self.prox_stats_rest.setFilterFixedString)
        self.editSearchGeoAll.textChanged.connect(self.prox_geo_all.setFilterFixedString)
        self.editSearchGeoRest.textChanged.connect(self.prox_geo_rest.setFilterFixedString)
        self.editSearchMapped.textChanged.connect(self.prox_mapped.setFilterFixedString)

        # When the user selects a different matcher in the list, show its settings page
        self.listMatchers.currentRowChanged.connect(lambda i: self.stackMatcherSettings.setCurrentIndex(i))

    # ==============================================================================
    #  Public API: Load Data
    # ==============================================================================
    def load_data(self, stats_df: pd.DataFrame, geo_df: pd.DataFrame) -> None:
        """
        Receives the statistics and geo DataFrames from MainWindow.

        - Stores the full DataFrames internally.
        - Populates the 'All' tabs with these DataFrames.
        - Initializes unmatched_df and available_df as copies of the full tables.
        - Resets matched_df to empty and calls _refresh_views() to update all displays.
        """
        # Store copies of the full tables, resetting the index
        self._stats_df = stats_df.reset_index(drop=True)
        self._geo_df = geo_df.reset_index(drop=True)

        # Populate the 'All' models so they show the entire dataset
        self.mod_stats_all.set_frame(self._stats_df)
        self.mod_geo_all.set_frame(self._geo_df)

        # Initially, all stats are unmatched and all geo are available
        self.unmatched_df = self._stats_df.copy()
        self.available_df = self._geo_df.copy()
        # No rows have been matched yet
        self.matched_df = pd.DataFrame()
        # Update all views and labels
        self._refresh_views()

    # ==============================================================================
    #  Matcher Toolbox: Add / Remove Matchers
    # ==============================================================================
    def _menu_add_matcher(self) -> None:
        """
        Displays a small popup menu so the user can pick a matcher type.

        Options are:
          - Unique
          - Prefix
          - Fuzzy
          - Regex

        Each selection calls _add() with the chosen kind.
        """
        menu = QMenu(self)
        # Add menu entries for each matcher type
        menu.addAction("Unique").triggered.connect(lambda: self._add("unique"))
        menu.addAction("Prefix").triggered.connect(lambda: self._add("prefix"))
        menu.addAction("Fuzzy").triggered.connect(lambda: self._add("fuzzy"))
        menu.addAction("Regex").triggered.connect(lambda: self._add("regex"))

        # Position the menu just below the AddMatcher button
        menu.exec(self.buttonAddMatcher.mapToGlobal(QPoint(0, self.buttonAddMatcher.height())))

    def _add(self, kind: str) -> None:
        """
        Instantiates a new matcher widget of the specified kind and inserts it into the UI.

        - Assigns a unique ID to the matcher.
        - Defines a display name with that ID (e.g., "UVM#1" for UniqueValueMatcher).
        - Connects the matcher's removed and updated signals to internal handlers.
        - Adds the matcher to the internal list and the stacked settings widget.
        - Creates and selects a corresponding item in the listMatchers widget.
        - Calls _check_ready() to update the Run button state.
        """
        # Generate the next unique ID
        nr = next(self._ids)

        # Determine which stats columns to use in the matcher:
        # If DataStore.selected_columns is set, use that subset; otherwise use all stats columns
        stats_cols = DataStore.selected_columns if DataStore.selected_columns else self._stats_df.columns

        # Instantiate the appropriate matcher based on 'kind'
        if kind == "unique":
            matcher = UniqueValueMatcher(nr, stats_cols, self._geo_df.columns)
            name = f"UVM#{nr}"
        elif kind == "prefix":
            matcher = PrefixMatcher(nr, stats_cols, self._geo_df.columns)
            name = f"PRE#{nr}"
        elif kind == "regex":
            matcher = RegexMatcher(nr, stats_cols, self._geo_df.columns)
            name = f"REGEX#{nr}"
        else:  # kind == "fuzzy"
            matcher = FuzzyMatcher(nr, stats_cols, self._geo_df.columns)
            name = f"FUZZ#{nr}"

        # Connect matcher signals:
        #   - removed: so that _remove_matcher() is called when the user removes it
        #   - updated: so that we re-check whether the pipeline is ready to run
        matcher.removed.connect(lambda _=matcher: self._remove_matcher(matcher))
        matcher.updated.connect(self._check_ready)

        # Register the matcher and add its widget to the stacked settings panel
        self._matchers.append(matcher)
        self.stackMatcherSettings.addWidget(matcher)

        # Create a corresponding list item in listMatchers for ordering/removal
        item = QListWidgetItem(name)
        self.listMatchers.addItem(item)
        # Select the newly added matcher so the user can configure it immediately
        self.listMatchers.setCurrentItem(item)

        # Check whether the Run button should be enabled
        self._check_ready()

    def _remove_matcher(self, matcher) -> None:
        """
        Removes the specified matcher widget from both the UI and the internal list.

        - Finds the index of the matcher in self._matchers.
        - Removes it from the list, the QListWidget, and the stacked widget.
        - Deletes the widget to free resources.
        - Calls _check_ready() to update Run button state.
        """
        # Locate the matcher in our internal list
        idx = self._matchers.index(matcher)
        # Remove from internal list
        self._matchers.pop(idx)
        # Remove from the QListWidget
        self.listMatchers.takeItem(idx)
        # Remove from the stacked settings widget and delete
        self.stackMatcherSettings.removeWidget(matcher)
        matcher.deleteLater()
        # Update Run button enablement
        self._check_ready()

    # ==============================================================================
    #  Pipeline Execution
    # ==============================================================================
    def _run(self) -> None:
        """
        Executes the matcher pipeline in the configured order.

        Workflow:
          1. If no matchers are configured, do nothing.
          2. Show the progress bar and set its range to number of matchers.
          3. Initialize working copies of stats_left and geo_left, and an empty list for matched parts.
          4. For each matcher in sequence:
             a. Call matcher.match(stats_left, geo_left).
             b. If 'mapped' is returned, append to matched_parts and drop those rows from stats_left and geo_left.
             c. Update the progress bar and process Qt events to keep UI responsive.
          5. After all matchers run:
             a. Concatenate all matched parts into matched_df (or empty if none).
             b. Set unmatched_df to the remaining stats rows.
             c. Suffix available geo rows with "_geodata" and set available_df.
          6. Refresh all views and hide the progress bar.
          7. Emit mappingDone signal with matched_df.
        """
        # If there are no matchers configured, skip execution
        if not self._matchers:
            return

        # Show and configure the progress bar
        self.progressBar.setVisible(True)
        self.progressBar.setMaximum(len(self._matchers))
        self.progressBar.setValue(0)

        # Initialize working DataFrames for the pipeline
        stats_left = self._stats_df.copy()
        geo_left = self._geo_df.copy()
        matched_parts: List[pd.DataFrame] = []

        # Sequentially run each matcher
        for step, matcher in enumerate(self._matchers, 1):
            # Each matcher returns (matched_df, idx_stats, idx_geo)
            mapped, idx_stats, idx_geo = matcher.match(stats_left, geo_left)
            if mapped is not None:
                # Append the matched portion
                matched_parts.append(mapped)
                # Remove matched rows from the 'leftover' DataFrames
                stats_left = stats_left.drop(idx_stats)
                geo_left = geo_left.drop(idx_geo)

            # Update progress bar and process events for UI responsiveness
            self.progressBar.setValue(step)
            QApplication.processEvents()

        # Combine all matched parts into a single DataFrame
        self.matched_df = pd.concat(matched_parts, ignore_index=True) if matched_parts else pd.DataFrame()
        # The rows not matched from stats_left become the unmatched_df
        self.unmatched_df = stats_left.reset_index(drop=True)
        # The rows not matched from geo_left become available_df with '_geodata' suffix
        self.available_df = geo_left.add_suffix("_geodata").reset_index(drop=True)

        # Update table views and labels
        self._refresh_views()
        # Hide the progress bar
        self.progressBar.setVisible(False)
        # Signal that mapping is done, passing the matched DataFrame
        self.mappingDone.emit(self.matched_df)

    # ==============================================================================
    #  Helpers: Refresh Views and Check Ready State
    # ==============================================================================
    def _refresh_views(self) -> None:
        """
        Updates all five table views and status labels after any change in data.

        - Sets the 'rest' models to unmatched_df and available_df respectively.
        - Sets the 'mapped' model to matched_df, sorted by original index.
        - Updates labelMatched to show number of matched rows.
        - Updates labelTotal to show total rows in the statistics table.
        - Calls _check_ready() to update the Run button.
        - Calls _auto_resize() on each QTableView to adjust column widths.
        """
        # Update models for unmatched and available tables
        self.mod_stats_rest.set_frame(self.unmatched_df)
        self.mod_geo_rest.set_frame(self.available_df)
        # Update model for matched table, sorting by index to keep original order
        self.mod_mapped.set_frame(self.matched_df.sort_index())

        # Update the status labels
        self.labelMatched.setText(f"Matched: {len(self.matched_df)}")
        self.labelTotal.setText(f"Total rows: {len(self._stats_df)}")

        # Enable/disable Run button based on current state
        self._check_ready()

        # Resize all table views so their columns fit the content
        for tv in (self.tableViewStatsAll, self.tableViewGeoAll, self.tableViewStatsRest, self.tableViewGeoRest, self.tableViewMapped):
            self._auto_resize(tv)

    def _check_ready(self) -> None:
        """
        Determines whether the Run button should be enabled.

        The Run button becomes enabled only when:
          - Both statistics and geo DataFrames are non-empty.
          - At least one matcher widget is configured.
        """
        ready = bool(self._stats_df.size and self._geo_df.size and self._matchers)
        self.buttonRunPipeline.setEnabled(ready)

    @staticmethod
    def _auto_resize(tv) -> None:
        """
        Resizes columns and rows of the given QTableView to fit their contents.

        - Calls resizeColumnsToContents() on the view.
        - Sets horizontal header mode to Interactive to allow manual adjustments.
        - Calls resizeRowsToContents() for row height adjustments.
        """
        tv.resizeColumnsToContents()
        # TODO: Fix ResizeToContents Warning ...
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[attr-defined]
        tv.resizeRowsToContents()

    # ==============================================================================
    #  Navigation Guard Methods
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Allows navigation to the next step only if the matched DataFrame is non-empty.

        Returns True when at least one row has been successfully matched.
        """
        return not self.matched_df.empty

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Allows navigation back from this view at any time.

        Always returns True.
        """
        return True
