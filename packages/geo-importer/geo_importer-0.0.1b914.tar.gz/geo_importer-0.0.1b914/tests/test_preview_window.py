from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

import src.views.map_preview.preview_window as preview_mod
from src.views.map_preview.preview_window import MapPreviewView


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """
    Ensure a QApplication instance exists for widget tests.
    """
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sample_stats_df():
    """
    Provide a sample statistics DataFrame with expected suffix columns.
    Columns include one ID with '_geodata' and one value with '_stats'.
    """
    return pd.DataFrame({"id_geodata": ["A", "B", "C"], "value_stats": [1.0, 2.0, 3.0]})


def make_simple_point_geojson():
    """
    Return a minimal GeoJSON FeatureCollection containing one Point feature.
    """
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"id": "A"}, "geometry": {"type": "Point", "coordinates": [10.0, 20.0]}}],
    }


def test_load_data_populates_combos_and_navigation(sample_stats_df):
    """
    Test that load_data fills the ID and value combo boxes correctly,
    and that navigation guards return expected values.
    """
    # Arrange: create MapPreviewView and sample DataFrame
    window = MapPreviewView()
    df = sample_stats_df

    # Act: load the statistics DataFrame into the preview window
    window.load_data(df)

    # Assert: ID combo has one entry mapping display 'id' to 'id_geodata'
    assert window.comboStatsId.count() == 1, "ID combo must have one item"
    assert window.comboStatsId.itemText(0) == "id", "Display text should strip '_geodata'"
    assert window.comboStatsId.itemData(0) == "id_geodata", "Stored data must be original column name"

    # Assert: Value combo has one entry mapping 'value' to 'value_stats'
    assert window.comboStatsValue.count() == 1, "Value combo must have one item"
    assert window.comboStatsValue.itemText(0) == "value", "Display text should strip '_stats'"
    assert window.comboStatsValue.itemData(0) == "value_stats", "Stored data must be original column name"

    # can_go_next should return True when data is loaded
    assert window.can_go_next() is True, "Navigation to next should be allowed when stats are loaded"
    # can_go_back always returns True
    assert window.can_go_back() is True, "Navigation back should always be allowed"


def test_reproject_geojson_keeps_identity_and_handles_polygon():
    """
    Test the _reproject_geojson static method for identity reprojection
    on both Point and nested Polygon coordinates.
    """
    # Arrange: prepare Point GeoJSON
    pt = make_simple_point_geojson()
    # Act: reproject from 4326 to 4326 (identity)
    out_pt = MapPreviewView._reproject_geojson(pt, 4326, 4326)
    coords_pt = out_pt["features"][0]["geometry"]["coordinates"]
    # Assert: coordinates remain unchanged
    assert pytest.approx(coords_pt) == [10.0, 20.0], "Point coordinates must remain the same on identity reprojection"

    # Arrange: prepare Polygon GeoJSON
    poly = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "B"},
                "geometry": {"type": "Polygon", "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]]},
            }
        ],
    }
    # Act: identity reprojection on Polygon
    out_poly = MapPreviewView._reproject_geojson(poly, 4326, 4326)
    coords_poly = out_poly["features"][0]["geometry"]["coordinates"]
    # Assert: nested coordinate structure is preserved
    assert pytest.approx(coords_poly[0][0]) == [0.0, 0.0], "First polygon vertex must be unchanged"
    assert pytest.approx(coords_poly[0][2]) == [1.0, 1.0], "Third polygon vertex must be unchanged"


def test_render_exits_gracefully_without_data_or_geo(monkeypatch):
    """
    Test that calling _render() with missing GeoJSON or stats does not raise exceptions
    and that informational dialogs are triggered instead.
    """
    # Arrange: initialize window and spy on dialogs
    window = MapPreviewView()
    # Replace QMessageBox methods with no-ops to prevent GUI blocking
    monkeypatch.setattr(preview_mod.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(preview_mod.QMessageBox, "warning", lambda *args, **kwargs: None)

    # Act & Assert: neither geo nor stats loaded → no exception
    window._geojson = None
    window._stats_df = None
    window._render()

    # Act & Assert: geo loaded but stats empty → no exception
    window._geojson = make_simple_point_geojson()
    window._stats_df = pd.DataFrame()
    window._render()

    # Act & Assert: stats loaded but geo missing → no exception
    window._geojson = None
    window._stats_df = pd.DataFrame({"id": [], "value": []})
    window._render()


def test_render_writes_html_and_loads(tmp_path, monkeypatch, sample_stats_df):
    """
    Test that _render() creates an HTML file when both stats and GeoJSON are present
    and that QWebEngineView.load is called with the correct file path.
    """
    # Arrange: prepare window with data and geojson
    window = MapPreviewView()
    window._geojson = make_simple_point_geojson()
    window._stats_df = sample_stats_df

    # Populate UI combos for join ID and value columns
    window.comboGeoId.clear()
    window.comboGeoId.addItem("id", "id")
    window.comboGeoId.setCurrentIndex(0)
    window.comboStatsId.clear()
    window.comboStatsId.addItem("id", "id_geodata")
    window.comboStatsId.setCurrentIndex(0)
    window.comboStatsValue.clear()
    window.comboStatsValue.addItem("value", "value_stats")
    window.comboStatsValue.setCurrentIndex(0)

    # Spy on _view.load to capture the URL
    loaded = {}

    def fake_load(qurl):
        loaded["path"] = Path(qurl.toLocalFile())

    monkeypatch.setattr(window._view, "load", fake_load)

    # Act: call render to generate and load the map
    window._render()

    # Assert: an HTML file was written and load was called with it
    html_path = loaded.get("path")
    assert html_path is not None, "Expected load() to be called with a file URL"
    assert html_path.exists(), f"Generated HTML file must exist at {html_path}"
