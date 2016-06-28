"""Script to show heatmap of git repo."""
from __future__ import print_function

import argparse
import calendar
import math
import random

from git import Git
from git.exc import InvalidGitRepositoryError
from dateutil.parser import parse
from dateutil.tz import tzoffset
from collections import defaultdict
import datetime
from xtermcolor import colorize

import sys

COLORS = [0, 22, 28, 34, 40, 46]

BLOCK_THICK = '   '
BLOCK_REG   = '  '
BLOCK_THIN  = ' '

GRAPH_INLINE = False
GRAPH_BLOCK = True
GRAPH_MONTH = True
MONTH_SEPARATION = True

# Defaults
GRAPH_TYPE = GRAPH_BLOCK
BLOCK_WIDTH = BLOCK_REG
MONTH_SEPARATION_SHOW = MONTH_SEPARATION
GRAPH_MONTH_SHOW = GRAPH_MONTH
MONTHS_COLOR = 6


def normalize(dictionary, x, y):
    #  normalize to [0, 1]
    min_value = min(dictionary.values())
    max_value = max(dictionary.values())
    range1 = max_value - min_value
    for key in dictionary:
        dictionary[key] = (dictionary[key] - min_value) / range1

    #  then scale [x,y] and take ceiling
    range2 = y - x
    for key in dictionary:
        dictionary[key] = math.ceil((dictionary[key] * range2) + x)

    return dictionary


def graph_inline(day_contribution_map):
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


def get_months(start_date, months):
    """
    Returns a list of months abbreviations starting from start_date
    :param start_date:
    :param months: number of previous months to return
    :return: list of months abbr
    """
    result = []
    for i in range(months):
        start_date -= datetime.timedelta(days=calendar.monthrange(start_date.year, start_date.month)[1])
        result.append(calendar.month_abbr[start_date.month])
    return result


def print_graph_month_header():
    months = get_months(datetime.date.today(), 12)
    #  append current month to front of list
    months = [months[-1]] + months

    for month in months:
        print(colorize(month, ansi=MONTHS_COLOR),
                      end="       ",
                      )
    print()


def graph_block(day_contribution_map):

    # TODO: Show months correctly aligned
    # if GRAPH_MONTH_SHOW and BLOCK_WIDTH is not BLOCK_THIN:
    #     print_graph_month_header()

    sorted_nomr_daily_contribution = sorted(day_contribution_map)
    #  iterate weekly staring from days of the year's first week
    first_seven_day_of_year = sorted_nomr_daily_contribution[:7]
    for day in first_seven_day_of_year:
        month_index = day.month
        for i in range(0, 54 * 7, 7):
            current_day = day + datetime.timedelta(days=i)
            # TODO: Separate months by space
            # if MONTH_SEPARATION_SHOW:
            #     if current_day.month != month_index:
            #         print(" ", end="")
            #         month_index = current_day.month
            if current_day <= datetime.date.today():
                norm_day_contribution = int(day_contribution_map[current_day])
                color = COLORS[norm_day_contribution]
                print(colorize(BLOCK_WIDTH, ansi=0, ansi_bg=color), end="")
        print()


def main():

    try:
        g = Git('/Users/mustafa/Repos/groppus')
        # loginfo = g.log()
        last_year_log_dates = g.log('--author=Mustafa', "--since=2.year", "--pretty=format:'%ci'")
        # loginfo = g.log('--author=Afshin Mehrabani', '--pretty=tformat:','--numstat')
        dates = last_year_log_dates.replace("'", '').split('\n')
        if dates and dates[0]:
            dates = [parse(dt) for dt in dates]
        else:
            print('No contribution found')
            sys.exit(0)

        day_contribution_map = defaultdict(float)

        today = datetime.date.today()
        last_year = today - datetime.timedelta(days=365 + 7)

        #  iterate through from last year date and init dict with zeros
        delta = today - last_year
        for i in range(delta.days + 1):
            current_day = last_year + datetime.timedelta(days=i)
            day_contribution_map[current_day] = 0.0

        #  update dict with contributions
        for dt in dates:
            contribution_day = datetime.date(dt.year, dt.month, dt.day)
            if contribution_day in day_contribution_map:
                day_contribution_map[contribution_day] += 1.0

        #  normalize values between [0, 5] because we have six colors
        day_contribution_map = normalize(day_contribution_map, 0, 5)

        if GRAPH_INLINE:
            graph_inline(day_contribution_map)
        else:
            graph_block(day_contribution_map)



        # print
        #
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print
        # for i in [0, 22, 28, 34, 40, 46]:
        #     print(colorize('  ', ansi=0, ansi_bg=i)),
        #     for j in random.sample([0, 22, 28, 34, 40, 46], len([0, 22, 28, 34, 40, 46])):
        #         print(colorize('  ', ansi=0, ansi_bg=j)),
        # print

    except InvalidGitRepositoryError:
        print('Are you sure your in an initialized git directory?')

if __name__ == '__main__':
    sys.exit(main())
