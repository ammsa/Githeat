"""Script to show heatmap of git repo."""
from __future__ import print_function

import argparse
import calendar
import copy
import math

from git import Git
from git.exc import InvalidGitRepositoryError
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import datetime
from xtermcolor import colorize

import sys

COLORS = [0, 22, 28, 34, 40, 46]
COLORS_BLUE = [16, 17, 18, 19, 20, 21]
COLORS_YELLOW_RED = [232, 220, 214, 208, 202, 196]

BLOCK_THICK = '   '
BLOCK_REG = '  '
BLOCK_THIN = ' '

GRAPH_INLINE = False
GRAPH_BLOCK = True
GRAPH_MONTH = True
MONTH_SEPARATION = False

# Defaults
GRAPH_TYPE = GRAPH_BLOCK
BLOCK_WIDTH = BLOCK_REG
MONTH_SEPARATION_SHOW = MONTH_SEPARATION
GRAPH_MONTH_SHOW = GRAPH_MONTH
MONTHS_COLOR = 6


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


def graph_inline(day_contribution_map):
    """
    Prints a whole year of contribution in inline form
    :param day_contribution_map:
    :return:
    """
    sorted_nomr_daily_contribution = sorted(day_contribution_map)
    for day in sorted_nomr_daily_contribution:
        for i in range(0, 54 * 7):
            current_day = day + datetime.timedelta(days=i)
            if current_day <= datetime.date.today():
                norm_day_contribution = int(day_contribution_map[current_day])
                color = COLORS[norm_day_contribution]
                print(colorize(BLOCK_WIDTH, ansi=0, ansi_bg=color),
                      end=" {}{}".format(current_day.strftime("%b %d, %Y"), '\n')
                      )
        print()
        break


def get_month_from_abbrv(month_abbrv):
    """
    Given the month abbrv, return it's number
    :param month_abbrv:
    :return:
    """
    return list(calendar.month_abbr).index(month_abbrv)


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


def print_graph_month_header():
    """
    Prints and returns a list of months abbreviations
    :return:
    """
    # TODO: align months correctly with its month block
    months = get_months_with_last_same_as_first(datetime.date.today(), 12)

    for month in months:
        print(colorize(month, ansi=MONTHS_COLOR),
              end=" " * 8,
              )
    print()
    return months


def graph_block(day_contribution_map):
    # TODO: Show months correctly aligned
    # if GRAPH_MONTH_SHOW and BLOCK_WIDTH is not BLOCK_THIN:
    #     print_graph_month_header()

    sorted_nomr_daily_contribution = sorted(day_contribution_map)

    streched_days = []
    copy_sorted_nomr_daily_contribution = copy.deepcopy(sorted_nomr_daily_contribution)
    for i in range(1, 55):
        first_seven_day_of_year = []
        for j in range(7):
            try:
                first_seven_day_of_year.append(copy_sorted_nomr_daily_contribution.pop(0))
            except IndexError:
                #  less than a week
                break

        for current_day in first_seven_day_of_year:
            norm_day_contribution = int(day_contribution_map[current_day])
            color = COLORS[norm_day_contribution]
            streched_days.append((current_day, colorize(BLOCK_WIDTH,
                                                        ansi=0,
                                                        ansi_bg=color)))
    if MONTH_SEPARATION:

        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                'Thursday', 'Friday', 'Saturday']
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        days_buckets = {}
        for d in days:
            days_buckets[d] = []

        months_bucket = {}

        for m in months:
            months_bucket[m] = copy.deepcopy(days_buckets)

        today_year = datetime.date.today()
        last_year = (today_year - relativedelta(years=1))

        years_bucket = {
            today_year.year: copy.deepcopy(months_bucket),
            last_year.year: copy.deepcopy(months_bucket),
        }

        #  fill in buckets
        for i in range(-1, 6):  # going day by day
            for j in range(i, len(streched_days), 7):  # jumping week by week
                day_color_pair = streched_days[j]
                day = day_color_pair[0]
                years_bucket[day.year][day.strftime("%b")][day.strftime("%A")].append(
                        day_color_pair)

        #  init months width dict
        months_width = {}
        for y in [today_year.year, last_year.year]:
            for m in months:
                key = datetime.date(y, get_month_from_abbrv(m), 1)
                months_width[key] = 0

        for y in years_bucket:
            for m in years_bucket[y]:
                width = max([len(x) for x in years_bucket[y][m].values()])
                key = datetime.date(y, get_month_from_abbrv(m), 1)
                months_width[key] = width

        #  remove un-used keys
        months_width = {k: v for k, v in months_width.items() if v}

        print('Months widths:')
        for mw in months_width:
            print("{}  {}".format(mw, months_width[mw]))
        print()

        print("Months order")
        months_order = get_months_with_last_same_as_first(datetime.date.today(),
                                                          12,
                                                          include_year=True)
        months_order.reverse()

        print(months_order)
        print()

        # TODO: Separate months by space

    else:

        for i in range(0, 6):
            for j in range(i, len(streched_days), 7):
                print("{}".format(streched_days[j][1]), end="")
            print()

    print()


def main():
    parser = argparse.ArgumentParser(
            description='githeat: Heatmap for your git repos on your terminal')

    parser.add_argument('--type', '-t',
                        choices=['inline', 'block'],
                        help='Choose how you want the graph to be displayed',
                        default='block')

    parser.add_argument('--width', '-w',
                        choices=['thick', 'regular', 'thin'],
                        help='Choose how wide you want the graph blocks to be',
                        default='regular')

    parser.add_argument('--author', '-a',
                        help='Filter heatmap by author. You can also write regex here')

    cli = parser.parse_args()

    if cli.type.lower() == 'inline':
        global GRAPH_INLINE
        GRAPH_INLINE = True

    if cli.width:
        global BLOCK_WIDTH

        if cli.width.lower() == 'thick':
            BLOCK_WIDTH = BLOCK_THICK
        elif cli.width.lower() == 'regular':
            BLOCK_WIDTH = BLOCK_REG
        else:
            BLOCK_WIDTH = BLOCK_THIN

    author = cli.author

    try:
        g = Git('/Users/mustafa/Repos/groppus')
        git_log_args = ["--since=1.year",
                        "--pretty=format:'%ci'"]
        if author:
            git_log_args.append('--author={}'.format(author))

        last_year_log_dates = g.log(git_log_args)
        dates = last_year_log_dates.replace("'", '').split('\n')
        if dates and dates[0]:
            dates = [parse(dt) for dt in dates]
        else:
            print('No contribution found')
            sys.exit(0)

        day_contribution_map = defaultdict(float)

        today = datetime.date.today()
        last_year = today - relativedelta(years=1)

        #  iterate through from last year date and init dict with zeros
        delta = today - last_year
        for i in range(delta.days + 1):
            current_day = last_year + datetime.timedelta(days=i)
            day_contribution_map[current_day] = 0.0

        # update dict with contributions
        for dt in dates:
            contribution_day = datetime.date(dt.year, dt.month, dt.day)
            if contribution_day in day_contribution_map:
                day_contribution_map[contribution_day] += 1.0

        # normalize values between [0, 5] because we have six colors
        day_contribution_map = normalize(day_contribution_map, 0, 5)

        if GRAPH_INLINE:
            graph_inline(day_contribution_map)
        else:
            graph_block(day_contribution_map)

    except InvalidGitRepositoryError:
        print('Are you sure your in an initialized git directory?')


if __name__ == '__main__':
    sys.exit(main())
