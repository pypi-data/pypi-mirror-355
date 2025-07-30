# FormatChecks.py

import re
import pandas as pd
from typing import Union, List, Optional, Dict

# Library-level defaults (if the user/class doesn’t override them)
DEFAULT_ORIGIN_REGEX = r".+/.+"     # e.g. "device1/sensorA"
DEFAULT_VALUE_COLUMNS = ["value"]   # minimal default for data columns

def check_origin_format(origin: str, pattern: str = DEFAULT_ORIGIN_REGEX) -> None:
    """
    Checks if `origin` matches the given regex `pattern`.
    Raises ValueError if not.
    """
    if not re.match(pattern, origin):
        raise ValueError(f"Origin '{origin}' does not match expected regex '{pattern}'.")

def check_required_columns(
    data: Union[pd.DataFrame, Dict[str, list]],
    required_columns: List[str]
) -> None:
    """
    Ensures that all columns in `required_columns` exist within the DataFrame or dictionary.
    Raises ValueError if a required column is missing.
    """
    if isinstance(data, pd.DataFrame):
        if data.empty:
            raise ValueError("DataFrame is empty; cannot validate required columns.")
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Required column '{col}' not found in DataFrame.")
    elif isinstance(data, dict):
        # Check if it's dict-of-lists or dict-of-singles.
        # If we assume dict-of-lists for multiple rows:
        if not data:
            raise ValueError("Data dictionary is empty; cannot validate required columns.")
        for col in required_columns:
            if col not in data:
                raise ValueError(f"Required column '{col}' not found in dictionary.")
    else:
        raise ValueError(f"Expected a pandas DataFrame or a dict, got {type(data)}.")
