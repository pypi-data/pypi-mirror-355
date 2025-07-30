# test_timestamp_format.py

import unittest
import pandas as pd
from datetime import timezone, timedelta
import pytz  # Ensure pytz is installed: pip install pytz

# Adjust the import path based on your project structure
from Zeitgleich import TimestampFormat

class TestTimestampFormatConversions(unittest.TestCase):
    """Unit tests for the TimestampFormat class conversions."""

    def setUp(self):
        """Set up sample timestamps for testing."""
        self.sample_timestamps = {
            TimestampFormat.ISO: "2021-06-05T12:00:00.123456",
            TimestampFormat.RFC3339: "2021-06-05T12:00:00.123456Z",
            TimestampFormat.UNIX: 1622894400,                  # 2021-06-05 12:00:00 UTC
            TimestampFormat.EPOCH_S: 1622894400.123456,        # 2021-06-05 12:00:00.123456 UTC
            TimestampFormat.EPOCH_NS: 1622894400123456000       # 2021-06-05 12:00:00.123456 UTC
        }

    # 1. Single Timestamp Conversions
    def test_single_iso_to_rfc3339(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456Z"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_iso_to_unix(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.UNIX
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_iso_to_epoch_s(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_S
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400.123456
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertAlmostEqual(converted, expected, places=6)

    def test_single_iso_to_epoch_ns(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_NS
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400123456000
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_rfc3339_to_iso(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.ISO
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_rfc3339_to_unix(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.UNIX
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_rfc3339_to_epoch_s(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_S
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400.123456
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertAlmostEqual(converted, expected, places=6)

    def test_single_rfc3339_to_epoch_ns(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_NS
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400123456000
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_unix_to_iso(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.ISO
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.000000"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_unix_to_rfc3339(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.RFC3339
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.000000Z"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_unix_to_epoch_s(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_S
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400.0
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_unix_to_epoch_ns(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_NS
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400000000000
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_s_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.ISO
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_s_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.RFC3339
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456Z"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_s_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.UNIX
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_s_to_epoch_ns(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.EPOCH_NS
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400123456000
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        # Allow a difference of 1 nanosecond due to floating point precision
        self.assertTrue(abs(converted - expected) <= 1, 
                        "Difference of 1 nanosecond allowed due to floating point precision.")

    def test_single_epoch_ns_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.ISO
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_ns_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.RFC3339
        timestamp = self.sample_timestamps[input_fmt]
        expected = "2021-06-05T12:00:00.123456Z"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_ns_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.UNIX
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_single_epoch_ns_to_epoch_s(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.EPOCH_S
        timestamp = self.sample_timestamps[input_fmt]
        expected = 1622894400.123456
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertAlmostEqual(converted, expected, places=6)

    # 2. List of Timestamps Conversions
    def test_list_iso_to_rfc3339(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456"
        ]
        expected = [
            "2021-06-05T12:00:00.123456Z",
            "2021-06-05T13:00:00.123456Z"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_iso_to_unix(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.UNIX
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456"
        ]
        expected = [
            1622894400,
            1622898000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_iso_to_epoch_s(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_S
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456"
        ]
        expected = [
            1622894400.123456,
            1622898000.123456
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        for c, e in zip(converted, expected):
            self.assertAlmostEqual(c, e, places=6)

    def test_list_iso_to_epoch_ns(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_NS
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456"
        ]
        expected = [
            1622894400123456000,
            1622898000123456000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_rfc3339_to_iso(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.ISO
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456Z"
        ]
        expected = [
            "2021-06-05T12:00:00.123456",
            "2021-06-05T13:00:00.123456"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_rfc3339_to_unix(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.UNIX
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456Z"
        ]
        expected = [
            1622894400,
            1622898000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_rfc3339_to_epoch_s(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_S
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456Z"
        ]
        expected = [
            1622894400.123456,
            1622898000.123456
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        for c, e in zip(converted, expected):
            self.assertAlmostEqual(c, e, places=6)

    def test_list_rfc3339_to_epoch_ns(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_NS
        timestamps = [
            self.sample_timestamps[input_fmt],
            "2021-06-05T13:00:00.123456Z"
        ]
        expected = [
            1622894400123456000,
            1622898000123456000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_unix_to_iso(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.ISO
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000  # UNIX timestamp for 13:00:00
        ]
        expected = [
            "2021-06-05T12:00:00.000000",
            "2021-06-05T13:00:00.000000"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_unix_to_rfc3339(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.RFC3339
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000  # UNIX timestamp for 13:00:00
        ]
        expected = [
            "2021-06-05T12:00:00.000000Z",
            "2021-06-05T13:00:00.000000Z"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_unix_to_epoch_s(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_S
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000  # UNIX timestamp for 13:00:00
        ]
        expected = [
            1622894400.0,
            1622898000.0
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_unix_to_epoch_ns(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_NS
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000  # UNIX timestamp for 13:00:00
        ]
        expected = [
            1622894400000000000,
            1622898000000000000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_s_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.ISO
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000.123456  # EPOCH_S for 13:00:00.123456
        ]
        expected = [
            "2021-06-05T12:00:00.123456",
            "2021-06-05T13:00:00.123456"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_s_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.RFC3339
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000.123456  # EPOCH_S for 13:00:00.123456
        ]
        expected = [
            "2021-06-05T12:00:00.123456Z",
            "2021-06-05T13:00:00.123456Z"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_s_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.UNIX
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000.123456  # EPOCH_S for 13:00:00.123456
        ]
        expected = [
            1622894400,
            1622898000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_s_to_epoch_ns(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.EPOCH_NS
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000.123456  # EPOCH_S for 13:00:00.123456
        ]
        expected = [
            1622894400123456000,
            1622898000123456000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        # Allow a difference of 1 nanosecond due to floating point precision
        for idx, (c, e) in enumerate(zip(converted, expected)):
            self.assertTrue(abs(c - e) <= 1, 
                            f"Difference of 1 nanosecond allowed due to floating point precision at index {idx}.")

    def test_list_epoch_ns_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.ISO
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000123456000  # EPOCH_NS for 13:00:00.123456
        ]
        expected = [
            "2021-06-05T12:00:00.123456",
            "2021-06-05T13:00:00.123456"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_ns_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.RFC3339
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000123456000  # EPOCH_NS for 13:00:00.123456
        ]
        expected = [
            "2021-06-05T12:00:00.123456Z",
            "2021-06-05T13:00:00.123456Z"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_ns_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.UNIX
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000123456000  # EPOCH_NS for 13:00:00.123456
        ]
        expected = [
            1622894400,
            1622898000
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted, expected)

    def test_list_epoch_ns_to_epoch_s(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.EPOCH_S
        timestamps = [
            self.sample_timestamps[input_fmt],
            1622898000123456000  # EPOCH_NS for 13:00:00.123456
        ]
        expected = [
            1622894400.123456,
            1622898000.123456
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        for c, e in zip(converted, expected):
            self.assertAlmostEqual(c, e, places=6)

    # 3. DataFrame Conversion Tests
    def test_dataframe_iso_to_rfc3339(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456Z",
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_iso_to_unix(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.UNIX
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456"
            ],
            'value': [100, 200]
        })
        # Define expected DataFrame with 'Int64' dtype to match converted DataFrame
        expected = pd.DataFrame({
            'timestamp': pd.Series([1622894400, 1622898000], dtype='Int64'),
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_iso_to_epoch_s(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_S
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400.123456,
                1622898000.123456
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_iso_to_epoch_ns(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.EPOCH_NS
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400123456000,
                1622898000123456000
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_rfc3339_to_iso(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.ISO
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456",
                "2021-06-05T13:00:00.123456"
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_rfc3339_to_unix(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.UNIX
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [100, 200]
        })
        # Define expected DataFrame with 'Int64' dtype to match converted DataFrame
        expected = pd.DataFrame({
            'timestamp': pd.Series([1622894400, 1622898000], dtype='Int64'),
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_rfc3339_to_epoch_s(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_S
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400.123456,
                1622898000.123456
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_rfc3339_to_epoch_ns(self):
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.EPOCH_NS
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [100, 200]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400123456000,
                1622898000123456000
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_unix_to_iso(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.ISO
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000  # UNIX timestamp for 13:00:00
            ],
            'value': [150, 250]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.000000",
                "2021-06-05T13:00:00.000000"
            ],
            'value': [150, 250]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_unix_to_rfc3339(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.RFC3339
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000  # UNIX timestamp for 13:00:00
            ],
            'value': [150, 250]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.000000Z",
                "2021-06-05T13:00:00.000000Z"
            ],
            'value': [150, 250]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_unix_to_epoch_s(self):
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_S
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000  # UNIX timestamp for 13:00:00
            ],
            'value': [150, 250]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400.0,
                1622898000.0
            ],
            'value': [150, 250]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        self.assertEqual(converted.equals(expected), True)

    def test_dataframe_unix_to_epoch_ns(self):
        """Test converting a DataFrame from UNIX to EPOCH_NS format."""
        input_fmt = TimestampFormat.UNIX
        output_fmt = TimestampFormat.EPOCH_NS
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000  # UNIX timestamp for 13:00:00 UTC
            ],
            'value': [150, 250]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400000000000,
                1622898000000000000
            ],
            'value': [150, 250]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_s_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.ISO
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000.123456  # EPOCH_S for 13:00:00.123456
            ],
            'value': [120, 220]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456",
                "2021-06-05T13:00:00.123456"
            ],
            'value': [120, 220]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_s_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.RFC3339
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000.123456  # EPOCH_S for 13:00:00.123456
            ],
            'value': [120, 220]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456Z",
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [120, 220]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_s_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.UNIX
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000.123456  # EPOCH_S for 13:00:00.123456
            ],
            'value': [120, 220]
        })
        # Define expected DataFrame with 'Int64' dtype to match converted DataFrame
        expected = pd.DataFrame({
            'timestamp': pd.Series([1622894400, 1622898000], dtype='Int64'),
            'value': [120, 220]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_s_to_epoch_ns(self):
        input_fmt = TimestampFormat.EPOCH_S
        output_fmt = TimestampFormat.EPOCH_NS
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000.123456  # EPOCH_S for 13:00:00.123456
            ],
            'value': [120, 220]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400123456000,
                1622898000123456000
            ],
            'value': [120, 220]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        # Allow a difference of 1 nanosecond due to floating point precision
        for idx, (c, e) in enumerate(zip(converted['timestamp'], expected['timestamp'])):
            self.assertTrue(abs(c - e) <= 1, 
                            f"Difference of 1 nanosecond allowed due to floating point precision at index {idx}.")

    def test_dataframe_epoch_ns_to_iso(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.ISO
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000123456000  # EPOCH_NS for 13:00:00.123456
            ],
            'value': [130, 230]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456",
                "2021-06-05T13:00:00.123456"
            ],
            'value': [130, 230]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_ns_to_rfc3339(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.RFC3339
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000123456000  # EPOCH_NS for 13:00:00.123456
            ],
            'value': [130, 230]
        })
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456Z",
                "2021-06-05T13:00:00.123456Z"
            ],
            'value': [130, 230]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_ns_to_unix(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.UNIX
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000123456000  # EPOCH_NS for 13:00:00.123456
            ],
            'value': [130, 230]
        })
        # Define expected DataFrame with 'Int64' dtype to match converted DataFrame
        expected = pd.DataFrame({
            'timestamp': pd.Series([1622894400, 1622898000], dtype='Int64'),
            'value': [130, 230]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_dataframe_epoch_ns_to_epoch_s(self):
        input_fmt = TimestampFormat.EPOCH_NS
        output_fmt = TimestampFormat.EPOCH_S
        df_input = pd.DataFrame({
            'timestamp': [
                self.sample_timestamps[input_fmt],
                1622898000123456000  # EPOCH_NS for 13:00:00.123456
            ],
            'value': [130, 230]
        })
        expected = pd.DataFrame({
            'timestamp': [
                1622894400.123456,
                1622898000.123456
            ],
            'value': [130, 230]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            output_format=output_fmt
        )
        pd.testing.assert_frame_equal(converted, expected)

    # 4. Detection Method Test
    def test_detect_format(self):
        """Test the detection of timestamp formats."""
        test_cases = [
            # Valid Formats
            ("2021-06-05T12:00:00.123456", TimestampFormat.ISO),
            ("2021-06-05T12:00:00.123456Z", TimestampFormat.RFC3339),
            (1622894400, TimestampFormat.UNIX),
            (1622894400.123456, TimestampFormat.EPOCH_S),
            (1622894400123456000, TimestampFormat.EPOCH_NS),
            # Invalid Formats
            ("2021/06/05 12:00:00", None),
            ("not a timestamp", None),
            (None, None),
            ([], None),
            ({}, None),
            (True, None),
            ("2021-06-05T12:00:00", TimestampFormat.ISO),           # ISO without microseconds
            ("2021-06-05T12:00:00.1234567", TimestampFormat.ISO),   # ISO with excessive precision
            (1622894400.1234567, TimestampFormat.EPOCH_S),          # EPOCH_S with excessive precision
        ]

        for timestamp, expected_format in test_cases:
            with self.subTest(timestamp=timestamp):
                detected_format = TimestampFormat.detect(timestamp)
                if expected_format is not None:
                    self.assertEqual(
                        detected_format, 
                        expected_format,
                        f"Failed to detect format for timestamp: {timestamp}"
                    )
                else:
                    self.assertIsNone(
                        detected_format, 
                        f"Expected None for timestamp: {timestamp}, but detected format {detected_format}"
                    )

    # 5. Timezone Conversion Tests
    def test_single_iso_to_rfc3339_with_timezones(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        timestamp = "2021-06-05T12:00:00.123456"
        input_timezone = pytz.timezone('US/Eastern')
        output_timezone = pytz.timezone('Asia/Tokyo')
        # US/Eastern is UTC-4 on 2021-06-05
        # Asia/Tokyo is UTC+9
        # 12:00 US/Eastern = 16:00 UTC = 25:00 Asia/Tokyo (next day 01:00)
        expected = "2021-06-06T01:00:00.123456Z"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        # Since RFC3339 expects 'Z' for UTC, but we converted to Asia/Tokyo,
        # it's better to adjust expected accordingly
        # However, in the implementation, 'Z' is appended if UTC
        # So if output_timezone is not UTC, it should have the offset
        # Adjust expected accordingly
        expected = "2021-06-06T01:00:00.123456+0900"
        self.assertEqual(converted, expected)

    def test_list_iso_to_rfc3339_with_timezones(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        timestamps = [
            "2021-06-05T12:00:00.123456",
            "2021-06-05T13:00:00.654321"
        ]
        input_timezone = pytz.timezone('Europe/London')  # UTC+1 on 2021-06-05 (BST)
        output_timezone = pytz.timezone('America/New_York')  # UTC-4 on 2021-06-05 (EDT)
        # London to New York: UTC+1 to UTC-4, so subtract 5 hours
        expected = [
            "2021-06-05T07:00:00.123456-0400",
            "2021-06-05T08:00:00.654321-0400"
        ]
        converted = TimestampFormat.convert(
            data=timestamps,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_dataframe_iso_to_rfc3339_with_timezones(self):
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        df_input = pd.DataFrame({
            'timestamp': [
                "2021-06-05T12:00:00.123456",
                "2021-06-05T13:00:00.654321"
            ],
            'value': [100, 200]
        })
        input_timezone = pytz.timezone('Europe/London')  # UTC+1 on 2021-06-05 (BST)
        output_timezone = pytz.timezone('Asia/Kolkata')  # UTC+5:30
        # London to Kolkata: UTC+1 to UTC+5:30, add 4:30
        expected = pd.DataFrame({
            'timestamp': [
                "2021-06-05T16:30:00.123456+0530",
                "2021-06-05T17:30:00.654321+0530"
            ],
            'value': [100, 200]
        })
        converted = TimestampFormat.convert(
            data=df_input,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        pd.testing.assert_frame_equal(converted, expected)

    def test_single_iso_with_input_output_timezone(self):
        """Test single timestamp conversion with different input and output timezones."""
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.ISO
        timestamp = "2021-06-05T12:00:00.000000"
        input_timezone = pytz.timezone('UTC')
        output_timezone = pytz.timezone('US/Eastern')  # UTC-4 on 2021-06-05
        expected = "2021-06-05T08:00:00.000000"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_invalid_timestamp_conversion(self):
        """Test that invalid timestamp conversions raise errors."""
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.UNIX
        invalid_timestamp = "invalid_timestamp"

        with self.assertRaises(ValueError):
            TimestampFormat.convert(
                data=invalid_timestamp,
                timestamp_col='timestamp',
                input_format=input_fmt,
                output_format=output_fmt
            )

    def test_timestamp_truncation(self):
        """Test that truncating timestamps longer than 6 decimal places works as expected."""
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.ISO
        timestamp = "2021-06-05T12:00:00.1234567"
        input_timezone = pytz.timezone('UTC')
        output_timezone = pytz.timezone('US/Eastern')
        expected = "2021-06-05T08:00:00.123456"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_timezone_naive_to_aware(self):
        """Test converting a naive timestamp to an aware timestamp."""
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.RFC3339
        timestamp = "2021-06-05T12:00:00.000000"
        input_timezone = None  # Let the convert method default to UTC
        output_timezone = pytz.timezone('Europe/London')  # UTC+1 on 2021-06-05

        expected = "2021-06-05T13:00:00.000000+0100"
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_timezone_aware_to_naive(self):
        """Test converting an aware timestamp to a naive timestamp."""
        # Since the implementation does not support naive outputs, expect the timestamp to remain aware
        input_fmt = TimestampFormat.RFC3339
        output_fmt = TimestampFormat.ISO
        timestamp = "2021-06-05T12:00:00.000000Z"  # UTC
        input_timezone = pytz.UTC
        output_timezone = None  # Defaults to UTC

        expected = "2021-06-05T12:00:00.000000"  # Still aware in UTC, represented without offset

        # Modify the implementation to handle output_timezone=None as UTC without altering the format
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_truncation_timezone(self):
        """Test converting string timestamps to different formats."""
        input_fmt = TimestampFormat.ISO
        output_fmt = TimestampFormat.ISO
        timestamp = "2025-01-20T10:48:25.9588349+01:00"  # UTC+01:00
        input_timezone = None  # Let the method detect timezone from the timestamp
        output_timezone = None  # Defaults to UTC

        expected = "2025-01-20T09:48:25.958834"  # UTC

        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)

    def test_decimal_places(self):
        """Test converting timestamps with different decimal places."""
        input_fmt = None
        output_fmt = TimestampFormat.ISO
        timestamp = "2024-09-24T07:34:17.965Z"
        input_timezone = None
        output_timezone = None

        expected = "2024-09-24T07:34:17.965000"
        
        converted = TimestampFormat.convert(
            data=timestamp,
            timestamp_col='timestamp',
            input_format=input_fmt,
            input_timezone=input_timezone,
            output_format=output_fmt,
            output_timezone=output_timezone
        )
        self.assertEqual(converted, expected)


if __name__ == '__main__':
    unittest.main()
