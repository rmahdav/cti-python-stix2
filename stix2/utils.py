"""Utility functions and classes for the stix2 library."""

import datetime as dt
import json

import pytz
from dateutil import parser

# Sentinel value for fields that should be set to the current time.
# We can't use the standard 'default' approach, since if there are multiple
# timestamps in a single object, the timestamps will vary by a few microseconds.
NOW = object()


def get_timestamp():
    return dt.datetime.now(tz=pytz.UTC)


def format_datetime(dttm):
    # 1. Convert to timezone-aware
    # 2. Convert to UTC
    # 3. Format in ISO format
    # 4. Add subsecond value if non-zero
    # 5. Add "Z"

    try:
        zoned = dttm.astimezone(pytz.utc)
    except ValueError:
        # dttm is timezone-naive; assume UTC
        pytz.utc.localize(dttm)
    ts = zoned.strftime("%Y-%m-%dT%H:%M:%S")
    if zoned.microsecond > 0:
        ms = zoned.strftime("%f")
        ts = ts + '.' + ms.rstrip("0")
    return ts + "Z"


def parse_into_datetime(value):
    if isinstance(value, dt.date):
        if hasattr(value, 'hour'):
            return value
        else:
            # Add a time component
            return dt.datetime.combine(value, dt.time(), tzinfo=pytz.utc)

    # value isn't a date or datetime object so assume it's a string
    try:
        parsed = parser.parse(value)
    except TypeError:
        # Unknown format
        raise ValueError("must be a datetime object, date object, or "
                         "timestamp string in a recognizable format.")
    if parsed.tzinfo:
        return parsed.astimezone(pytz.utc)
    else:
        # Doesn't have timezone info in the string; assume UTC
        return pytz.utc.localize(parsed)


def get_dict(data):
    """Return data as a dictionary.
    Input can be a dictionary, string, or file-like object.
    """

    if type(data) is dict:
        obj = data
    else:
        try:
            obj = json.loads(data)
        except TypeError:
            obj = json.load(data)

    return obj
