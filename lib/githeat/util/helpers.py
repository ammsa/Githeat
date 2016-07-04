""" Helper methods

"""
from __future__ import absolute_import

import calendar
import math

import datetime
from operator import itemgetter

import unicodedata


def normalize_dict(dictionary, x, y):
    """
    Normalize values in dictinoary to be in range [x, y]

    :param dictionary:
    :param x: range min
    :param y: range max
    :return: dict with values changed accordingly
    """
    min_value = min(dictionary.values())
    max_value = max(dictionary.values())
    if max_value <= y and min_value >= x:
        return dictionary

    #  normalize to [0, 1]
    range1 = max_value - min_value
    if not range1:
        range1 = 1
    for key in dictionary:
        dictionary[key] = (float(dictionary[key]) - min_value) / range1

    # then scale [x,y] and take ceiling
    range2 = y - x
    for key in dictionary:
        dictionary[key] = math.ceil((float(dictionary[key]) * range2) + x)

    return dictionary


def normalize_tuple_list(tuple_list, x, y):
    """
    Normalize values in a list of tuples to be in range [x, y]

    :param tuple_list:
    :param x: range min
    :param y: range max
    :return: list of tuples with values changed accordingly
    """
    min_value = min(tuple_list, key=itemgetter(1))[1]
    max_value = max(tuple_list, key=itemgetter(1))[1]
    if max_value <= y and min_value >= x:
        return tuple_list

    #  normalize to [0, 1]
    range1 = max_value - min_value
    if not range1:
        range1 = 1
    for idx, pair in enumerate(tuple_list):
        key = pair[0]
        value = (float(pair[1]) - min_value) / range1
        tuple_list[idx] = (key, value)

    # then scale [x,y] and take ceiling
    range2 = y - x
    for idx, pair in enumerate(tuple_list):
        key = pair[0]
        value = math.ceil((float(pair[1]) * range2) + x)
        tuple_list[idx] = (key, value)

    return tuple_list


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


def remove_accents(input_str):
    """
    Removes accents from input string
    :param input_str:
    :return:
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii

def first(iterable, func=lambda L: L is not None, **kwargs):
    """
    Get first non none iterm from list
    :param iterable:
    :param func:
    :param kwargs:
    :return:
    """
    it = (el for el in iterable if func(el))
    if 'default' in kwargs:
        return next(it, kwargs['default'])
    return next(it) # no default so raise `StopIteration`