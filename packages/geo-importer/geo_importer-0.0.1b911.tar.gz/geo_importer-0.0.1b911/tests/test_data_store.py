import pandas as pd

from src.core.data_store import DataStore, GeoMeta


def test_set_upload_and_clear():
    """
    Test that set_upload correctly stores the file path and clear resets it.
    """
    # Ensure DataStore is in a clean state before testing
    DataStore.clear()

    # Store a sample file path
    DataStore.set_upload("/tmp/file.csv")
    # Verify the file_path attribute holds the stored path
    assert DataStore.file_path == "/tmp/file.csv"

    # Clear the DataStore again to reset state
    DataStore.clear()
    # Confirm file_path is reset to None after clear
    assert DataStore.file_path is None


def test_set_selection_creates_copy_and_records_columns():
    """
    Test that set_selection stores a copy of the DataFrame and records selected columns.
    """
    # Start with a clean DataStore
    DataStore.clear()

    # Create an original DataFrame for selection
    df_original = pd.DataFrame({"a": [1, 2]})
    # Apply selection specifying the 'a' column
    DataStore.set_selection(df_original, ["a"])

    # Check that selected_columns matches the provided list
    assert DataStore.selected_columns == ["a"]
    # Verify that df_user equals the original data by content
    assert DataStore.df_user.equals(df_original)
    # Ensure that df_user is a copy, not the same object
    assert DataStore.df_user is not df_original


def test_set_geo_and_set_mapping_store_data_and_metadata():
    """
    Test that set_geo stores a copy of the geo DataFrame and metadata, and set_mapping stores mapping DataFrame.
    """
    # Reset DataStore to clear previous state
    DataStore.clear()

    # Prepare a sample geo DataFrame
    geo_df = pd.DataFrame({"id": [1]})
    # Define metadata dictionary for GeoMeta
    meta = {"type": "NUTS", "version": "2024", "level": "3"}

    # Store geo data and metadata into DataStore
    DataStore.set_geo(geo_df, meta)
    # Confirm df_geo matches the original DataFrame by content
    assert DataStore.df_geo.equals(geo_df)
    # Confirm metadata is correctly instantiated and populated
    assert isinstance(DataStore.geo_meta, GeoMeta)
    assert DataStore.geo_meta.type == "NUTS"
    assert DataStore.geo_meta.version == "2024"
    assert DataStore.geo_meta.level == "3"

    # Use set_mapping to store the mapping DataFrame
    DataStore.set_mapping(geo_df)
    # Confirm df_mapped matches the geo_df by content
    assert DataStore.df_mapped.equals(geo_df)


def test_clear_resets_all_attributes_to_none():
    """
    Test that clear method resets all DataStore attributes to None.
    """
    # Populate all DataStore attributes with sample data
    DataStore.set_upload("/tmp/foo.csv")
    df_sample = pd.DataFrame({"a": [1]})
    DataStore.set_selection(df_sample, ["a"])
    DataStore.set_geo(df_sample, {"type": "NUTS", "version": "v", "level": "1"})
    DataStore.set_mapping(df_sample)

    # Clear all stored data in DataStore
    DataStore.clear()

    # Assert every attribute is reset to None after clear
    assert DataStore.file_path is None
    assert DataStore.df_user is None
    assert DataStore.selected_columns is None
    assert DataStore.df_geo is None
    assert DataStore.geo_meta is None
    assert DataStore.df_mapped is None
