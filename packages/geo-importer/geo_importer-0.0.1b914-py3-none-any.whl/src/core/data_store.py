"""
Central in-memory repository (*quasi-singleton*) that keeps all
intermediate DataFrames while the import workflow is running.

This class uses only class attributes – no instance is ever created.
Access is always via DataStore.<attribute>, so every window/controller
can read/write data without passing objects around.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


# ==============================================================================
#  GeoMeta: Metadata container for chosen geographical CSV
# ==============================================================================
@dataclass(slots=True)
class GeoMeta:
    """
    Thin container for meta-information accompanying a geographical CSV selection.

    Attributes:
      type : Data set family (e.g. 'NUTS', 'LAU', …).
      version : Release/vintage identifier (e.g. '2023-01').
      level : Resolution or administrative level of the chosen CSV file.
    """

    type: str
    version: str
    level: str


# ==============================================================================
#  DataStore: Central repository for intermediate DataFrames
# ==============================================================================
class DataStore:
    # --------------------------------------------------------------------------
    #  User data (statistics)
    # --------------------------------------------------------------------------
    file_path: Optional[str] = None  # Absolute path of uploaded file
    df_user: Optional[pd.DataFrame] = None  # Filtered statistics DataFrame
    selected_columns: Optional[list[str]] = None  # Columns chosen by the user

    # --------------------------------------------------------------------------
    #  Geo data
    # --------------------------------------------------------------------------
    geo_meta: Optional[GeoMeta] = None  # Metadata about the loaded geo CSV
    df_geo: Optional[pd.DataFrame] = None  # Geo reference DataFrame

    # --------------------------------------------------------------------------
    #  Mapping result
    # --------------------------------------------------------------------------
    df_mapped: Optional[pd.DataFrame] = None  # Combined statistics-geo mapping

    # ========================================================================
    #  Mutators – always make a copy() so that external code cannot mutate store
    # ========================================================================
    @classmethod
    def set_upload(cls, path: str) -> None:
        """
        Store the absolute path of the user-uploaded file.

        Steps:
          1. Assign the given path to the class attribute `file_path`.
        """
        cls.file_path = path

    @classmethod
    def set_selection(cls, df: pd.DataFrame, columns: Optional[list[str]] | None = None) -> None:
        """
        Store the statistics DataFrame after column selection/filtering.

        Steps:
          1. Copy the given DataFrame to prevent external mutations.
          2. Store the user-selected columns for downstream steps.
        """
        cls.df_user = df.copy()
        cls.selected_columns = columns

    @classmethod
    def set_geo(cls, df: pd.DataFrame, meta: dict) -> None:
        """
        Store the geo reference table together with its meta-information.

        Steps:
          1. Copy the DataFrame to keep the original immutable.
          2. Convert the incoming metadata dict into a GeoMeta instance.
          3. Store both DataFrame and GeoMeta.
        """
        cls.df_geo = df.copy()
        cls.geo_meta = GeoMeta(**meta)

    @classmethod
    def set_mapping(cls, df: pd.DataFrame) -> None:
        """
        Persist the matched table (auto or manual).

        Steps:
          1. Copy the combined mapping DataFrame.
          2. Store it in `df_mapped` for downstream preview/export.
        """
        cls.df_mapped = df.copy()

    # --------------------------------------------------------------------------
    #  House-keeping
    # --------------------------------------------------------------------------
    @classmethod
    def clear(cls) -> None:
        """
        Reset all stored data – used when the user starts a new workflow run.

        Steps:
          1. Iterate over all relevant class attributes.
          2. Set each attribute to None to release references to DataFrames.
        """
        for attr in ("file_path", "df_user", "df_geo", "geo_meta", "df_mapped", "selected_columns"):
            setattr(cls, attr, None)
