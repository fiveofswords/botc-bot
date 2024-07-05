from datetime import datetime, timezone
from unittest import TestCase, mock
from time_utils import parse_deadline


class TestParseDeadline(TestCase):

    def setUp(self):
        patcher = mock.patch('time_utils.datetime', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_datetime = patcher.start()

        # Ensure strptime and fromtimestamp methods work as expected
        self.mock_datetime.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)
        self.mock_datetime.fromtimestamp.side_effect = lambda *args, **kwargs: datetime.fromtimestamp(*args, **kwargs)
        self.mock_datetime.combine.side_effect = lambda date, time, tzinfo: datetime.combine(date, time).replace(
            tzinfo=tzinfo)

    def test_time_in_future_sets_same_day(self):
        # Set up a real datetime object for comparison
        real_datetime_now = datetime(1988, 5, 20, 16, 46, tzinfo=timezone.utc)
        # Configure the mock to return a real datetime object for now() with timezone.utc
        self.mock_datetime.now.return_value = real_datetime_now

        input_deadline = "18:00"
        expected = datetime(1988, 5, 20, 18, 0, tzinfo=timezone.utc)
        actual = parse_deadline(input_deadline)

        self.assertEqual(expected, actual, "The parsed deadline does not match the expected value.")

    def test_time_in_past_sets_next_day(self):
        # Set up a real datetime object for comparison
        real_datetime_now = datetime(1988, 5, 20, 23, 46, tzinfo=timezone.utc)
        # Configure the mock to return a real datetime object for now() with timezone.utc
        self.mock_datetime.now.return_value = real_datetime_now

        input_deadline = "01:00"
        expected = datetime(1988, 5, 21, 1, 0, tzinfo=timezone.utc)
        actual = parse_deadline(input_deadline)

        self.assertEqual(expected, actual, "The parsed deadline does not match the expected value.")

    def test_unix_timestamp(self):
        input_deadline = "580149960"
        expected = datetime(1988, 5, 20, 16, 46, tzinfo=timezone.utc)
        actual = parse_deadline(input_deadline)

        self.assertEqual(expected, actual, "The parsed deadline does not match the expected value.")

    def test_relative_time_raises_error_since_not_yet_implemented(self):
        input_deadline = "+2h30m"
        with self.assertRaises(ValueError):
            parse_deadline(input_deadline)

    def test_invalid_string_raises_error(self):
        input_deadline = "1223"
        with self.assertRaises(ValueError):
            parse_deadline(input_deadline)


if __name__ == '__main__':
    import unittest

    unittest.main()
