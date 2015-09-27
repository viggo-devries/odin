# -*- coding: utf-8 -*-
import datetime
from odin import datetimeutil


STRING_TYPES = {}


def register_string_type(data_type, serialise_method):
    """
    Register a data type serialise method that results in a string.

    :param data_type: a type instance that string data type should match.
    :param serialise_method: a method that accepts a single value that will return a string representation of
        the serialised type.

    """
    STRING_TYPES[data_type] = serialise_method


def date_iso_format(value):
    """
    Serialise a datetime.date to ISO string format.
    """
    assert isinstance(value, datetime.date)
    return value.isoformat()


class DatetimeIsoFormat(object):
    """
    Serialise a datetime.time or datetime.datetime to ISO string format.
    """
    def __init__(self, default_timezone=datetimeutil.local):
        self.default_timezone = default_timezone

    def __call__(self, value):
        assert isinstance(value, (datetime.time, datetime.datetime))
        if value.tzinfo is None:
            value = value.replace(tzinfo=self.default_timezone)
        return value.isoformat()

datetime_iso_format = DatetimeIsoFormat()
TimeIsoFormat = DatetimeIsoFormat
time_iso_format = TimeIsoFormat()


class DatetimeEcmaFormat(object):
    """
    Serialize a datetime object into the ECMA defined format.
    """
    input_type = datetime.datetime

    def __init__(self, assume_local=True, default_timezone=datetimeutil.local):
        self.default_timezone = datetimeutil.local if assume_local else default_timezone

    def __call__(self, value):
        assert isinstance(value, self.input_type)
        return datetimeutil.to_ecma_datetime_string(value, self.default_timezone)

datetime_ecma_format = DatetimeEcmaFormat()
