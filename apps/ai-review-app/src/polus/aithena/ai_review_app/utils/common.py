"""Common types and functions for AI Review Dashboard."""

# pylint: disable=unused-import
import datetime
from polus.aithena.common.logger import get_logger

TIME_FORMAT = '%Y-%m-%d %H:%M'
DATE_FORMAT = '%Y-%m-%d'

def display_time_from_datetime(d: datetime.datetime):
    return d.strftime(TIME_FORMAT)

def display_date_from_datetime(d: datetime.datetime):
    return d.strftime(DATE_FORMAT)

def current_date():
    return display_date_from_datetime(datetime.datetime.now())

def current_time():
    return display_time_from_datetime(datetime.datetime.now())