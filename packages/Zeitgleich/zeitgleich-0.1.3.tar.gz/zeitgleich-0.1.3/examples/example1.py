from Zeitgleich import TimeSeriesData, TimestampFormat, Origin

data = {
    'timestamp': ["2021-06-06T12:00:00.654321"],
    'value': [10]
}

ts_data = TimeSeriesData(
    origin=Origin("device1/sensor1"),
    data=data,
    input_timestamp_format=TimestampFormat.ISO,
    output_timestamp_format=TimestampFormat.EPOCH_NS # How it should be formatted within the data object
)

print(ts_data.df.head())            # View time series data with RFC3339 timestamps
print(ts_data.origin.get_device())  # Output: device1
print(ts_data.origin.get_topic())   # Output: sensor1
