from datetime import datetime, timezone, timedelta


def parse_deadline(deadline_string: str) -> datetime | None:
    """
    Parses a deadline string into a datetime object.
    Supports absolute time in UTC ('HH:MM'), relative time ('+[HHh][MMm]'), or Unix timestamp.
    :param deadline_string: The deadline string to parse.
    :return: A datetime object or None if the string cannot be parsed.
    """
    now = datetime.now(timezone.utc)
    for parser in (_parse_relative_deadline, _parse_deadline_from_utc, _parse_deadline_from_epoch_timestamp):
        result = parser(deadline_string, now)
        if result:
            return result
    return None


def _parse_deadline_from_utc(deadline_string: str, now: datetime) -> datetime | None:
    try:
        deadline = datetime.strptime(deadline_string, "%H:%M").replace(year=now.year, month=now.month, day=now.day,
                                                                       tzinfo=timezone.utc)
        return deadline if deadline >= now else deadline + timedelta(days=1)
    except ValueError:
        return None


def _parse_deadline_from_epoch_timestamp(deadline_string: str, _: datetime) -> datetime | None:
    try:
        timestamp = int(deadline_string)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp >= 10000 else None
    except ValueError:
        return None


def _parse_relative_deadline(deadline_string: str, now: datetime) -> datetime | None:
    delta = _convert_to_timedelta(deadline_string)
    return _round_datetime_to_nearest_half_hour(now + delta) if delta else None


def _convert_to_timedelta(delta_str: str) -> timedelta | None:
    if '+' not in delta_str or ('h' not in delta_str and 'm' not in delta_str):
        return None
    try:
        hours, minutes = 0.0, 0.0
        if 'h' in delta_str:
            hours = float(delta_str[1:delta_str.find('h')].strip())
        if 'm' in delta_str:
            minutes_start = delta_str.find('h') + 1 if 'h' in delta_str else 1
            minutes = float(delta_str[minutes_start:delta_str.find('m')].strip())
        return timedelta(hours=hours, minutes=minutes)
    except ValueError:
        return None


def _round_datetime_to_nearest_half_hour(input_time: datetime) -> datetime:
    minutes = input_time.minute
    if minutes < 15:
        return input_time.replace(minute=0, second=0, microsecond=0)
    elif minutes < 45:
        return input_time.replace(minute=30, second=0, microsecond=0)
    else:
        return (input_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
