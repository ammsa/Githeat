""" Helper methods

"""
from __future__ import absolute_import

import calendar
import math

import datetime


def normalize(dictionary, x, y):
    """
    Normalize values in dictinoary to be in range [x, y]

    :param dictionary:
    :param x: range min
    :param y: range max
    :return: dict with values changed accordingly
    """
    #  normalize to [0, 1]
    min_value = min(dictionary.values())
    max_value = max(dictionary.values())
    range1 = max_value - min_value
    for key in dictionary:
        dictionary[key] = (dictionary[key] - min_value) / range1

    # then scale [x,y] and take ceiling
    range2 = y - x
    for key in dictionary:
        dictionary[key] = math.ceil((dictionary[key] * range2) + x)

    return dictionary


def get_months(start_date, months, include_year=False):
    """
    Returns a list of months abbreviations starting from start_date
    :param include_year:
    :param start_date:
    :param months: number of previous months to return
    :return: list of months abbr if not include_year, else list of list [year, month]
    """
    result = []
    for i in range(months):
        start_date -= datetime.timedelta(days=calendar.monthrange(start_date.year,
                                                                  start_date.month)[1])
        if include_year:
            result.append([start_date.year, calendar.month_abbr[start_date.month]])
        else:
            result.append(calendar.month_abbr[start_date.month])
    return result


def get_months_with_last_same_as_first(start_date, months, include_year=False):
    """
    Returns a list of months abbreviations starting from start_date, and last month
    is the same is first month (i.e. extra month)
    :param include_year:
    :param start_date:
    :param months: number of previous months to return
    :return: list of months abbr if not include_year, else list of tuple [year, month]
    """
    if include_year:
        months = get_months(datetime.date.today(), 12, include_year=True)
        #  update last month to have current year
        months = [[start_date.year, calendar.month_abbr[start_date.month]]] + months
    else:
        months = get_months(datetime.date.today(), 12)
        #  append current month to front of list
        months = [months[-1]] + months

    return months