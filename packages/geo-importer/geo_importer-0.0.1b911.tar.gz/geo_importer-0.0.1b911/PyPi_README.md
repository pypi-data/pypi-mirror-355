<p align="center">
  <img src="https://raw.githubusercontent.com/frievoe97/geo-importer/main/src/app_icon_long.png" alt="App Icon" width="600" />
</p>

# Geo-Importer

Geo-Importer is a lightweight desktop application built with PySide6 for importing, cleaning and georeferencing statistical tables.

---

## Installation

Install from PyPI:

```bash
pip install geo-importer
````

---

## Quick Start

Launch the application:

```bash
geo-importer
```

Or from Python:

```python
import geo_importer
geo_importer.main()
```

Then:

1. Upload your Excel, CSV or PDF file
2. Select table region (PDF) or worksheet (Excel)
3. Clean and prepare columns in the DataPrep view
4. Filter which statistics to include
5. Load and filter geodata (choose type, version, level)
6. Automatically map statistics to regions (exact, prefix, fuzzy, regex)
7. Manually adjust any unmatched records
8. Preview on an interactive Folium map
9. Export your matched data as CSV or GeoJSON

---

## Features

* Multi-format support: Excel (.xls/.xlsx), CSV, PDF
* Interactive table cleaning with transpose, undo/redo, cut/copy/paste
* Flexible automatic matching: exact, prefix, fuzzy (RapidFuzz), regex
* Built-in geodata: NUTS (0–3), LAU, LOR — select version and level
* Live preview on a Folium map (gradient or categorical coloring)
* One-click export to CSV or GeoJSON

---

## Documentation

Full documentation is available at:
[https://frievoe97.github.io/geo-importer/latest/](https://frievoe97.github.io/geo-importer/latest/)

---

## License

Distributed under the MIT License. See the [LICENSE](https://github.com/frievoe97/geo-importer/blob/main/LICENSE) file for details.