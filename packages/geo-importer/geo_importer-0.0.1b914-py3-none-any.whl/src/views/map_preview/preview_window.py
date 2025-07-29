"""
HTML-based map preview (Folium + Qt WebEngine).

The dialog joins a statistics table to a GeoJSON (on arbitrary key columns),
renders a quick choropleth and shows the result inside a QWebEngineView.

Focus lies on ease-of-use – there are no map-editing capabilities.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import branca.colormap as bcm
import folium
import pandas as pd
from matplotlib.colors import rgb2hex
from matplotlib.pyplot import colormaps
from pyproj import Transformer
from PySide6.QtCore import QFileInfo, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QSizePolicy, QVBoxLayout

from src.views.map_preview.ui.preview_window_ui import Ui_PreviewWindow


# ==============================================================================
#  MapPreviewView: Leaflet-based quick-look for joined statistic / geo data.
# ==============================================================================
class MapPreviewView(QMainWindow, Ui_PreviewWindow):
    """
    Provides a quick-look preview of joined statistic data and GeoJSON on a Leaflet map.

    It creates a choropleth by joining a DataFrame to a GeoJSON file and loads
    the generated HTML into a QWebEngineView.  There is no editing capability,
    only viewing.
    """

    # Signal that fires after the HTML finishes loading so callers can take screenshots
    renderingFinished = Signal()

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Sets up the preview window, initializes caches, configures the map view,
        and connects UI buttons to their handlers.
        """
        super().__init__()
        # Load the UI definitions from the .ui file
        self.setupUi(self)

        # ---------------- Runtime Caches ----------------
        # Will store the loaded GeoJSON as a dict
        self._geojson: Optional[dict] = None
        # Will store the statistics DataFrame
        self._stats_df: Optional[pd.DataFrame] = None
        # Will keep the last bounds for zooming after loading the map
        self._last_bounds: Optional[list] = None
        # Will hold the name of the folium map object for JavaScript callbacks
        self._map_name: Optional[str] = None

        # ---------------- Embed WebEngineView ----------------
        # Create a QWebEngineView inside the right pane of the splitter
        self._view = QWebEngineView(self.pageMap)
        # Allow it to expand to fill available space
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # type: ignore[arg-type]
        # Add the view into a vertical layout to remove margins
        layout = QVBoxLayout(self.pageMap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

        # Set a balanced splitter layout
        self._fix_splitter()

        # ---------------- Enable Local File Access ----------------
        # Folium output needs to load local CSS/JS, so allow file URL access
        settings = self._view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)  # type: ignore[arg-type]
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)  # type: ignore[arg-type]

        # Connect map load finished signal to a handler for fitting bounds
        self._view.loadFinished.connect(self._on_load_finished)

        # ---------------- Button Connections ----------------
        # Connect the "Browse GeoJSON" button to its handler
        self.buttonBrowseGeo.clicked.connect(self._browse_geojson)
        # Connect the "Render" button to build and show the map
        self.buttonRender.clicked.connect(self._render)

    # ==================================================================
    #  Splitter Helpers
    # ==================================================================
    def resizeEvent(self, event):
        """
        Keeps the splitter panels evenly divided when the window is resized.

        Overrides the default resizeEvent to adjust splitter sizes.
        """
        super().resizeEvent(event)
        # Calculate total width and set both sides to half
        total = self.splitMain.size().width()
        self.splitMain.setSizes([total // 2, total // 2])

    def _fix_splitter(self) -> None:
        """
        Ensures that the splitter divides the window 50/50 initially.

        Called once after setup to enforce equal stretch factors.
        """
        # Set both panes to expand equally
        self.splitMain.setStretchFactor(0, 1)
        self.splitMain.setStretchFactor(1, 1)
        # After layout is done, force equal sizes
        QTimer.singleShot(0, lambda: self.splitMain.setSizes([1, 1]))

    # ==================================================================
    #  Data & GeoJSON Loading
    # ==================================================================
    def load_data(self, df_stats: pd.DataFrame) -> None:
        """
        Receives the statistics DataFrame from MainWindow and populates the dropdowns.

        Extracts columns ending in "_geodata" for IDs and "_stats" for values,
        then shows display names without suffixes.
        """
        # Copy the provided DataFrame to avoid modifying the original
        self._stats_df = df_stats.copy()

        # Identify columns for GeoJSON join keys and statistic values
        id_cols = [c for c in df_stats.columns if c.endswith("_geodata")]
        val_cols = [c for c in df_stats.columns if c.endswith("_stats")]

        # Create user-friendly display names by stripping suffixes
        id_display = [c[:-8] for c in id_cols]  # Remove "_geodata"
        val_display = [c[:-6] for c in val_cols]  # Remove "_stats"

        # Clear any existing items from the combo boxes
        self.comboStatsId.clear()
        self.comboStatsValue.clear()

        # Populate the ID dropdown: display name with original column as data
        for display, original in zip(id_display, id_cols):
            self.comboStatsId.addItem(display, original)
        # Populate the value dropdown similarly
        for display, original in zip(val_display, val_cols):
            self.comboStatsValue.addItem(display, original)

        # Set default selection to first element if lists are non-empty
        if id_cols:
            self.comboStatsId.setCurrentIndex(0)
        if val_cols:
            self.comboStatsValue.setCurrentIndex(0)

    def _browse_geojson(self) -> None:
        """
        Opens a file dialog to pick a GeoJSON file and validates its structure.

        If the file is not a FeatureCollection, shows a warning.
        Otherwise, stores the parsed JSON and populates the ID dropdown.
        """
        # Prompt the user to select a GeoJSON or JSON file
        path, _ = QFileDialog.getOpenFileName(self, "Pick GeoJSON", "", "GeoJSON (*.geojson *.json)")
        if not path:
            # User canceled, do nothing
            return

        try:
            # Read the file content and parse as JSON
            gj = json.loads(Path(path).read_text(encoding="utf-8"))
            # Ensure it is a FeatureCollection type
            if gj.get("type") != "FeatureCollection":
                raise ValueError("Expected a FeatureCollection GeoJSON.")
        except Exception as exc:
            # If parsing fails or type is wrong, show a warning and abort
            QMessageBox.warning(self, "Error", f"Invalid GeoJSON:\n{exc}")
            return

        # Store the parsed GeoJSON for later use
        self._geojson = gj
        # Show just the file name (not full path) in the UI
        self.lineEditGeoPath.setText(QFileInfo(path).fileName())

        # Collect all property keys from features to let user pick the join key
        keys = {k for feat in gj["features"] for k in feat.get("properties", {})}
        # Clear the existing items and add sorted keys
        self.comboGeoId.clear()
        self.comboGeoId.addItems(sorted(keys))

    # ==================================================================
    #  Rendering the Map
    # ==================================================================
    def _render(self) -> None:
        """
        Assembles a Folium map by joining the stats DataFrame to the GeoJSON.

        Checks for missing inputs, reprojects if needed, categorizes values,
        then renders a choropleth or categorical fill and loads the HTML.
        """
        # --- Sanity Checks ---
        # Ensure a GeoJSON was loaded
        if self._geojson is None:
            QMessageBox.information(self, "GeoJSON missing", "Please load a GeoJSON first.")
            return
        # Ensure statistics DataFrame is available and not empty
        if self._stats_df is None or self._stats_df.empty:
            QMessageBox.information(self, "Statistics missing", "No statistics data available.")
            return

        # Get the selected keys from UI dropdowns
        geo_key = self.comboGeoId.currentText().strip()
        stats_id = self.comboStatsId.currentData()  # original column name for join
        value_key = self.comboStatsValue.currentData()  # original column for values
        if not (geo_key and stats_id and value_key):
            QMessageBox.information(self, "Selection incomplete", "Please select all dropdowns.")
            return

        # --- CRS Handling ---
        # Check GeoJSON 'crs' property to see if it uses EPSG:3035 and reproject to 4326 if needed
        crs_name = self._geojson.get("crs", {}).get("properties", {}).get("name", "")
        if "3035" in crs_name:
            # Reproject all coordinates from EPSG:3035 to EPSG:4326
            gj = self._reproject_geojson(self._geojson, 3035, 4326)
        else:
            # Keep original GeoJSON if already in WGS84 or unknown CRS
            gj = self._geojson

        # --- Prepare Statistics DataFrame ---
        # Select only the join ID and value columns, drop any rows with NaN
        df = self._stats_df[[stats_id, value_key]].dropna(subset=[stats_id, value_key]).rename(columns={stats_id: "id", value_key: "value"})
        # Convert IDs to string to match GeoJSON property types
        df["id"] = df["id"].astype(str)

        # Build a lookup dict from ID to value, then filter GeoJSON features
        lookup = dict(zip(df["id"], df["value"]))
        feats = []
        raw_values = []
        for feature in gj["features"]:
            # Get the ID from GeoJSON properties (converted to string)
            gid = str(feature["properties"].get(geo_key))
            if gid in lookup:
                # Store matched value under a temporary property for styling
                feature["properties"]["__val__"] = lookup[gid]
                feats.append(feature)
                raw_values.append(lookup[gid])

        # If no features matched, inform the user and abort
        if not feats:
            QMessageBox.information(self, "No matches", "ID columns do not overlap.")
            return

        # Create a filtered GeoJSON containing only matched features
        gj_filtered = {"type": "FeatureCollection", "features": feats}

        # --- Initialize Folium Map ---
        fmap = folium.Map(tiles="Cartodb Positron", control_scale=True)  # OpenStreetMap
        # Store the map object name for later JS interaction
        self._map_name = fmap.get_name()

        # Try to interpret values as numeric, replacing commas with dots
        numeric_vals = pd.to_numeric(pd.Series(raw_values).astype(str).str.replace(",", ".", regex=False), errors="coerce")

        if numeric_vals.notna().all():
            # ---- Numeric Choropleth ----
            # Determine min/max for the color scale
            min_value, max_value = numeric_vals.min(), numeric_vals.max()
            # Choose 20 buckets from the viridis colormap
            # viridis = cm.get_cmap("viridis", 20)
            viridis = colormaps["viridis"].resampled(20)
            palette = [rgb2hex(viridis(i)) for i in range(20)]
            # Create a LinearColormap for the data range
            cmap = bcm.LinearColormap(palette, vmin=min_value, vmax=max_value, caption=value_key).to_step(n=20)

            def style_numeric(feat):
                """
                Assigns a fill color based on the numeric value in __val__.

                Falls back to min_value if parsing fails.
                """
                try:
                    val = float(str(feat["properties"]["__val__"]).replace(",", "."))
                except ValueError:
                    val = min_value
                return {"fillColor": cmap(val), "color": "#333", "weight": 0.5, "fillOpacity": 0.8}

            # Add the GeoJSON layer with numeric styling
            layer = folium.GeoJson(gj_filtered, style_function=style_numeric, name="values")
            layer.add_to(fmap)
            # Add the color legend to the map
            cmap.add_to(fmap)
            # Retrieve bounds for zooming to features
            bounds = layer.get_bounds()

        else:
            # ---- Categorical Fill ----
            # Determine unique categories from raw_values
            categories = sorted({str(v) for v in raw_values})
            # Use a predefined categorical palette
            paired = bcm.linear.Paired_12.scale(0, len(categories) - 1)
            cat2col = {cat: paired(i) for i, cat in enumerate(categories)}

            def style_cat(feat):
                """
                Assigns a fill color based on the categorical value in __val__.
                """
                return {"fillColor": cat2col[str(feat["properties"]["__val__"])], "color": "#333", "weight": 0.5, "fillOpacity": 0.8}

            # Add the GeoJSON layer with categorical styling
            layer = folium.GeoJson(gj_filtered, style_function=style_cat, name="categories")
            layer.add_to(fmap)
            bounds = layer.get_bounds()

            # Build a simple HTML legend for categories
            legend_entries = "".join(
                f"<i style='background:{col};width:12px;height:12px;" f"display:inline-block;margin-right:6px;'></i>{cat}<br/>"
                for cat, col in cat2col.items()
            )
            legend_html = (
                "<div style='position: fixed; bottom: 30px; left: 10px;"
                "background: white; padding: 8px; border:1px solid gray;"
                "max-height:200px; overflow:auto; font-size:12px; z-index:1000;'>"
                f"<b>{value_key}</b><br/>{legend_entries}</div>"
            )
            # Inject the legend HTML into the map
            fmap.get_root().html.add_child(folium.Element(legend_html))  # type: ignore[attr-defined]

        # Add layer controls so user can toggle layers
        folium.LayerControl(collapsed=False).add_to(fmap)
        # Store the computed bounds for later JS fitting
        self._last_bounds = bounds

        # --- Save Map HTML and Load into QWebEngineView ---
        output_directory = tempfile.mkdtemp(prefix="pv_folium_")
        html_path = os.path.join(output_directory, "map.html")
        # Write the HTML file to a temporary directory
        fmap.save(html_path)
        # Load the local HTML file into the QWebEngineView
        self._view.load(QUrl.fromLocalFile(html_path))

        # Notify any listeners that rendering is complete
        self.renderingFinished.emit()

    # ==================================================================
    #  WebEngine Callbacks
    # ==================================================================
    def _on_load_finished(self, ok: bool) -> None:
        """
        Zooms and centers the Leaflet map to include all joined polygons once HTML finishes loading.

        Runs a small JavaScript snippet to call leaflet.fitBounds().
        """
        # Proceed only if load succeeded and bounds and map name are available
        if not ok or not (self._last_bounds and self._map_name):
            return

        # Rebalance splitter panels again
        total = self.splitMain.size().width()
        self.splitMain.setSizes([total // 2, total // 2])

        # JavaScript to fit the map view to the data bounds
        js = f"""
        (function() {{
            var raw = {self._last_bounds};
            var map = {self._map_name};
            map.invalidateSize();
            var bb = L.latLngBounds(raw);
            var zoom = map.getBoundsZoom(bb, false);
            var sw = bb.getSouthWest();
            var ne = bb.getNorthEast();
            map.setView([(sw.lat + ne.lat)/2, (sw.lng + ne.lng)/2], zoom);
        }})();
        """
        # Execute the JS in the QWebEngineView context
        self._view.page().runJavaScript(js)

    # ==================================================================
    #  Helper Methods
    # ==================================================================
    @staticmethod
    def _reproject_geojson(gj: dict, src_epsg: int, dst_epsg: int = 4326) -> dict:
        """
        Reprojects all coordinates in the GeoJSON from one CRS to another.

        Walks through nested coordinate arrays recursively and applies pyproj Transformer.
        """
        # Create a transformer from source EPSG to destination EPSG
        tf = Transformer.from_crs(src_epsg, dst_epsg, always_xy=True)

        def _recurse(coordinates):
            # If coordinates represent a single point [lon, lat], transform it
            if isinstance(coordinates[0], (float, int)):
                lon, lat = tf.transform(coordinates[0], coordinates[1])
                return [lon, lat]
            # If coordinates represent nested rings or multipolygons, recurse deeper
            return [_recurse(c) for c in coordinates]

        # Build a new GeoJSON structure with transformed coordinates
        out = {"type": "FeatureCollection", "features": []}
        for feat in gj["features"]:
            nf = feat.copy()
            geom = feat["geometry"].copy()
            geom["coordinates"] = _recurse(geom["coordinates"])
            nf["geometry"] = geom
            out["features"].append(nf)
        return out

    # ==================================================================
    #  Navigation Guards
    # ==================================================================
    def can_go_next(self) -> bool:
        """
        Allows navigation to the next step only if statistics data has been loaded.

        Returns True when a non-empty DataFrame is present.
        """
        return self._stats_df is not None and not self._stats_df.empty

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Always allows going back from this view.

        Returns True unconditionally.
        """
        return True
