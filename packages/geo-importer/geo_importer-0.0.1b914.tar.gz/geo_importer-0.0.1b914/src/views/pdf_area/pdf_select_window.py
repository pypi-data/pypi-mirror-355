"""
PDF table selector (read-only).

This module provides a dialog window that allows users to view a PDF page,
draw a rectangle over a region they want to extract as a table, and then use
the Camelot library to extract only that selected area. The extracted table
is displayed in a read-only QTableWidget, and the resulting DataFrame is
emitted via the `extractionReady` signal.

The main class, PdfAreaView, inherits from QMainWindow and the generated
UI class Ui_PDFWindow. It manages the following responsibilities:

1. Loading a PDF file using PyMuPDF (fitz).
2. Rendering pages at a high zoom level for accurate selection.
3. Capturing mouse events to allow the user to draw a red rectangle over the
   desired region on the PDF page.
4. Converting the rectangle's scene coordinates to PDF coordinate space (points)
   so Camelot can understand the extraction area.
5. Invoking Camelot in stream mode to extract a table from the specified area.
6. Populating a QTableWidget with the extracted table data (as strings).
7. Emitting a signal containing the extracted DataFrame for downstream use.

Note: The table preview is strictly read-only – no editing is supported.
"""

from __future__ import annotations

from typing import Optional, Tuple

import camelot  # Library for PDF table extraction
import pandas as pd
import pymupdf as fitz  # PyMuPDF for rendering PDF pages
from pyproj import Transformer
from PySide6.QtCore import QEvent, QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem

from src.views.pdf_area.ui.pdf_window_ui import Ui_PDFWindow


