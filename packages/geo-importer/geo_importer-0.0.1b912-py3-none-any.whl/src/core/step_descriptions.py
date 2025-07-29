from src.core.steps import Step

STEP_DESCRIPTIONS: dict[Step, tuple[str, str]] = {
    Step.UPLOAD: (
        """
        <h4>Step 1: Upload or Select File</h4>
        <p>
          Here you can upload your statistics file. Select the file type
          (<b>Excel</b> (.xlsx/.xls), <b>CSV</b> (.csv), or <b>PDF</b> (.pdf)),
          click <b>Browse…</b> to choose your file, and then click <b>Next</b>
          once the upload completes.
        </p>
        """,
        """
        <h3>More about Step 1</h3>
        <p>
          In this initial step you bring your raw data into the system:
        </p>
        <ul>
          <li><b>Excel</b> (<code>.xlsx</code>, <code>.xls</code>): Workbooks with multiple sheets.</li>
          <li><b>CSV</b> (<code>.csv</code>): Plain-text tables with comma separation.</li>
          <li><b>PDF</b> (<code>.pdf</code>): Scanned or embedded tables.</li>
        </ul>
        <p>
          <b>How it works:</b>
        </p>
        <ol>
          <li>Choose the file type from the dropdown.</li>
          <li>Click <b>Browse…</b> to open your file browser.</li>
          <li>Select your file and wait until the application confirms the upload.</li>
          <li>Once you see the file name listed, click <b>Next</b> to continue.</li>
        </ol>
        """,
    ),
    Step.PDF: (
        """
        <h4>Step 2: Select Table Region (PDF)</h4>
        <p>
          Here you select the area in your PDF that contains the table.
          Choose the page, drag to draw a red box around the table,
          click <b>Extract Table</b>, and then click <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 2 (PDF)</h3>
        <p>
          PDF documents don’t inherently mark table boundaries, so you need to:
        </p>
        <ol>
          <li>Select the correct page number in the <b>Page</b> dropdown.</li>
          <li>Click and hold your mouse, then drag to draw a red rectangle around the entire table area.</li>
          <li>Release the mouse button, then click <b>Extract Table</b>.</li>
        </ol>
        <p>
          The system displays the extracted table on the right. <b>Important:</b> At this stage, the table does 
          not need perfect formatting—only ensure that all rows and columns appear. You will clean and format the 
          data in the next step.
        </p>
        <p>
          When you see all values correctly extracted, click <b>Next</b> to enter the DataPrep view.
        </p>
        """,
    ),
    Step.WORKSHEET: (
        """
        <h4>Step 2: Choose Worksheet (Excel)</h4>
        <p>
          Here you use the <b>Worksheet</b> dropdown to select the sheet
          containing your data. Verify the preview, then click <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 2 (Excel)</h3>
        <p>
          Excel workbooks often contain multiple sheets. In this step:
        </p>
        <ol>
          <li>Open the <b>Worksheet</b> dropdown to list all sheets.</li>
          <li>Click the sheet name that holds your data.</li>
          <li>Observe the live preview to confirm columns and headers.</li>
          <li>If it’s correct, click <b>Next</b> to load it into DataPrep.</li>
        </ol>
        """,
    ),
    Step.DATAPREP: (
        """
        <h4>Step 3: Clean & Prepare Table (<i>DataPrep</i>)</h4>
        <p>
          In this step, prepare your table so you have one or more geodata
          columns, statistic columns, and clear headers in the first row.
          You can transpose, undo/redo up to five steps, or export your table.
          When ready, click <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 3</h3>
        <p>
          DataPrep helps you transform raw tables into analysis-ready data:
        </p>
        <ul>
          <li><b>Cell Selection:</b> Click for single cells, Shift-click for ranges, ⌘-click for multiple non‐adjacent cells.</li>
          <li><b>Cut/Copy/Paste:</b> Right-click to cut (⌘+X), copy (⌘+C), or paste (⌘+V). Layouts must match exactly.</li>
          <li><b>Menu Selections:</b> Highlight every nth row/column, shift selections, and combine via OR/AND modes.</li>
          <li><b>Row/Column Ops:</b> Right-click headers to insert or delete entire rows or columns.</li>
          <li><b>Transpose:</b> Switch rows and columns when data is oriented incorrectly.</li>
          <li><b>Undo/Redo:</b> Step backward or forward through up to five recent edits.</li>
          <li><b>Export:</b> Save your current table as CSV or Excel to merge multi‐page PDF data manually.</li>
        </ul>
        <p>
          Before you click <b>Next</b>, ensure the first row contains headers for each column. 
          If any header is missing, a popup will prompt you to ignore (not recommended), auto-generate, or manually enter the missing names.
        </p>
        """,
    ),
    Step.FILTER: (
        """
        <h4>Step 4: Select Columns & Apply Filters</h4>
        <p>
          Here you filter your statistics and choose which columns to keep.
          Double-click a column or value to add it to your filter query, test
          with <b>Test/Preview</b>, then click <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 4</h3>
        <p>
          In the filtering step you refine which data passes to mapping:
        </p>
        <ol>
          <li><b>Select Columns:</b> Tick the checkboxes for each field you want in the output.</li>
          <li><b>Build Filter Query:</b>
            <ul>
              <li>Double-click a column heading to list its unique values.</li>
              <li>Double-click a value to insert a condition (e.g., <code>Country == "DE"</code>).</li>
              <li>Use the AND/OR buttons to combine multiple conditions.</li>
            </ul>
          </li>
          <li><b>Test/Preview:</b> Click to view the filtered table and verify your logic.</li>
          <li>When the results look correct, click <b>Next</b> to continue.</li>
        </ol>
        """,
    ),
    Step.GEODATA: (
        """
        <h4>Step 5: Apply GeoCSV Filters</h4>
        <p>
          Here you load and filter geographic data. Choose <b>Type</b>
          (e.g., NUTS, LAU), <b>Version</b> (e.g., NUTS 2024), and
          <b>Level</b> (e.g., NUTS-3), click <b>Load</b>, then refine with
          column selection and filters before clicking <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 5</h3>
        <p>
          Here you bring in and narrow down geographic reference data:
        </p>
        <ol>
          <li><b>Select Source:</b>
            <ul>
              <li><b>Type:</b> Geographic schema (NUTS, LAU, etc.).</li>
              <li><b>Version:</b> Year or edition (e.g., NUTS 2024).</li>
              <li><b>Level:</b> Granularity (e.g., NUTS-3 for small regions).</li>
            </ul>
          </li>
          <li>Click <b>Load</b> to import the chosen geodata.</li>
          <li><b>Filter/Select Columns:</b>
            <ul>
              <li>Use <b>Select Columns</b> to pick only needed fields.</li>
              <li>Open the <b>Filter/Query Builder</b> to add row conditions:</li>
              <ul>
                <li>Double-click a column to list values.</li>
                <li>Double-click a value or use AND/OR buttons to build queries (e.g., <code>CNTR_CODE == 'DE'</code>).</li>
              </ul>
            </ul>
          </li>
          <li>Click <b>Test/Preview</b> to check the filtered geodata.</li>
          <li>When satisfied, click <b>Next</b>.</li>
        </ol>
        """,
    ),
    Step.MAPPING: (
        """
        <h4>Step 6: Prepare Automatic Mapping</h4>
        <p>
          Here you match your statistics records to geographic regions.
          Add matchers (Unique, Prefix, Fuzzy, Regex) in order, click
          <b>Start Mapping</b>, and review the Mapped and Unmapped tables.
          Click <b>Next</b> when ready.
        </p>
        """,
        """
        <h3>More about Step 6</h3>
        <p>
          Automatic mapping attempts to link each statistic entry to a region:
        </p>
        <ol>
          <li>Click <b>+ Add Matcher</b> to insert a new rule. Matchers run in the order added.</li>
          <li>Choose from:
            <ul>
              <li><b>Unique:</b> Exact one-to-one matches only.</li>
              <li><b>Prefix:</b> Compare the first n characters.</li>
              <li><b>Fuzzy:</b> Use RapidFuzz to score similarity (set a threshold).</li>
              <li><b>Regex:</b> Match via custom regular expressions.</li>
            </ul>
          </li>
          <li>After configuring all matchers, click <b>Start Mapping</b>.</li>
          <li>
            The lower panel shows four tables:
            <ul>
              <li><b>Mapped:</b> Successfully matched pairs.</li>
              <li><b>Unmapped:</b> Stats entries without matches.</li>
              <li><b>Geo-Data:</b> All geographic entries.</li>
              <li><b>Statistics:</b> All statistic entries.</li>
            </ul>
          </li>
          <li>You can inspect which entries matched and which did not. Perfect mapping is not required—you’ll fix leftovers next.</li>
          <li>When most entries look good, click <b>Next</b>.</li>
        </ol>
        """,
    ),
    Step.MANUAL: (
        """
        <h4>Step 7: Confirm or Adjust Manual Mappings</h4>
        <p>
          Here you fix any wrong matches or map missing entries by hand.
          Select rows in <b>Mapped</b> or <b>Unmapped</b> and use
          <b>Unmap Selection</b> or <b>Map Manually</b>, then click
          <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 7</h3>
        <p>
          Finalize your mapping manually:
        </p>
        <ul>
          <li>
            In the <b>Mapped</b> table, check any incorrectly matched rows
            and click <b>Unmap Selection</b> to release them.
          </li>
          <li>
            In the <b>Unmapped</b> table, select exactly one row from each
            of the Statistics and Geo-Data tables, then click <b>Map Manually</b>
            to link them.
          </li>
        </ul>
        <p>
          Repeat until all entries are correctly paired. Once done,
          click <b>Next</b>.
        </p>
        """,
    ),
    Step.PREVIEW: (
        """
        <h4>Step 8: Preview Map (Folium)</h4>
        <p>
          Here you visualize your mapped data on an interactive map.
          Load your GeoJSON file, choose Geo-ID and Stats-ID columns,
          select the display value, and click <b>Show Map</b>. Then
          click <b>Next</b>.
        </p>
        """,
        """
        <h3>More about Step 8</h3>
        <p>
          Before exporting, verify your results on a map:
        </p>
        <ol>
          <li>Upload a <b>GeoJSON</b> file via the file browser.</li>
          <li>Select the <b>Geo-ID Column</b> (region identifier) and the <b>Stats-ID Column</b> (data identifier).</li>
          <li>Choose the <b>Display Value</b> from your statistics for coloring.</li>
          <li>Click <b>Show Map</b>:
            <ul>
              <li>Numerical values use a gradient color scale.</li>
              <li>Categorical values assign distinct colors per category.</li>
            </ul>
          </li>
        </ol>
        <p>
          Pan, zoom, and click markers to inspect details.
          If something looks off, you can go back to mapping steps.
          Otherwise, click <b>Next</b>.
        </p>
        """,
    ),
    Step.EXPORT: (
        """
        <h4>Step 9: Export Your Final Data</h4>
        <p>
          Here you export your results as a .zip archive containing
          a CSV of IDs and values plus a YAML metadata file.
          Select ID and Value columns, fill in metadata, and click
          <b>Export as Zip</b>.
        </p>
        """,
        """
        <h3>More about Step 9</h3>
        <p>
          In the final step, package your cleaned and mapped data:
        </p>
        <ol>
          <li>
            Choose the <b>ID Column</b> (from Geo-Data) and the <b>Value Column</b>
            (from Statistics) that link your records.
          </li>
          <li>
            Fill in the metadata fields:
            <ul>
              <li><b>Name:</b> A human-readable title.</li>
              <li><b>Description:</b> What the dataset represents.</li>
              <li><b>Source:</b> Data origin or citation.</li>
              <li><b>Year:</b> The reference year for the statistics.</li>
              <li><b>Type:</b> Indicator, Index, or Other.</li>
            </ul>
          </li>
          <li>
            Click <b>Export as Zip</b>. The download will include:
            <ul>
              <li>A CSV file with paired IDs and values.</li>
              <li>A YAML file containing your metadata.</li>
            </ul>
          </li>
        </ol>
        <p>
          Your .zip archive is now ready for sharing or further analysis.
        </p>
        """,
    ),
}
