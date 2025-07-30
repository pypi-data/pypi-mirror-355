# test_timestamp_format.py

import unittest
import pandas as pd
from datetime import timezone, timedelta
import pytz  # Ensure pytz is installed: pip install pytz

# Adjust the import path based on your project structure
from Zeitgleich import TimestampFormat

class TestCurrentTimestamp(unittest.TestCase):

    def test_get_current_timestamp(self):
        # Get the current timestamp
        timestamp = TimestampFormat.get_current_timestamp() # defaults to RFC3339 format
        print(f"Current timestamp: {timestamp}")
        self.assertTrue(isinstance(timestamp, str))