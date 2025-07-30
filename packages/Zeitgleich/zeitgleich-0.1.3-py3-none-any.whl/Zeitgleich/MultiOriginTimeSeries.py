from typing import Dict, Optional, Union
import pandas as pd
from datetime import timezone, tzinfo

from .FormatChecks import DEFAULT_ORIGIN_REGEX, DEFAULT_VALUE_COLUMNS, check_origin_format
from .Origin import Origin
from .TimestampFormat import TimestampFormat
from .TimeSeriesData import TimeSeriesData

class MultiOriginTimeSeries:
    """
    A class to manage time series data from multiple origins,
    with direct or delegated checks for required columns & origin format.
    """

    def __init__(self,
                 output_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
                 output_timezone: Optional[tzinfo] = timezone.utc,
                 time_as_index: bool = True,
                 origin_regex: str = DEFAULT_ORIGIN_REGEX,
                 value_columns: Optional[list] = None,
                 extra_columns_handling: str = "append"):
        if value_columns is None:
            value_columns = DEFAULT_VALUE_COLUMNS

        self.origin_data_map: Dict[Origin, pd.DataFrame] = {}
        self.output_timestamp_format = output_timestamp_format
        self.output_timezone = output_timezone
        self.time_as_index = time_as_index
        self.origin_regex = origin_regex
        self.value_columns = value_columns
        self.extra_columns_handling = extra_columns_handling

    def add_data(self,
                 origin: Union[str, Origin],
                 data: Union[pd.DataFrame, dict],
                 input_timestamp_format: Optional[TimestampFormat] = None,
                 time_column: str = "timestamp",
                 input_timezone: Optional[tzinfo] = timezone.utc):
        """
        Adds data for a specific origin; we can rely on TimeSeriesData for checks.
        """
        # 1. Check the origin’s pattern:
        origin_str = str(origin)
        check_origin_format(origin_str, self.origin_regex)

        # 2. Create a TimeSeriesData instance for the single origin,
        #    letting it do the required columns check, etc.
        ts_data = TimeSeriesData(
            origin=origin_str,
            data=data,
            input_timestamp_format=input_timestamp_format,
            output_timestamp_format=self.output_timestamp_format,
            time_column=time_column,
            input_timezone=input_timezone,
            output_timezone=self.output_timezone,
            time_as_index=self.time_as_index,
            origin_regex=self.origin_regex,
            value_columns=self.value_columns,
            extra_columns_handling=self.extra_columns_handling
        )

        df_converted = ts_data.df
        origin_key = Origin(origin_str)
        if origin_key in self.origin_data_map:
            self.origin_data_map[origin_key] = pd.concat([self.origin_data_map[origin_key], df_converted])
            self.origin_data_map[origin_key].sort_index(inplace=True)
        else:
            self.origin_data_map[origin_key] = df_converted

    def get_data_by_origin(self, origin: Origin) -> pd.DataFrame:
        return self.origin_data_map[origin]

    def equals(self, other):
        if not isinstance(other, MultiOriginTimeSeries):
            return False
        return (self.origin_data_map.keys() == other.origin_data_map.keys() and
                all(self.origin_data_map[origin].equals(other.origin_data_map[origin]) 
                    for origin in self.origin_data_map))

    def _apply_operation(self, other, op, output_timestamp_format: TimestampFormat = None):
        if output_timestamp_format is None:
            output_timestamp_format = self.output_timestamp_format

        result = MultiOriginTimeSeries(
            output_timestamp_format=self.output_timestamp_format,
            output_timezone=self.output_timezone,
            time_as_index=self.time_as_index,
            origin_regex=self.origin_regex,
            value_columns=self.value_columns,
            extra_columns_handling=self.extra_columns_handling
        )

        if isinstance(other, MultiOriginTimeSeries):
            if set(self.origin_data_map.keys()) != set(other.origin_data_map.keys()):
                raise ValueError("Origins do not match between MultiOriginTimeSeries objects.")
            for origin in self.origin_data_map:
                df = self.origin_data_map[origin]
                other_df = other.origin_data_map[origin]
                result_df = op(df, other_df)
                result.add_data(
                    origin=origin,
                    data=result_df.reset_index(),
                    input_timestamp_format=output_timestamp_format
                )
        else:
            for origin, df in self.origin_data_map.items():
                result_df = op(df, other)
                result.add_data(
                    origin=origin,
                    data=result_df.reset_index(),
                    input_timestamp_format=output_timestamp_format
                )
        return result

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

    def __repr__(self):
        return (f"MultiOriginTimeSeries(\n"
                f"  output_timestamp_format={self.output_timestamp_format},\n"
                f"  output_timezone={self.output_timezone},\n"
                f"  timestamp_as_index={self.time_as_index},\n"
                f"  origin_data_map={self.origin_data_map}\n"
                f")")
