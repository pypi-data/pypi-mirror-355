from typing import Union, Optional
import pandas as pd
from datetime import timezone, tzinfo

from .FormatChecks import DEFAULT_ORIGIN_REGEX, DEFAULT_VALUE_COLUMNS, check_origin_format, check_required_columns
from .Origin import Origin
from .TimestampFormat import TimestampFormat

class TimeSeriesData:
    """
    A class to manage time series data from a single origin, performing direct validation
    of the origin string and required columns in the constructor.
    """

    def __init__(self,
                 origin: Union[Origin, str],
                 data: Union[pd.DataFrame, dict],
                 input_timestamp_format: Optional[TimestampFormat] = None,
                 output_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
                 time_column: str = 'timestamp',
                 input_timezone: Optional[tzinfo] = timezone.utc,
                 output_timezone: Optional[tzinfo] = timezone.utc,
                 time_as_index: bool = True,
                 origin_regex: str = DEFAULT_ORIGIN_REGEX,
                 value_columns: Optional[list] = None,
                 extra_columns_handling: str = "append"):
        """
        :param origin: The origin of the data, e.g. "device1/sensor1"
        :param data: A pandas DataFrame or dict with time series data.
        :param input_timestamp_format: The format of the input timestamps (e.g. TimestampFormat.ISO).
        :param output_timestamp_format: The desired output format (e.g. TimestampFormat.RFC3339).
        :param time_column: Name of the timestamp column in `data`. Default is "timestamp".
        :param input_timezone: Timezone of input timestamps (default UTC).
        :param output_timezone: Desired output timezone (default UTC).
        :param time_as_index: Whether to set the time column as the DataFrame index.
        :param origin_regex: Regex pattern to validate `origin`. Default is r".+/.+".
        :param value_columns: List of data columns (e.g. ["value", "status"]). Defaults to ["value"].
        :param extra_columns_handling: "ignore", "error", or "append" for columns outside the required set.

        By default, the "required set" = {time_column} + (value_columns or ["value"]).
        """
        # 1. Validate the origin format
        origin_str = str(origin)
        check_origin_format(origin_str, origin_regex)

        # 2. Decide data columns
        if value_columns is None:
            value_columns = DEFAULT_VALUE_COLUMNS  # e.g. ["value"]

        self.time_column = time_column
        self.required_columns = [time_column] + value_columns

        # 3. Validate extra_columns_handling
        if extra_columns_handling not in ["ignore", "error", "append"]:
            raise ValueError(
                "extra_columns_handling must be one of: 'ignore', 'error', 'append'."
            )
        self.extra_columns_handling = extra_columns_handling

        # 4. Convert data to DataFrame if needed
        if isinstance(data, dict):
            if not data:
                raise ValueError("Data dictionary must not be empty.")
            
            #? Maybe as optional config choosing between:
                # 1. keep dict as json in df
                # 2. flatten nested dict as individual columns in df
                
            # wrap any nested dicts into lists in order to keep it as json in df, otherwise NaN
            data = {
                key: [value] if isinstance(value, dict) else value
                for key, value in data.items()
            }
            
            # Decide if single-row or multiple-row
            # Unused
            first_value = next(iter(data.values()))
            
            #! need to wrap dict into list.
            #! by occasion wrapped dict could be the first_value => false positive for mutirow
            #! checking all instances of value being lists removes false positive
            multirow = all(isinstance(value, list) for value in data.values())
            
            if multirow:
                self.df = pd.DataFrame(data)
            else:
                self.df = pd.DataFrame(data, index=[0])
        elif isinstance(data, pd.DataFrame):
            self.df = data.copy(deep=True)
        else:
            raise TypeError(f"Expected a DataFrame or dict, got {type(data)}.")

        # 5. Check required columns exist
        check_required_columns(self.df, self.required_columns)

        # 6. Possibly handle extra columns
        actual_cols = set(self.df.columns)
        required_set = set(self.required_columns)
        extras = actual_cols - required_set
        if extras:
            if self.extra_columns_handling == "ignore":
                self.df = self.df[self.required_columns]
            elif self.extra_columns_handling == "error":
                raise ValueError(
                    f"Extra columns {extras} present but extra_columns_handling='error'."
                )
            # if "append", do nothing

        # 7. Convert timestamps
        self.df = TimestampFormat.convert(
            data=self.df,
            timestamp_col=time_column,
            input_format=input_timestamp_format,
            input_timezone=input_timezone,
            output_format=output_timestamp_format,
            output_timezone=output_timezone
        )

        # 8. Possibly set as index
        if time_as_index:
            self.df.set_index(time_column, inplace=True)

        # 9. Store rest
        self.origin = Origin(origin)
        self.output_timestamp_format = output_timestamp_format
        self.output_timezone = output_timezone
        self.time_as_index = time_as_index

    def __len__(self):
        return len(self.df)

    def __repr__(self):
        return f"Origin: {self.origin}, Data:\n{self.df}"

    def mean(self):
        return self.df.mean()

    def equals(self, other):
        if not isinstance(other, TimeSeriesData):
            return False
        return self.origin == other.origin and self.df.equals(other.df)
    
    def get_first_timestamp(self):
        """Returns the first timestamp in the time column, or None if empty."""
        if len(self.df) == 0:
            return None
        if self.time_as_index:
            return self.df.index[0]
        return self.df[self.time_column].iloc[0]

    def _apply_operation(self, other, op, output_timestamp_format: TimestampFormat = None):
        """Applies a binary operation to the time series data."""
        if output_timestamp_format is None:
            output_timestamp_format = self.output_timestamp_format

        if isinstance(other, TimeSeriesData):
            if self.origin != other.origin:
                raise ValueError("Cannot perform operation on TimeSeriesData with different origins.")
            result_df = op(self.df, other.df)
        else:
            result_df = op(self.df, other)

        result_df = result_df.reset_index()

        return TimeSeriesData(
            origin=self.origin,
            data=result_df,
            input_timestamp_format=output_timestamp_format,
            output_timestamp_format=output_timestamp_format,
            timestamp_col=self.timestamp_col,
            input_timezone=self.output_timezone,
            output_timezone=self.output_timezone,
            timestamp_as_index=self.timestamp_as_index,
            default_expected_origin_format=self.default_expected_origin_format,
            default_expected_data_columns=self.default_expected_data_columns,
            extra_columns_handling=self.extra_columns_handling
        )

    def __add__(self, other):
        import operator
        return self._apply_operation(other, operator.add)

    def __sub__(self, other):
        import operator
        return self._apply_operation(other, operator.sub)

    def __mul__(self, other):
        import operator
        return self._apply_operation(other, operator.mul)

    def __truediv__(self, other):
        import operator
        return self._apply_operation(other, operator.truediv)

    def __floordiv__(self, other):
        import operator
        return self._apply_operation(other, operator.floordiv)

    def __mod__(self, other):
        import operator
        return self._apply_operation(other, operator.mod)

    def __pow__(self, other):
        import operator
        return self._apply_operation(other, operator.pow)

    def __getitem__(self, key):
        subset_df = self.df[key]
        subset_df = subset_df.reset_index()
        return TimeSeriesData(
            origin=self.origin,
            data=subset_df,
            input_timestamp_format=self.output_timestamp_format,
            output_timestamp_format=self.output_timestamp_format,
            timestamp_col=self.timestamp_col,
            input_timezone=self.output_timezone,
            output_timezone=self.output_timezone,
            timestamp_as_index=self.timestamp_as_index,
            default_expected_origin_format=self.default_expected_origin_format,
            default_expected_data_columns=self.default_expected_data_columns,
            extra_columns_handling=self.extra_columns_handling
        )
