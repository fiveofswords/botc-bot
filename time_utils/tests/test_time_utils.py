from datetime import datetime, timezone, timedelta
from unittest import TestCase, mock
from time_utils.time_utils import parse_deadline, _convert_to_timedelta, _round_datetime_to_nearest_half_hour


class TestParseDeadline(TestCase):

    def setUp(self):
        patcher = mock.patch('time_utils.time_utils.datetime', autospec=True)
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

    def test_relative_time_rounds_up_to_nearest_half_hour(self):
        # Set up a real datetime object for comparison
        real_datetime_now = datetime(1988, 5, 20, 16, 46, tzinfo=timezone.utc)
        # Configure the mock to return a real datetime object for now() with timezone.utc
        self.mock_datetime.now.return_value = real_datetime_now

        input_deadline = "+2h30m"
        expected = datetime(1988, 5, 20, 19, 30, tzinfo=timezone.utc)
        actual = parse_deadline(input_deadline)

        self.assertEqual(expected, actual, "The parsed deadline does not match the expected value.")

    def test_relative_time_rounds_down_to_nearest_half_hour(self):
        # Set up a real datetime object for comparison
        real_datetime_now = datetime(1988, 5, 20, 17, 10, tzinfo=timezone.utc)
        # Configure the mock to return a real datetime object for now() with timezone.utc
        self.mock_datetime.now.return_value = real_datetime_now

        input_deadline = "+2h30m"
        expected = datetime(1988, 5, 20, 19, 30, tzinfo=timezone.utc)
        actual = parse_deadline(input_deadline)

        self.assertEqual(expected, actual, "The parsed deadline does not match the expected value.")

    def test_invalid_string_returns_none(self):
        input_deadline = "1223"
        self.assertIsNone(parse_deadline(input_deadline))


class TestConvertToTimeDelta(TestCase):
    def test_accepts_only_hours(self):
        input_deadline = "+2h"
        self.assertEqual(_convert_to_timedelta(input_deadline), timedelta(hours=2, minutes=0))

    def test_accepts_only_minute(self):
        input_deadline = "+30m"
        self.assertEqual(_convert_to_timedelta(input_deadline), timedelta(hours=0, minutes=30))

    def test_accepts_hours_and_minutes(self):
        input_deadline = "+3h30m"
        self.assertEqual(_convert_to_timedelta(input_deadline), timedelta(hours=3, minutes=30))

    def test_accepts_decimal(self):
        input_deadline = "+3.5h"
        self.assertEqual(_convert_to_timedelta(input_deadline), timedelta(hours=3, minutes=30))

    def test_missing_prefix_returns_none(self):
        input_deadline = "2h"
        self.assertIsNone(_convert_to_timedelta(input_deadline))

    def test_just_plus_returns_none(self):
        input_deadline = "+"
        self.assertIsNone(_convert_to_timedelta(input_deadline))

    def test_invalid_input_without_h_or_m_returns_none(self):
        input_deadline = "+dk3"
        self.assertIsNone(_convert_to_timedelta(input_deadline))

    def test_invalid_input_with_h_or_m_returns_none(self):
        input_deadline = "+3kh"
        self.assertIsNone(_convert_to_timedelta(input_deadline))


class TestRoundDatetimeToHalfHour(TestCase):
    def test_rounds_up_to_hour(self):
        input_datetime = datetime(1988, 5, 20, 16, 46, tzinfo=timezone.utc)
        expected = datetime(1988, 5, 20, 17, 0, tzinfo=timezone.utc)
        self.assertEqual(_round_datetime_to_nearest_half_hour(input_datetime), expected)

    def test_rounds_down_to_hour(self):
        input_datetime = datetime(1988, 5, 20, 16, 13, tzinfo=timezone.utc)
        expected = datetime(1988, 5, 20, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(_round_datetime_to_nearest_half_hour(input_datetime), expected)

    def test_rounds_up_to_half_hour(self):
        input_datetime = datetime(1988, 5, 20, 16, 25, tzinfo=timezone.utc)
        expected = datetime(1988, 5, 20, 16, 30, tzinfo=timezone.utc)
        self.assertEqual(_round_datetime_to_nearest_half_hour(input_datetime), expected)

    def test_rounds_down_to_half_hour(self):
        input_datetime = datetime(1988, 5, 20, 16, 37, tzinfo=timezone.utc)
        expected = datetime(1988, 5, 20, 16, 30, tzinfo=timezone.utc)
        self.assertEqual(_round_datetime_to_nearest_half_hour(input_datetime), expected)


if __name__ == '__main__':
    import unittest

    unittest.main()
