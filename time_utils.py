from datetime import datetime, timezone, timedelta
from typing import Optional


def parse_deadline(deadline_string: str) -> datetime:
    """

    :param deadline_string: The string to parse into a deadline to be set.
     Can be in the format 'HH:MM' for a time today, or a Unix timestamp for an epoch time.
    :return: A datetime object representing the deadline to be set.
    """
    now = datetime.now(timezone.utc)
    deadline = _parse_deadline_from_utc(deadline_string, now)
    if deadline is None:
        deadline = _parse_deadline_from_epoch_timestamp(deadline_string)
        if deadline is None:
            raise ValueError(
                "Time format not recognized. If in doubt, use 'HH:MM' in UTC")
    return deadline


def _parse_deadline_from_utc(deadline_string: str, now: datetime) -> Optional[datetime]:
    try:
        deadline = (datetime.strptime(deadline_string, "%H:%M")
                    .replace(year=now.year, month=now.month, day=now.day,
                             tzinfo=timezone.utc))
        if deadline < now:
            deadline += timedelta(days=1)
        return deadline
    except ValueError:
        return None


def _parse_deadline_from_epoch_timestamp(deadline_string: str) -> Optional[datetime]:
    try:
        timestamp = int(deadline_string)
        # Prevent accidentally inputting HHMM as a timestamp
        if timestamp < 10000:
            return None
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except ValueError:
        return None
