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
MONTH_SEPARATION = True
BLOCK_SEPARATION = False

# Defaults
GRAPH_TYPE = GRAPH_BLOCK
BLOCK_WIDTH = BLOCK_REG
MONTH_SEPARATION_SHOW = MONTH_SEPARATION
BLOCK_SEPARATION_SHOW = ' ' if BLOCK_SEPARATION else ''
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

        class Column:

            def __init__(self, full_empty_col=False):
                if full_empty_col:
                    self.col = [[None, BLOCK_WIDTH]] * 7
                else:
                    self.col = []

            def append(self, val):
                if len(self.col) >= 7:
                    raise ValueError("Can't add more than 7 days")
                self.col.append(val)

            def fill(self):
                while len(self.col) != 7:
                    self.col += [[None, BLOCK_WIDTH]]

            def fill_by(self, first_x):
                self.col += [[None, BLOCK_WIDTH]] * first_x

            def __len__(self):
                return len(self.col)

            def __str__(self):
                result = ""
                for c in self.col:
                    result += str(c[0]) + "\n"
                return result

            def __repr__(self):
                if self.col:
                    return "Week of {}".format(self.col[0][0])
                else:
                    return "Empty col"

        matrix = []
        first_day = sorted_nomr_daily_contribution[0]
        if first_day.strftime("%A") != "Sunday":
            c = Column()
            d = first_day - datetime.timedelta(days=1)
            while d.strftime("%A") != "Saturday":
                d = d - datetime.timedelta(days=1)
                c.append([None, BLOCK_WIDTH])
            matrix.append(c)
        else:
            new_column = Column()
            matrix.append(new_column)

        for current_day in sorted_nomr_daily_contribution:
            last_week_col = matrix[-1]
            norm_day_contribution = int(day_contribution_map[current_day])
            color = COLORS[norm_day_contribution]

            try:
                last_week_col.append([current_day, colorize(BLOCK_WIDTH,
                                                            ansi=0,
                                                            ansi_bg=color)])

            except ValueError:
                new_column = Column()
                matrix.append(new_column)
                last_week_col = matrix[-1]
                last_week_col.append([current_day, colorize(BLOCK_WIDTH,
                                                            ansi=0,
                                                            ansi_bg=color)])

            next_day = current_day + datetime.timedelta(days=1)
            if next_day.month != current_day.month:
                # if week isn't 7 days, fill it with empty blocks
                last_week_col.fill()

                #  make new empty col to separate months
                matrix.append(Column(full_empty_col=True))

                matrix.append(Column())
                last_week_col = matrix[-1]

                #  if next_day (which is first day of new month) starts in middle of the
                #  week, prepend empty blocks in the next col before inserting 'next day'
                next_day_num = days.index(next_day.strftime("%A"))
                last_week_col.fill_by(next_day_num)

        #  make sure that most current week (last col of matrix) col is of size 7,
        #  so fill it if it's not
        matrix[-1].fill()

        for i in range(7):
            for week in matrix:
                print("{}{}".format(week.col[i][1], BLOCK_SEPARATION_SHOW), end="")
            print("{}".format("\n" if BLOCK_SEPARATION_SHOW else ''))

    else:
        for i in range(0, 6):
            for j in range(i, len(streched_days), 7):
                print("{}{}".format(streched_days[j][1], BLOCK_SEPARATION_SHOW), end="")
            print("{}".format("\n" if BLOCK_SEPARATION_SHOW else ''))



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
        last_year = today - relativedelta(years=1, days=7)

        #  iterate through from last year date and init dict with zeros
        delta = today - last_year
        flag_skip_til_first_sunday = True
        for i in range(delta.days + 1):
            current_day = last_year + datetime.timedelta(days=i)
            if flag_skip_til_first_sunday:
                if current_day.strftime("%A") != 'Sunday':
                    continue
                else:
                    flag_skip_til_first_sunday = False
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
