from datetime import timezone
from Zeitgleich import MultiOriginTimeSeries, TimestampFormat, Origin

# Initialize MultiOriginTimeSeries with default settings
# You can customize the settings by passing different values to the constructor
multi_ts = MultiOriginTimeSeries(
    output_timestamp_format=TimestampFormat.RFC3339,  # Optional: Defaults to RFC3339
    output_timezone=timezone.utc,                     # Optional: Defaults to UTC
    time_as_index=True                           # Optional: Defaults to True
)

# Sample DataFrames with different timestamp formats
data1 = {
    'timestamp': [1622894400, 1622980800],  # Unix epoch times
    'value': [10, 20]
}
data2 = {
    'timestamp': ["2021-06-05T12:00:00Z", "2021-06-06T12:00:00Z"],  # RFC3339 format
    'value': [30, 40]
}

# Define origins
origin1 = Origin("device1/sensor1")
origin2 = Origin("device2/sensor2")

# Add time series data for multiple origins with specified input timestamp formats
# Note: `output_timestamp_format` is no longer passed here
multi_ts.add_data(
    origin=origin1,
    data=data1,
    input_timestamp_format=TimestampFormat.UNIX
)

multi_ts.add_data(
    origin=origin2,
    data=data2,
    input_timestamp_format=TimestampFormat.RFC3339
)

print(multi_ts)

# Perform Pandas operations on each origin's data
mean_origin1 = multi_ts.get_data_by_origin(origin1)['value'].mean()
mean_origin2 = multi_ts.get_data_by_origin(origin2)['value'].mean()

print(mean_origin1)  # Expected Output: 15.0
print(mean_origin2)  # Expected Output: 35.0
