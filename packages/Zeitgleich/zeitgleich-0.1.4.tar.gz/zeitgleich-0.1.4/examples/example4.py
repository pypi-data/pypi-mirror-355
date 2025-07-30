from Zeitgleich import TimeSeriesData, TimestampFormat, Origin
import pandas as pd

# Incorrect origin format
try:
    invalid_origin = Origin("device1-sensor1")  # Should be "device1/sensor1"
    data = {
        'timestamp': ["2021-06-05T12:00:00Z"],
        'value': [100]
    }
    df = pd.DataFrame(data)
    ts_data = TimeSeriesData(
        origin=invalid_origin,
        data=df,
        input_timestamp_format=TimestampFormat.RFC3339
    )
except ValueError as e:
    print(e)  # Output: Origin 'device1-sensor1' does not match expected format '.+/.+'.

# Missing data column
try:
    valid_origin = Origin("device1/sensor1")
    incomplete_data = {
        'time': ["2021-06-05T12:00:00Z"],  # Should be 'timestamp'
        'value': [100]
    }
    df_incomplete = pd.DataFrame(incomplete_data)
    ts_data = TimeSeriesData(
        origin=valid_origin,
        data=df_incomplete,
        input_timestamp_format=TimestampFormat.RFC3339
    )
except ValueError as e:
    print(e)  # Output: Column 'timestamp' not found in DataFrame.
