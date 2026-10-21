"""Shared date bucketing for the activity charts (admin-wide and per-user)."""
from datetime import date, timedelta
from typing import Callable

# range key -> (days covered, days per bar). 3 months is 13 weekly bars so the chart stays readable.
RANGES = {"7d": (7, 1), "1m": (30, 1), "3m": (91, 7)}
RANGE_PATTERN = "^(7d|1m|3m)$"


def make_buckets(range_key: str, today: date | None = None):
    """Return (since_day, days_per_bar, buckets, locate) for a range.

    `locate("YYYY-MM-DD")` returns the bucket dict that day falls into, or None.
    """
    days, size = RANGES[range_key]
    today = today or date.today()
    since = today - timedelta(days=days - 1)
    count = days // size
    buckets = [
        {
            "date": (since + timedelta(days=i * size)).isoformat(),
            "queries": 0,
            "document_views": 0,
            "security_events": 0,
        }
        for i in range(count)
    ]

    def locate(day_str) -> dict | None:
        try:
            offset = (date.fromisoformat(str(day_str)) - since).days
        except ValueError:
            return None
        index = offset // size
        return buckets[index] if 0 <= index < count else None

    return since, size, buckets, locate  # type: ignore[return-value]


LocateFn = Callable[[str], "dict | None"]
