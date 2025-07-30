# TimestampFormat.py

from enum import Enum
import pandas as pd
from typing import Union, Optional, Any, List, Dict
from datetime import timezone, tzinfo
import re
import numpy as np

class TimestampFormat(Enum):
    ISO = 'ISO'             # 'YYYY-MM-DDTHH:MM:SS[.ffffff]'
    RFC3339 = 'RFC3339'     # 'YYYY-MM-DDTHH:MM:SS[.ffffff]Z' or with timezone offset
    UNIX = 'UNIX'           # Integer seconds since epoch
    EPOCH_S = 'EPOCH_S'     # Float seconds since epoch
    EPOCH_NS = 'EPOCH_NS'   # Integer nanoseconds since epoch

    @staticmethod
    def detect(timestamp: Union[str, int, float]) -> Optional['TimestampFormat']:
        """
        Attempts to detect the timestamp format based on the input.

        :param timestamp: The timestamp to detect format for.
        :return: Detected TimestampFormat or None if detection fails.
        """
        if isinstance(timestamp, np.int64):
            timestamp = int(timestamp)
    
        if not isinstance(timestamp, (int, float, str)):
            return None

        if isinstance(timestamp, (int, float)):
            return TimestampFormat._detect_numeric_timestamp(timestamp)
        elif isinstance(timestamp, str):
            return TimestampFormat._detect_string_timestamp(timestamp)
        return None

    @staticmethod
    def _detect_numeric_timestamp(num_timestamp: Union[int, float]) -> Optional['TimestampFormat']:
        """
        Detects the numeric timestamp format.

        :param num_timestamp: Numeric timestamp.
        :return: Detected TimestampFormat or None if detection fails.
        """
        if isinstance(num_timestamp, int):
            if num_timestamp > 1e18:
                return TimestampFormat.EPOCH_NS
            elif num_timestamp > 1e9:
                return TimestampFormat.UNIX
        elif isinstance(num_timestamp, float):
            return TimestampFormat.EPOCH_S
        return None
    
    @staticmethod
    def _detect_string_timestamp(string_timestamp: str) -> Optional['TimestampFormat']:
        """
        Detects the string timestamp format.

        :param string_timestamp: String timestamp.
        :return: Detected TimestampFormat or None if detection fails.
        """
        

        # Check for ISO/RFC3339 formats using regex
        iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$"
        rfc3339_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$"
        if re.match(iso_regex, string_timestamp):
            return TimestampFormat.ISO
        elif re.match(rfc3339_regex, string_timestamp):
            return TimestampFormat.RFC3339
        # Check for numeric string timestamps
        try:
            num_timestamp = float(string_timestamp)
            return TimestampFormat._detect_numeric_timestamp(num_timestamp)
        except ValueError:
            return None

    @staticmethod
    def convert(
        data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]], Any],
        timestamp_col: str = 'timestamp',
        input_format: Optional['TimestampFormat'] = None,
        input_timezone: Optional[tzinfo] = timezone.utc,
        output_format: 'TimestampFormat' = 'RFC3339',
        output_timezone: Optional[tzinfo] = timezone.utc
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]], Any]:
        """
        Converts timestamp(s) from one format to another.

        :param data: Input data, can be DataFrame, dict, list, or single value.
        :param timestamp_col: Name of the timestamp field (for dicts and DataFrames).
        :param input_format: (Optional) Format of input timestamps. If None, detect automatically.
        :param input_timezone: Timezone of the input timestamps. Defaults to UTC.
        :param output_format: Desired output format. Defaults to RFC3339.
        :param output_timezone: Desired timezone for the output timestamps. Defaults to UTC.
        :return: Data with converted timestamp(s).
        """
        if isinstance(data, pd.DataFrame):
            if input_format is None:
                sample = data[timestamp_col].dropna().iloc[0] if not data[timestamp_col].dropna().empty else None
                if sample is not None:
                    detected_format = TimestampFormat.detect(sample)
                    if detected_format is not None:
                        input_format = detected_format
                    else:
                        raise ValueError("Cannot detect timestamp format from the DataFrame sample.")
                else:
                    raise ValueError("Cannot detect timestamp format from an empty DataFrame.")
            return TimestampFormat._convert_dataframe(
                data, input_format, output_format, timestamp_col, input_timezone, output_timezone
            )
        elif isinstance(data, dict):
            # Check if dict contains lists (multiple entries) or single entries
            if any(isinstance(v, list) for v in data.values()):
                # Convert dict of lists to DataFrame
                df = pd.DataFrame(data)
                if input_format is None:
                    sample = df[timestamp_col].dropna().iloc[0] if not df[timestamp_col].dropna().empty else None
                    if sample is not None:
                        detected_format = TimestampFormat.detect(sample)
                        if detected_format is not None:
                            input_format = detected_format
                        else:
                            raise ValueError("Cannot detect timestamp format from the dictionary sample.")
                    else:
                        raise ValueError("Cannot detect timestamp format from an empty dictionary.")
                df_converted = TimestampFormat._convert_dataframe(
                    df, input_format, output_format, timestamp_col, input_timezone, output_timezone
                )
                # Convert DataFrame back to dict of lists
                return df_converted.to_dict(orient='list')
            else:
                if input_format is None:
                    sample = data.get(timestamp_col)
                    if sample is not None:
                        detected_format = TimestampFormat.detect(sample)
                        if detected_format is not None:
                            input_format = detected_format
                        else:
                            raise ValueError("Cannot detect timestamp format from the dictionary sample.")
                    else:
                        raise ValueError("Cannot detect timestamp format as the timestamp key is missing.")
                return TimestampFormat._convert_dict(
                    data, input_format, output_format, timestamp_col, input_timezone, output_timezone
                )
        elif isinstance(data, list):
            if not data:
                raise ValueError("Cannot detect timestamp format from an empty list.")
            if input_format is None:
                sample = data[0].get(timestamp_col) if isinstance(data[0], dict) else data[0]
                detected_format = TimestampFormat.detect(sample)
                if detected_format is not None:
                    input_format = detected_format
                else:
                    raise ValueError("Cannot detect timestamp format from the list sample.")
            return [TimestampFormat.convert(
                item,
                timestamp_col=timestamp_col,
                input_format=input_format,
                input_timezone=input_timezone,
                output_format=output_format,
                output_timezone=output_timezone
            ) for item in data]
        else:
            if input_format is None:
                detected_format = TimestampFormat.detect(data)
                if detected_format is not None:
                    input_format = detected_format
                else:
                    raise ValueError("Cannot detect timestamp format from the single value.")
            return TimestampFormat._convert_single(
                data, input_format, output_format, input_timezone, output_timezone
            )
        
    @staticmethod
    def get_current_timestamp(format: 'TimestampFormat' = 'RFC3339', timezone: Optional[tzinfo] = timezone.utc) -> str:
        """
        Returns the current timestamp in the specified format.

        :param format: Desired output format. Defaults to RFC3339.
        :param timezone: Desired timezone for the output timestamp. Defaults to UTC.
        :return: Current timestamp as a string.
        """
        dt = pd.Timestamp.now(tz=timezone)
        return TimestampFormat._from_datetime(dt, format)

    @staticmethod
    def _truncate_fractional_seconds(timestamp_str: str) -> str:
        """
        Truncate the fractional seconds in a timestamp string to 6 digits.
        If there are more than 6, truncate to 6. If less or none, leave as is.
        """
        truncated = re.sub(r'(\.\d{6})\d+', r'\1', timestamp_str)
        return truncated

    @staticmethod
    def _convert_dataframe(
        df: pd.DataFrame,
        input_format: 'TimestampFormat',
        output_format: 'TimestampFormat',
        timestamp_col: str,
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> pd.DataFrame:
        """
        Converts the timestamp column of a DataFrame from the input format to the output format.

        :param df: Input DataFrame.
        :param input_format: Format of input timestamps.
        :param output_format: Desired output format.
        :param timestamp_col: Name of the timestamp column or index.
        :param input_timezone: Timezone of the input timestamps.
        :param output_timezone: Desired timezone for the output timestamps.
        :return: DataFrame with converted timestamps.
        """
        df = df.copy() # Avoid modifying the original DataFrame # TODO: Make this optional

        # Determine if timestamp is a column or index
        if timestamp_col in df.columns:
            timestamp_series = df[timestamp_col]

            # Apply truncation if necessary
            if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
                timestamp_series = timestamp_series.astype(str).apply(TimestampFormat._truncate_fractional_seconds)

            df[timestamp_col] = TimestampFormat._convert_series(
                timestamp_series, input_format, output_format, input_timezone, output_timezone
            )
        elif df.index.name == timestamp_col:
            timestamp_series = df.index.to_series()

            # Apply truncation if necessary
            if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
                timestamp_series = timestamp_series.astype(str).apply(TimestampFormat._truncate_fractional_seconds)

            converted_series = TimestampFormat._convert_series(
                timestamp_series, input_format, output_format, input_timezone, output_timezone
            )
            df.index = converted_series
        else:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found in DataFrame.")

        return df

    @staticmethod
    def _convert_dict(
        data: Dict[str, Any],
        input_format: 'TimestampFormat',
        output_format: 'TimestampFormat',
        timestamp_col: str,
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> Dict[str, Any]:
        """
        Converts the timestamp in a dictionary from the input format to the output format.

        :param data: Input dictionary.
        :param input_format: Format of input timestamp.
        :param output_format: Desired output format.
        :param timestamp_col: Name of the timestamp field.
        :param input_timezone: Timezone of the input timestamp.
        :param output_timezone: Desired timezone for the output timestamp.
        :return: Dictionary with converted timestamp.
        """
        if timestamp_col not in data:
            raise ValueError(f"Key '{timestamp_col}' not found in the dictionary.")

        data = data.copy()

        # Apply truncation if necessary
        if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339} and isinstance(data[timestamp_col], str):
            data[timestamp_col] = TimestampFormat._truncate_fractional_seconds(data[timestamp_col])

        data[timestamp_col] = TimestampFormat._convert_single(
            data[timestamp_col], input_format, output_format, input_timezone, output_timezone
        )
        return data

    @staticmethod
    def _convert_single(
        timestamp: Any,
        input_format: 'TimestampFormat',
        output_format: 'TimestampFormat',
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> Any:
        """
        Converts a single timestamp from the input format to the output format.

        :param timestamp: The timestamp to convert.
        :param input_format: Format of the input timestamp.
        :param output_format: Desired output format.
        :param input_timezone: Timezone of the input timestamp.
        :param output_timezone: Desired timezone for the output timestamp.
        :return: Converted timestamp.
        """
        try:
            # If input is ISO or RFC3339 and is a string, truncate fractional seconds
            if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339} and isinstance(timestamp, str):
                timestamp = TimestampFormat._truncate_fractional_seconds(timestamp)

            # Convert input timestamp to pandas datetime
            dt = TimestampFormat._to_datetime(timestamp, input_format, input_timezone, output_timezone)

            # Convert pandas datetime to desired output format
            return TimestampFormat._from_datetime(dt, output_format)
        except Exception as e:
            raise ValueError(f"Failed to convert timestamp '{timestamp}': {e}")

    @staticmethod
    def _convert_series(
        series: pd.Series,
        input_format: 'TimestampFormat',
        output_format: 'TimestampFormat',
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> pd.Series:
        """
        Converts a Pandas Series of timestamps from the input format to the output format.

        :param series: Pandas Series containing timestamps.
        :param input_format: Format of input timestamps.
        :param output_format: Desired output format.
        :param input_timezone: Timezone of the input timestamps.
        :param output_timezone: Desired timezone for the output timestamps.
        :return: Series with converted timestamps.
        """
        try:
            # Apply truncation if necessary
            if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
                series = series.astype(str).apply(TimestampFormat._truncate_fractional_seconds)

            # Convert input series to pandas datetime
            dt_series = TimestampFormat._to_datetime_series(
                series, input_format, input_timezone, output_timezone
            )

            # Convert pandas datetime series to desired output format
            if output_format == TimestampFormat.ISO:
                return dt_series.dt.strftime('%Y-%m-%dT%H:%M:%S.%f').astype('object')
            elif output_format == TimestampFormat.RFC3339:
                formatted = dt_series.dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
                # Replace '+0000' with 'Z' for UTC
                formatted = formatted.str.replace(r'\+0000$', 'Z', regex=True)
                return formatted
            elif output_format == TimestampFormat.UNIX:
                return (dt_series.astype('int64') // 10**9).astype('Int64')
            elif output_format == TimestampFormat.EPOCH_S:
                return (dt_series.astype('int64') / 10**9).astype(float)
            elif output_format == TimestampFormat.EPOCH_NS:
                return dt_series.astype('int64')
            else:
                raise ValueError(f"Unsupported output timestamp format: {output_format}")
        except Exception as e:
            raise ValueError(f"Failed to convert timestamp series: {e}")

    @staticmethod
    def _to_datetime(
        timestamp: Any,
        input_format: 'TimestampFormat',
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> pd.Timestamp:
        """
        Converts a single timestamp to pandas Timestamp.
        """

        try:
            
            if input_format == TimestampFormat.ISO:
                dt = pd.to_datetime(timestamp, format="%Y-%m-%dT%H:%M:%S.%f", utc=False, errors='raise')
            if input_format == TimestampFormat.RFC3339:
                timestamp = timestamp.replace('Z', '+00:00')
                
                dt = pd.to_datetime(timestamp, format="%Y-%m-%dT%H:%M:%S.%f%z", utc=False, errors='raise')
            #! missing format triggers _guess_datetime_format_for_array and _array_strptime_with_fallback, leading to 100% cpu
            # if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
            #     dt = pd.to_datetime(timestamp, utc=False, errors='raise')
            if input_format in {TimestampFormat.UNIX, TimestampFormat.EPOCH_S}:
                dt = pd.to_datetime(timestamp, unit='s', utc=False, errors='raise')
            if input_format == TimestampFormat.EPOCH_NS:
                dt = pd.to_datetime(timestamp, unit='ns', utc=False, errors='raise')
        except Exception as err:  
            raise ValueError(f"Error during timestamp conversion: {str(err)} with input timestamp format: {input_format} and timestamp: {timestamp} of datattype {type(timestamp)}")

        # Localize if timestamp is naive
        if dt.tzinfo is None:
            if input_timezone is None:
                input_timezone = timezone.utc  # Default to UTC if not specified
            dt = dt.replace(tzinfo=input_timezone)
            
        # Convert to output timezone
        if output_timezone is not None:
            dt = dt.astimezone(output_timezone)
        else:
            dt = dt.astimezone(timezone.utc)  # Default to UTC if output_timezone is None

        return pd.Timestamp(dt)

    @staticmethod
    def _to_datetime_series(
        series: pd.Series,
        input_format: 'TimestampFormat',
        input_timezone: Optional[tzinfo],
        output_timezone: Optional[tzinfo]
    ) -> pd.Series:
        """
        Converts a Pandas Series of timestamps to pandas datetime.

        :param series: Pandas Series containing timestamps.
        :param input_format: Format of input timestamps.
        :param input_timezone: Timezone of the input timestamps.
        :param output_timezone: Desired timezone for the output timestamps.
        :return: Series with pandas datetime.
        """
        if input_format is None:
            # Detect format based on a sample
            sample = series.dropna().iloc[0] if not series.dropna().empty else None
            if sample is not None:
                input_format = TimestampFormat.detect(sample)
                if input_format is None:
                    raise ValueError(f"Could not detect timestamp format for sample '{sample}'.")
            else:
                raise ValueError("Cannot detect timestamp format from an empty series.")

        try:
            
            if input_format == TimestampFormat.ISO:
                dt_series = pd.to_datetime(series, format="%Y-%m-%dT%H:%M:%S.%f", utc=False, errors='raise')
            if input_format == TimestampFormat.RFC3339:
                series = series.str.replace("Z", "+00:00")
                dt_series = pd.to_datetime(series, format="%Y-%m-%dT%H:%M:%S.%f%z", utc=False, errors='raise')
            #! missing format triggers _guess_datetime_format_for_array and _array_strptime_with_fallback, leading to 100% cpu
            # if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
            #     dt = pd.to_datetime(timestamp, utc=False, errors='raise')
            if input_format in {TimestampFormat.UNIX, TimestampFormat.EPOCH_S}:
                dt_series = pd.to_datetime(series, unit='s', utc=False, errors='raise')
            if input_format == TimestampFormat.EPOCH_NS:
                dt_series = pd.to_datetime(series, unit='ns', utc=False, errors='raise')
        except Exception as err:  
            raise ValueError(f"Error during timestamp conversion: {str(err)} with input timestamp format: {input_format} and series: {series}")


        #! Replaced above
        # # Parse the series without setting UTC to allow timezone localization
        # if input_format in {TimestampFormat.ISO, TimestampFormat.RFC3339}:
        #     dt_series = pd.to_datetime(series, utc=False, errors='raise')
        # elif input_format in {TimestampFormat.UNIX, TimestampFormat.EPOCH_S}:
        #     dt_series = pd.to_datetime(series, unit='s', utc=False, errors='raise')
        # elif input_format == TimestampFormat.EPOCH_NS:
        #     dt_series = pd.to_datetime(series, unit='ns', utc=False, errors='raise')
        # else:
        #     raise ValueError(f"Unsupported input timestamp format: {input_format}")

        
        
        # Localize if timestamps are naive
        if dt_series.dt.tz is None or not dt_series.dt.tz:
            if input_timezone is None:
                input_timezone = timezone.utc  # Default to UTC if not specified
            dt_series = dt_series.dt.tz_localize(input_timezone, ambiguous='raise', nonexistent='raise')

        # Convert to output timezone
        if output_timezone is not None:
            dt_series = dt_series.dt.tz_convert(output_timezone)
        else:
            dt_series = dt_series.dt.tz_convert(timezone.utc)  # Default to UTC if output_timezone is None

        # Check for any NaT values resulting from invalid conversions
        if dt_series.isnull().any():
            invalid_values = series[dt_series.isnull()]
            raise ValueError(f"Failed to convert timestamps: {invalid_values.tolist()}")

        return dt_series

    @staticmethod
    def _from_datetime(
        dt: pd.Timestamp,
        output_format: 'TimestampFormat'
    ) -> Any:
        """
        Converts pandas Timestamp to the desired output format.

        :param dt: pandas Timestamp.
        :param output_format: Desired output format.
        :return: Converted timestamp.
        """
        if type(output_format) is str:
            output_format = TimestampFormat(output_format)
            
        if output_format == TimestampFormat.ISO:
            return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
        elif output_format == TimestampFormat.RFC3339:
            formatted = dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
            # Replace '+0000' with 'Z' for UTC
            if formatted.endswith('+0000'):
                formatted = formatted[:-5] + 'Z'
            return formatted
        elif output_format == TimestampFormat.UNIX:
            return int(dt.timestamp())
        elif output_format == TimestampFormat.EPOCH_S:
            return dt.timestamp()
        elif output_format == TimestampFormat.EPOCH_NS:
            return dt.value
        else:
            raise ValueError(f"Unsupported output timestamp format: {output_format}")
