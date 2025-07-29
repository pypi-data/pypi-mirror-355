"""
Export logic module.

This module contains the core logic for data export operations,
separated from the UI components in export_window.py.
"""

from __future__ import annotations

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

from src.core.data_store import DataStore

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ==============================================================================
#  ExportLogic: Core logic for data export operations
# ==============================================================================
class ExportLogic:
    """
    Core logic for data export operations.

    Responsibilities:
      1. Identify ID and value columns for export.
      2. Process column names to remove importer-specific suffixes.
      3. Collect metadata for the dataset, including geo metadata if available.
      4. Export the selected columns and metadata as CSV and YAML inside a ZIP archive.
    """

    def __init__(self):
        """
        Initializes the export logic.

        - Sets up an internal placeholder for the DataFrame to export.
        """
        self._current_df: Optional[pd.DataFrame] = None

    # ==============================================================================
    #  Data Preparation: Load DataFrame and identify columns
    # ==============================================================================
    def load_data(self, df_stats: pd.DataFrame) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Processes the DataFrame to prepare column lists for export.

        Steps:
          1. Store the provided DataFrame as _current_df.
          2. If the DataFrame is None or empty, return empty lists.
          3. Identify ID columns by filtering names ending with "_geodata".
          4. Identify value columns by filtering names ending with "_stats".
          5. Build display names by removing the suffixes from the column names.
          6. Return tuples of display and original names for both ID and value columns.
        """
        self._current_df = df_stats
        if df_stats is None or df_stats.empty:
            return [], [], [], []

        # Identify ID columns by suffix "_geodata"
        id_cols = [c for c in df_stats.columns if c.endswith("_geodata")]
        # Identify value columns by suffix "_stats"
        val_cols = [c for c in df_stats.columns if c.endswith("_stats")]

        # Create display names by stripping the suffixes
        id_display = [c[:-8] for c in id_cols]  # Remove "_geodata"
        val_display = [c[:-6] for c in val_cols]  # Remove "_stats"

        return id_display, id_cols, val_display, val_cols

    # ==============================================================================
    #  Helper: Process column names for final CSV
    # ==============================================================================
    @staticmethod
    def process_column_name(col: str) -> str:
        """
        Removes importer-specific suffixes from a column name.

        - If name ends with "_geodata", strip that suffix.
        - If name ends with "_stats", strip that suffix.
        - Otherwise, return the name unchanged.
        """
        if col.endswith("_geodata"):
            return col[:-8]
        if col.endswith("_stats"):
            return col[:-6]
        return col

    # ==============================================================================
    #  Metadata Collection
    # ==============================================================================
    def get_metadata(self, id_col: str, val_col: str, name: str, description: str, source: str, year: int, data_type: str) -> Dict[str, Any]:
        """
        Collects all metadata required for export.

        Steps:
          1. Build a dictionary with trimmed values for name, description, source, year, and type.
          2. Add processed ID and value column names (without suffixes).
          3. If geo metadata is available in DataStore, include geo data details.
          4. Return the complete metadata dictionary.
        """
        metadata: Dict[str, Any] = {
            "name": name.strip(),
            "description": description.strip(),
            "source": source.strip(),
            "year": year,
            "type": data_type,
            "id_column": self.process_column_name(id_col),
            "value_column": self.process_column_name(val_col),
        }

        # If geographical metadata is present in the DataStore, add it
        if DataStore.geo_meta is not None:
            metadata["geo_data"] = {"type": DataStore.geo_meta.type, "version": DataStore.geo_meta.version, "level": DataStore.geo_meta.level}

        return metadata

    # ==============================================================================
    #  Export Data: Write CSV, YAML, and package into ZIP
    # ==============================================================================
    def export_data(self, id_col: str, val_col: str, metadata: Dict[str, Any], target_path: str) -> None:
        """
        Exports the data to a ZIP file containing a CSV and a YAML file.

        Steps:
          1. Validate that _current_df is set and non-empty; otherwise raise an error.
          2. Create a temporary directory to hold CSV and YAML files.
          3. Prepare the export DataFrame with only the two selected columns.
             - Rename them to "GEO_ID" and "VALUE" for consistency.
          4. Write the DataFrame to a CSV file named data.csv in the temp directory.
          5. Dump the metadata dictionary to a YAML file named metadata.yaml in the temp directory.
          6. Create a ZIP archive at target_path and add both data.csv and metadata.yaml.
        """
        if self._current_df is None or self._current_df.empty:
            raise ValueError("No data available for export")

        # Use a temporary directory to stage CSV and YAML before zipping
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # ---------------------------
            #  CSV Export
            # ---------------------------
            # Select only ID and value columns from the DataFrame
            df_export = self._current_df[[id_col, val_col]].copy()
            # Rename columns for final output
            df_export.columns = ["GEO_ID", "VALUE"]
            csv_path = tmp_path / "data.csv"
            # Write CSV without row indices
            df_export.to_csv(csv_path, index=False)

            # ---------------------------
            #  YAML Export
            # ---------------------------
            yaml_path = tmp_path / "metadata.yaml"
            # Dump metadata to YAML using PyYAML
            with open(yaml_path, "w", encoding="utf-8") as fh:
                yaml.dump(metadata, fh, allow_unicode=True, sort_keys=False)

            # ---------------------------
            #  ZIP Packaging
            # ---------------------------
            # Create a ZIP archive and include both files
            with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Add data.csv under the name "data.csv"
                zf.write(csv_path, arcname="data.csv")
                # Add metadata.yaml under the name "metadata.yaml"
                zf.write(yaml_path, arcname="metadata.yaml")
