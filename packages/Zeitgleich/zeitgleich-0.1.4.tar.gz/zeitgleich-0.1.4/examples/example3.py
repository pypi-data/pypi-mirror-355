import pandas as pd
from datetime import timezone, timedelta
from Zeitgleich import TimestampFormat

# Single value conversion
timestamp_str = "2021-06-05T12:00:00.123456789Z"
converted_single = TimestampFormat.convert(
    timestamp_str,
    input_format=TimestampFormat.RFC3339,
    output_format=TimestampFormat.UNIX
)
print(converted_single)  # Output: 1622894400

# List conversion
timestamp_list = ["2021-06-05T12:00:00Z", "2021-06-06T12:00:00Z"]
converted_list = TimestampFormat.convert(
    timestamp_list,
    input_format=TimestampFormat.RFC3339,
    output_format=TimestampFormat.ISO
)
print(converted_list)
# Output: ['2021-06-05T12:00:00.000000', '2021-06-06T12:00:00.000000']

# Dictionary conversion
timestamp_dict = {
    'timestamp': "2021-06-05T12:00:00Z",
    'value': 100
}
converted_dict = TimestampFormat.convert(
    timestamp_dict,
    input_format=TimestampFormat.RFC3339,
    output_format=TimestampFormat.EPOCH_S
)
print(converted_dict)
# Output: {'timestamp': 1622894400.0, 'value': 100}

# DataFrame conversion with timezone handling
data = {
    'timestamp': ["2021-06-05T12:00:00Z", "2021-06-06T12:00:00Z"],
    'value': [100, 200]
}
df = pd.DataFrame(data)

converted_df = TimestampFormat.convert(
    data=df,
    input_format=TimestampFormat.RFC3339,
    output_format=TimestampFormat.ISO,
    timestamp_col='timestamp',
    input_timezone=timezone.utc,
    output_timezone=timezone(timedelta(hours=2))
)
print(converted_df)