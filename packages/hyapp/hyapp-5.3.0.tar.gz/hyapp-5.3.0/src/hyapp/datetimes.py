from __future__ import annotations

import datetime


def dt_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def require_aware_dt(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        raise ValueError(f"TZ-aware datetime is required, got {value!r}")
    return value


def floor_dt_to_interval(dt: datetime.datetime, interval_sec: float) -> datetime.datetime:
    """
    Round datetime down to the nearest whole number of intervals from midnight.

    >>> floor_dt_to_interval(datetime.datetime.fromisoformat("2023-04-05T06:07:48Z"), 30.0).isoformat()
    '2023-04-05T06:07:30+00:00'
    >>> floor_dt_to_interval(datetime.datetime.fromisoformat("2023-04-05T06:07:48Z"), 60.0).isoformat()
    '2023-04-05T06:07:00+00:00'
    """
    dt_date = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_seconds = (dt - dt_date).total_seconds()
    assert day_seconds >= 0
    dt_intervals = day_seconds / interval_sec
    offset_sec = (dt_intervals - int(dt_intervals)) * interval_sec
    return dt - datetime.timedelta(seconds=offset_sec)
