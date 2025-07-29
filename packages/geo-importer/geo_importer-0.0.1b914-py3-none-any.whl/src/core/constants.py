"""Central collection of constants used across the application.

This file stores general numeric thresholds and small helper strings that are
used in multiple places. Keeping them here avoids scattering magic numbers
throughout the code base.
"""

# When a user clicks on a column in the GeoData or CSV filtering dialogs,
# up to this many unique values will be listed for selection.
MAX_UNIQUE_VALUES = 100

# Duration (in milliseconds) that a normal status message is shown.
STATUS_DURATION = 3000

# Duration (in milliseconds) that an error message is shown.
ERROR_DURATION = 5000

# Number of bytes to read from the start of a CSV file in order to detect
# the delimiter character.
SAMPLE_SIZE = 4096


EQUAL = " == "
NOT_EQUAL = " != "
LESS_THAN = " < "
GREATER_THAN = " > "
LOGICAL_AND = " and "
LOGICAL_OR = " or "
LIKE_OPERATOR = " like "
IN_OPERATOR = " in "
