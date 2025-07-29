"""Definitions related to the workflow steps of the import wizard.

The :class:`Step` enumeration lists every page in the sequence and the
``TITLE`` mapping assigns a short name used for the sidebar and navigation.
"""

from enum import Enum


# ================================================================== #
#  Workflow steps enumeration
# ================================================================== #
class Step(Enum):
    """
    Enumerates all logical steps of the import wizard.

    The order of members defines the sequence in which the steps appear.
    """

    UPLOAD, PDF, WORKSHEET, DATAPREP, FILTER, GEODATA, MAPPING, MANUAL, PREVIEW, EXPORT = range(10)


# ================================================================== #
#  Human-readable titles for each wizard step
# ================================================================== #
TITLE = {
    # Step.UPLOAD: First step where the user uploads a file
    Step.UPLOAD: "1 • Upload",
    # Step.PDF: Second step for selecting an area in a PDF (if applicable)
    Step.PDF: "2 • PDF area",
    # Step.WORKSHEET: Second step for choosing a worksheet from an Excel file
    Step.WORKSHEET: "2 • Worksheet",
    # Step.DATAPREP: Third step for cleaning and preparing the data
    Step.DATAPREP: "3 • Data preparation",
    # Step.FILTER: Fourth step for selecting relevant columns and applying row filters
    Step.FILTER: "4 • Columns & filter",
    # Step.GEODATA: Fifth step for choosing and filtering geographic CSV files
    Step.GEODATA: "5 • Geo filter",
    # Step.MAPPING: Sixth step for automatically mapping statistics to geo data
    Step.MAPPING: "6 • Mapping",
    # Step.MANUAL: Seventh step for manually mapping any remaining unmatched rows
    Step.MANUAL: "7 • Manual mapping",
    # Step.PREVIEW: Eighth step for previewing the joined data on a map
    Step.PREVIEW: "8 • Preview",
    # Step.EXPORT: Ninth (and final) step for exporting the prepared data
    Step.EXPORT: "9 • Export",
}
