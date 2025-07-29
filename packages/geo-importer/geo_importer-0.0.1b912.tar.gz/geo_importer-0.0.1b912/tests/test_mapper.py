import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from src.mapper.base.matcher_base import BaseMatcher
from src.mapper.matchers.fuzzy_matcher import FuzzyMatcher
from src.mapper.matchers.prefix_matcher import PrefixMatcher
from src.mapper.matchers.regex_matcher import RegexMatcher
from src.mapper.matchers.unique_value_matcher import UniqueValueMatcher


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """
    Ensure that a QApplication instance exists for widget-based matcher tests.
    """
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sample_data():
    """
    Provide sample DataFrames for statistics and geo data.

    stats_df has three codes and values.
    geo_df has three region codes and populations.
    Returns a tuple (stats_df, geo_df).
    """
    stats = pd.DataFrame({"code": ["AAA123", "BBB456", "CCC789"], "value": [10, 20, 30]}, index=[0, 1, 2])
    geo = pd.DataFrame({"region": ["AAA", "BBB", "DDD"], "pop": [1000, 2000, 3000]}, index=[0, 1, 2])
    return stats, geo


def test_base_matcher_build_result():
    """
    Test combining one stats row and one geo row with an optional label.
    """
    # Arrange: create simple one-row DataFrames
    stats_df = pd.DataFrame({"a": [1]}, index=[0])
    geo_df = pd.DataFrame({"b": [2]}, index=[0])

    # Act: build combined result with label
    result = BaseMatcher.build_result(stats_df, geo_df, label="TestLabel")

    # Assert: column names have correct suffixes and label column
    assert list(result.columns) == ["a_stats", "b_geodata", "matcher"], "Columns should be suffixed and include matcher"
    assert result.loc[0, "matcher"] == "TestLabel", "Matcher label must match provided label"
    assert result.loc[0, "a_stats"] == 1 and result.loc[0, "b_geodata"] == 2, "Values must be carried over correctly"


def test_unique_value_matcher_exact_and_normalized(sample_data):
    """
    Test UniqueValueMatcher for exact and normalized matching behavior.
    """
    stats_df, geo_df = sample_data
    matcher = UniqueValueMatcher(nr=1, excel_cols=["code"], geo_cols=["region"])

    # Act & Assert: without normalization no rows should match
    df_none, ex_none, ge_none = matcher.match(stats_df, geo_df)
    assert df_none is None and ex_none is None and ge_none is None, "No matches expected when strings differ exactly"

    # Arrange: monkey-patch normalize to compare prefixes only
    matcher.normalize = lambda s: s[:3]

    # Act: now first two codes should match their geo prefixes
    df2, ex2, ge2 = matcher.match(stats_df, geo_df)

    # Assert: correct indices and DataFrame structure
    assert ex2 == [0, 1], "Expected stats indices [0,1] for matched prefixes"
    assert sorted(ge2) == [0, 1], "Expected geo indices [0,1]"
    assert df2.shape[0] == 2, "Result DataFrame should have two rows"
    # TODO: FIX: Expected type 'Iterable[object]', got 'bool' instead
    assert all(df2["matcher"] == matcher.description()), "All matcher labels must match description"
    assert "code_stats" in df2.columns and "region_geodata" in df2.columns, "Column suffixes must be present in result"


def test_prefix_matcher_default_length(sample_data):
    """
    Test PrefixMatcher with default prefix length of 3 characters.
    """
    stats_df, geo_df = sample_data
    matcher = PrefixMatcher(nr=2, stats_cols=["code"], geo_cols=["region"])

    # Act: perform matching with default settings (length=3)
    df, ex_idx, ge_idx = matcher.match(stats_df, geo_df)

    # Assert: only first two entries match by prefix AAA and BBB
    assert ex_idx == [0, 1], "Expected stats indices [0,1]"
    assert sorted(ge_idx) == [0, 1], "Expected geo indices [0,1]"
    assert df.shape[0] == 2, "Result should contain two matched rows"
    assert matcher.description().startswith("PRE#2:code→region["), "Description must include matcher ID and prefix length"


def test_regex_matcher_valid_and_invalid(sample_data):
    """
    Test RegexMatcher for valid extraction and handling of invalid patterns.
    """
    stats_df, geo_df = sample_data
    matcher = RegexMatcher(nr=3, excel_cols=["code"], geo_cols=["region"])

    # Arrange: select columns and set regex to capture first three letters
    matcher.comboExcel.setCurrentText("code")
    matcher.comboGeo.setCurrentText("region")
    matcher.editExcelRegex.setText(r"^([A-Z]{3})")
    matcher.editGeoRegex.setText(r"^([A-Z]{3})")

    # Act: perform matching
    df_valid, ex_valid, ge_valid = matcher.match(stats_df, geo_df)

    # Assert: first two tokens match exactly
    assert ex_valid == [0, 1], "Expected regex match for first two rows"
    assert sorted(ge_valid) == [0, 1], "Expected geo indices [0,1]"
    assert df_valid.shape[0] == 2, "Result DataFrame must have two rows"
    assert all(df_valid["matcher"] == matcher.description()), "Matcher labels must reflect description"

    # Arrange: set an invalid regex pattern
    matcher.editExcelRegex.setText(r"([)")

    # Act: call match with invalid regex
    df_invalid, ex_inv, ge_inv = matcher.match(stats_df, geo_df)

    # Assert: invalid pattern should yield no matches
    assert df_invalid is None and ex_inv is None and ge_inv is None, "Invalid regex must result in no matches"


def test_fuzzy_matcher_threshold_and_empty_columns(sample_data):
    """
    Test FuzzyMatcher for threshold scaling, one-to-one mapping, and empty selection behavior.
    """
    stats_df, geo_df = sample_data
    matcher = FuzzyMatcher(nr=4, excel_cols=["code"], geo_cols=["region"])

    # Arrange: set threshold to 0 so it scales to 0*100 = 0
    matcher.spinThreshold.setValue(0)
    matcher.comboExcel.setCurrentText("code")
    matcher.comboGeo.setCurrentText("region")

    # Act: perform fuzzy matching
    df_fuzzy, ex_fuzzy, ge_fuzzy = matcher.match(stats_df, geo_df)

    # Assert: only two best prefix matches should be accepted one-to-one
    assert set(ex_fuzzy) == {0, 1}, "Expected stats indices {0,1} for fuzzy prefix matches"
    assert set(ge_fuzzy) == {0, 1}, "Expected geo indices {0,1}"
    assert df_fuzzy.shape[0] == 2, "Result must have two rows"
    assert all(df_fuzzy["matcher"].str.startswith("FUZZ#4:")), "Matcher labels must include FUZZ# identifier and score"

    # Act: clear both combos to simulate no column selected
    matcher.comboExcel.clear()
    matcher.comboGeo.clear()
    df_none, ex_none2, ge_none2 = matcher.match(stats_df, geo_df)

    # Assert: no selection yields no matches
    assert df_none is None and ex_none2 is None and ge_none2 is None, "Clearing column selections must result in no matches"