# ==============================================================================
#  PdfAreaView: Rectangle-based PDF table extraction window
# ==============================================================================
class PdfAreaView(QMainWindow, Ui_PDFWindow):
    """
    Provides a UI for drawing a rectangle on a PDF page and extracting a table.

    The user can load a PDF, render a specified page at high resolution, draw
    a red rectangle over the desired table region, and invoke Camelot to extract
    that area. The extracted table appears in a read-only QTableWidget, and a
    pandas DataFrame is emitted via the extractionReady signal for downstream use.
    """

    # Emit a dict with key "df" and value = extracted DataFrame when extraction finishes
    extractionReady = Signal(dict)

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initializes the PdfAreaView.

        - Loads UI elements defined in Ui_PDFWindow.
        - Prepares internal state variables for PDF document, selection rectangle,
          and scene.
        - Configures the QGraphicsView to display PDF pages and capture mouse events.
        - Connects page navigation and extraction buttons to their handlers.
        """
        super().__init__()
        # Load UI layout from the generated class
        self.setupUi(self)

        # ---------------- Internal State Variables ----------------
        # Holds the opened PDF document via PyMuPDF; None if not loaded
        self._doc: Optional[fitz.Document] = None  # type: ignore[attr-defined]
        # File path of the currently loaded PDF; None if none loaded
        self._path: Optional[str] = None
        # Starting point of the rectangle in scene coordinates (x, y)
        self._start_pos: Optional[Tuple[float, float]] = None
        # QGraphicsRectItem representing the user-drawn rectangle; None if no rectangle
        self._rect_item = None

        # ---------------- Graphics Scene Setup ----------------
        # Create a QGraphicsScene to render PDF pages as pixelmaps
        self.scene = QGraphicsScene(self)
        # Attach the scene to the QGraphicsView defined in the UI (named pdfView)
        self.pdfView.setScene(self.scene)

        # Configure the QGraphicsView for better rendering and no default dragging
        self.pdfView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore[arg-type]
        self.pdfView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore[arg-type]
        self.pdfView.setRenderHint(QPainter.Antialiasing)  # type: ignore[arg-type]
        self.pdfView.setRenderHint(QPainter.SmoothPixmapTransform)  # type: ignore[arg-type]
        self.pdfView.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)  # type: ignore[arg-type]
        self.pdfView.setResizeAnchor(QGraphicsView.AnchorUnderMouse)  # type: ignore[arg-type]
        self.pdfView.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # type: ignore[arg-type]
        self.pdfView.setDragMode(QGraphicsView.NoDrag)  # type: ignore[arg-type]

        # Install this class as an event filter on the viewport to capture mouse events
        self.pdfView.viewport().installEventFilter(self)

        # ---------------- Table Widget Configuration ----------------
        # Make the tableWidget read-only by disabling any edit triggers
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore[attr‐defined]

        # ---------------- Splitter Configuration ----------------
        # Set the main splitter to divide the window 50/50 between PDF and table
        self.splitMain.setStretchFactor(0, 1)
        self.splitMain.setStretchFactor(1, 1)

        # ---------------- Connect Signals ----------------
        # When the page spin box value changes, call _on_page_changed to render that page
        self.spinPage.valueChanged.connect(self._on_page_changed)
        # When the 'Extract Table' button is clicked, call _on_extract to perform extraction
        self.btnExtract.clicked.connect(self._on_extract)

        # Override resizeEvent and showEvent to refresh PDF view on window changes
        self.resizeEvent = self._on_resize
        self.showEvent = self._on_show

    # ==============================================================================
    #  Resize and Show Event Handlers
    # ==============================================================================
    def _on_resize(self, event):
        """
        Handles the window resize event to re-render the current PDF page.

        When the window resizes, the PDF view must update so that the page fits
        the new size. If a PDF is loaded, calls _display_page for the current page.
        """
        super().resizeEvent(event)
        if self._doc:
            # Re-draw the current page at the new size
            self._display_page(self.spinPage.value())

    def _on_show(self, event):
        """
        Handles the window show event to render the current PDF page.

        When the window is shown (first display or re-show), ensure that the
        PDF page appears. If a PDF is loaded, call _display_page.
        """
        super().showEvent(event)
        if self._doc:
            self._display_page(self.spinPage.value())

    # ==============================================================================
    #  PDF Loading and Page Display
    # ==============================================================================
    def load_pdf(self, path: str) -> None:
        """
        Loads the specified PDF file and renders its first page.

        - Attempts to open the PDF using PyMuPDF.
        - On success, sets up the page spin box range and renders page 1.
        - On failure, shows a critical error message.
        """
        # Store the selected PDF file path
        self._path = path
        try:
            # Open the PDF document
            self._doc = fitz.open(path)  # type: ignore[attr-defined]
        except Exception as exc:
            # If opening fails, show an error dialog
            QMessageBox.critical(self, "Error", f"Could not open PDF:\n{exc}")
            return

        # Set spinPage range from 1 to number of pages
        self.spinPage.setRange(1, self._doc.page_count)
        # Default to page 1
        self.spinPage.setValue(1)
        # Render the first page
        self._display_page(1)

    def _display_page(self, page_number: int) -> None:
        """
        Renders a given page number of the loaded PDF into the QGraphicsScene.

        - Resets any existing selection rectangle.
        - Calculates a zoom factor so the page fits the view while maintaining aspect ratio.
        - Renders the page at that zoom level as a pixmap and displays it.
        - Clears previous scene items and fits the view to show the full page.
        """
        # If no document is loaded, do nothing
        if not self._doc:
            return

        # Reset selection rectangle state when changing pages
        self._start_pos = None
        if self._rect_item:
            self.scene.removeItem(self._rect_item)
            self._rect_item = None

        # PyMuPDF uses 0-based page indices
        page = self._doc.load_page(page_number - 1)

        # Get view dimensions to compute appropriate zoom
        view_size = self.pdfView.size()
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        # Compute ratios to fit the page in the view
        width_ratio = view_size.width() / page_width
        height_ratio = view_size.height() / page_height
        zoom = min(width_ratio, height_ratio)

        # Render the page with the calculated zoom factor
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))  # type: ignore[attr-defined]

        # Convert PyMuPDF pixmap to QPixmap via PNG bytes
        q_pixelmap = QPixmap()
        q_pixelmap.loadFromData(pix.tobytes(output="png"))

        # Clear any existing scene items and add the new page image
        self.scene.clear()
        self.scene.addPixmap(q_pixelmap)
        # Set scene rectangle to match the pixmap size
        self.scene.setSceneRect(q_pixelmap.rect())
        # Make the QGraphicsView fit the entire page while maintaining aspect ratio
        self.pdfView.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)  # type: ignore[arg-type]

    # ==============================================================================
    #  Mouse Event Filtering for Rectangle Drawing
    # ==============================================================================
    def eventFilter(self, watched, event) -> bool:
        """
        Captures mouse events on the PDF view viewport to draw a selection rectangle.

        - On left mouse press: record the starting scene coordinate and remove existing rectangle.
        - On mouse move while dragging: update or create a red rectangle item according to mouse position.
        - On left mouse release: finalize the rectangle and stop tracking movements.

        Returns True if the event is handled here; otherwise calls default handler.
        """
        # Only intercept events from the pdfView's viewport
        if watched is self.pdfView.viewport():
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:  # type: ignore[attr‐defined]
                # Record starting position in scene coordinates
                self._start_pos = self.pdfView.mapToScene(event.pos())  # type: ignore[attr‐defined]

                # Remove any existing rectangle so the user can draw a new one
                if self._rect_item:
                    self.scene.removeItem(self._rect_item)
                    self._rect_item = None

                # Return True to indicate the event is handled
                return True

            if event.type() == QEvent.MouseMove and self._start_pos:  # type: ignore[attr‐defined]
                # Map mouse position to scene coordinates
                end = self.pdfView.mapToScene(event.pos())  # type: ignore[attr‐defined]

                # Build a QRectF from start to current position, then normalize
                rect = QRectF(self._start_pos, end).normalized()  # type: ignore[attr‐defined]

                # Use a thick red pen for the rectangle outline
                pen = QPen(Qt.red, 2)  # type: ignore[attr‐defined]

                if self._rect_item is None:
                    # If no rectangle exists, add a new one to the scene
                    self._rect_item = self.scene.addRect(rect, pen)
                else:
                    # Otherwise update the existing rectangle's geometry
                    self._rect_item.setRect(rect)

                return True

            if event.type() == QEvent.MouseButtonRelease and self._rect_item:  # type: ignore[attr‐defined]
                # User finished drawing; stop tracking and finalize rectangle
                self._start_pos = None
                return True

        # For all other cases, delegate to the default event filter behavior
        return super().eventFilter(watched, event)

    # ==============================================================================
    #  Page Change Slot
    # ==============================================================================
    def _on_page_changed(self, page: int) -> None:
        """
        Responds to changes in the page spin box by displaying the selected page.

        Called when spinPage.valueChanged is emitted. If a PDF is loaded, calls
        _display_page to re-render the new page.
        """
        if self._doc:
            self._display_page(page)

    # ==============================================================================
    #  Table Extraction Logic with Camelot
    # ==============================================================================
    def _on_extract(self) -> None:
        """
        Performs table extraction over the drawn rectangle using Camelot.

        Steps:
        1. Verify that a selection rectangle exists and a PDF is loaded.
           If missing, show a warning and return.
        2. Compute rectangle bounds in PDF points:
           - Load current page and its high-zoom pixmap to get pixel width/height.
           - Retrieve scene's bounding rectangle matching the pixmap size.
           - Map the rectangle's scene coordinates to pixel coordinates.
           - Divide pixel coordinates by zoom factor to convert to PDF points.
           - Flip y-coordinates to account for origin differences between Qt and PDF.
        3. Format the area string "x1,y1,x2,y2" for Camelot.
        4. Call camelot.read_pdf with flavor='stream' and the computed area.
        5. If Camelot raises an exception, show a warning message and return.
        6. If no tables found, inform the user and return.
        7. Take first table from Camelot, convert to pandas DataFrame, reset index,
           and rename columns to simple string indices.
        8. Populate the QTableWidget with DataFrame contents via _fill_table.
        9. Emit extractionReady signal with {"df": df}.
        """
        # Ensure a rectangle exists, a path is set, and a document is loaded
        if not (self._rect_item and self._path and self._doc):
            QMessageBox.warning(self, "Selection missing", "Please draw a rectangle first.")
            return

        # 1) Load the current page (0-based index)
        page_index = self.spinPage.value() - 1
        page = self._doc.load_page(page_index)

        # 2) Use the same zoom factor as in _display_page (calibrated high zoom for accuracy)
        zoom = 10
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))  # type: ignore[attr-defined]
        width, height = pix.width, pix.height  # pixel dimensions of the rendered page

        # The scene's bounding rectangle corresponds to the pixmap's dimensions
        bbox_scene = self.scene.itemsBoundingRect()
        # The user-drawn rectangle in scene coordinates
        r = self._rect_item.rect()

        # Convert scene coordinates to pixel coordinates
        l_px = r.left() * (width / bbox_scene.width())
        t_px = r.top() * (height / bbox_scene.height())
        r_px = r.right() * (width / bbox_scene.width())
        b_px = r.bottom() * (height / bbox_scene.height())

        # Convert pixel coordinates to PDF points by dividing by zoom
        # PDF origin is bottom-left, so flip y-coordinates accordingly
        x1 = l_px / zoom
        x2 = r_px / zoom
        y1 = (height - b_px) / zoom
        y2 = (height - t_px) / zoom

        # Format the area string as "x1,y1,x2,y2"
        area_str = f"{x1},{y1},{x2},{y2}"

        # 3) Invoke Camelot to extract tables in the specified area
        try:
            tables = camelot.read_pdf(
                self._path,
                pages=str(self.spinPage.value()),
                flavor="stream",
                table_areas=[area_str],  # 1-based page number  # Stream mode is better for visually detected tables
            )
        except Exception as exc:
            # If Camelot fails, show a warning and abort
            QMessageBox.warning(self, "Extraction error", str(exc))
            return

        # If Camelot did not find any tables, inform the user
        if not tables:
            QMessageBox.information(self, "No table", "Nothing found in the selected area.")
            return

        # 4) Take the first table returned by Camelot
        df = tables[0].df.reset_index(drop=True)
        # Rename columns to simple string indices ("0", "1", ...)
        df.columns = [str(i) for i in range(df.shape[1])]

        # 5) Populate the QTableWidget with the extracted DataFrame
        self._fill_table(df)

        # 6) Emit the signal carrying the DataFrame for downstream use
        self.extractionReady.emit({"df": df})

    # ==============================================================================
    #  Populate QTableWidget with Extracted Data
    # ==============================================================================
    def _fill_table(self, df: pd.DataFrame) -> None:
        """
        Displays the extracted pandas DataFrame in the QTableWidget.

        - Clears any existing table contents.
        - Sets the column and row counts to match the DataFrame shape.
        - Iterates through each DataFrame cell, converts to string, and inserts
          as a QTableWidgetItem into the table.
        - Resizes columns to fit content for better readability.
        """
        # Clear any previous content
        self.tableWidget.clear()

        # Configure table dimensions
        self.tableWidget.setColumnCount(df.shape[1])
        self.tableWidget.setRowCount(df.shape[0])

        # Populate each cell with string representation
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[r, c]))
                self.tableWidget.setItem(r, c, item)

        # Adjust each column width to fit its contents
        self.tableWidget.resizeColumnsToContents()

    # ==============================================================================
    #  Helper: Reproject GeoJSON Coordinates (Not used here but included for reference)
    # ==============================================================================
    @staticmethod
    def _reproject_geojson(gj: dict, src_epsg: int, dst_epsg: int = 4326) -> dict:
        """
        Re-projects all coordinates in the input GeoJSON from src_epsg to dst_epsg.

        - Recursively traverses nested coordinate arrays.
        - Uses pyproj Transformer to convert each [lon, lat] pair.
        - Builds a new GeoJSON FeatureCollection with transformed geometries.
        """
        # Create a transformer for the desired coordinate reference systems
        tf = Transformer.from_crs(src_epsg, dst_epsg, always_xy=True)

        def _recurse(coordinates):
            # If coordinates represent a single point, transform it
            if isinstance(coordinates[0], (float, int)):
                lon, lat = tf.transform(coordinates[0], coordinates[1])
                return [lon, lat]
            # If nested (e.g., polygons), recurse deeper
            return [_recurse(c) for c in coordinates]

        # Build and return a new GeoJSON with reprojected features
        out = {"type": "FeatureCollection", "features": []}
        for feat in gj["features"]:
            new_feat = feat.copy()
            geom = feat["geometry"].copy()
            geom["coordinates"] = _recurse(geom["coordinates"])
            new_feat["geometry"] = geom
            out["features"].append(new_feat)
        return out

    # ==============================================================================
    #  Navigation Guard Methods
    # ==============================================================================
    def can_go_next(self) -> bool:
        """
        Prevents navigation to the next view until a table has been extracted.

        Returns True when the QTableWidget contains at least one row (i.e., extraction succeeded).
        """
        return self.tableWidget.rowCount() > 0

    # noinspection PyMethodMayBeStatic
    def can_go_back(self) -> bool:
        """
        Always allows navigation back from this view.

        Returns True unconditionally.
        """
        return True
