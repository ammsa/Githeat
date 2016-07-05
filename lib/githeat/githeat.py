#!/usr/bin/env python
from __future__ import print_function

import datetime
import itertools
import sys
from collections import Counter, defaultdict

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from itertools import cycle
import os
from xtermcolor import colorize

from .core import logger
from .util import helpers

DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

COLORS_GRASS = [0, 22, 28, 34, 40, 46]
COLORS_SKY = [0, 24, 31, 38, 45, 51]
COLORS_FIRE = [0, 220, 214, 208, 202, 196]
COLORS = [COLORS_GRASS, COLORS_FIRE, COLORS_SKY]

BLOCK_THICK = '   '
BLOCK_REG = '  '
BLOCK_THIN = ' '


class Commit:
    def __init__(self, abbr_commit_hash, date, author, author_email, subject):
        self.abbr_commit_hash = abbr_commit_hash
        self.date = date
        self.author = author
        self.author_email = author_email
        self.subject = subject

    def __cmp__(self, other):
        if hasattr(other, 'date'):
            return self.date.__cmp__(other.date)

    def __str__(self):
        return "{} on {}".format(self.author, self.date)

    def __repr__(self):
        return self.__str__()


class Githeat:
    class _Column:

        def __init__(self, width, full_empty_col=False):
            if full_empty_col:
                self.col = [[None, width]] * 7
            else:
                self.col = []

            self.width = width

        def append(self, val):
            if len(self.col) >= 7:
                raise ValueError("Can't add more than 7 days")
            self.col.append(val)

        def fill(self):
            while len(self.col) != 7:
                self.col += [[None, self.width]]

        def fill_by(self, first_x):
            self.col += [[None, self.width]] * first_x

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

    def __init__(self, git_repo,
                 gtype='block', width='reg', days=[], color='grass', colors=[],
                 stat=False, stat_number=5, separate=True, month_merge=False,
                 legend=False, author=None, grep=None, config=None,
                 logging_level="CRITICAL"
                 ):
        self.git_repo = git_repo

        self.gtype = gtype
        self.width = BLOCK_REG
        self.days = days
        self.days_toggle = [False] * 7
        self.months = []
        self.display_months = []
        self.display_months_toggle = []
        global COLORS
        if colors:
            COLORS = colors
        self.colors_iterator = cycle(COLORS)
        self.colors = self.switch_to_next_color()

        self.stat = stat
        self.stat_number = stat_number
        self.block_separation_show = ' ' if separate else ''
        self.month_merge = month_merge
        self.hide_legend = legend
        self.author = author
        self.grep = grep

        self.config = config

        self.commits_db = None
        self.daily_contribution_map = None

        if width:
            if width == 'thick':
                self.width = BLOCK_THICK
            elif width == 'thin':
                self.width = BLOCK_THIN

        if color:
            if color == 'sky':
                self.colors = COLORS_SKY
            elif color == 'fire':
                self.colors = COLORS_FIRE

        logger.start(logging_level)
        logger.debug("initialing Githeat instance")

    def toggle_day(self, day_num):
        """
        Toggles a day to be shown and updates self.days
        """
        if 0 <= day_num <= 6:
            self.days_toggle[day_num] = not self.days_toggle[day_num]  # toggle day
            self.days = [d for idx, d in enumerate(DAYS) if self.days_toggle[idx]]

    def toggle_month(self, num):
        """
        Toggles a month to be shown and updates self.month_to_be_shown
        """
        if num > len(self.months) - 1:
            return
        self.display_months_toggle[num] = not self.display_months_toggle[num]
        self.display_months = []
        for idx, m in enumerate(self.months):
            if self.display_months_toggle[idx]:
                self.display_months.append(m)

    def switch_to_next_color(self):
        """
        Updates colors to next color in `COLORS` list
        """
        self.colors = self.colors_iterator.next()
        return self.colors

    def parse_commits(self):
        """
        Parses the 'git_repo' git log

        """
        logger.debug("parsing git log")
        delimiter = '<githeat_delimeter>'
        git_log_args = ["--since=1 year 7 days",
                        "--pretty=format:'%h{0}%ci{0}%an{0}%ae{0}%s'".format(delimiter),
                        "--date=local"]
        if self.author:
            git_log_args.append('--author={}'.format(self.author))
        if self.grep:
            git_log_args.append("--grep={}".format(self.grep))

        last_year_log_dates = self.git_repo.log(git_log_args)
        raw_commits = last_year_log_dates.replace("'", '').split("\n")
        self.commits_db = {}  # holds commits by date as key

        if raw_commits and raw_commits[0]:  # check if there exists any contribution
            for rc in raw_commits:
                [abbr_commit_hash, exact_date_and_time, author, author_email, subject]\
                    = helpers.remove_accents(rc).split(delimiter)
                # author = author.decode('ascii', 'ignore')
                exact_date_and_time = parse_date(exact_date_and_time)

                #  if user specified what days to show, skip if not included
                if self.days and exact_date_and_time.strftime("%A") not in self.days:
                    continue

                commit = Commit(abbr_commit_hash,
                                exact_date_and_time,
                                author,
                                author_email,
                                subject)
                if exact_date_and_time.date() in self.commits_db:
                    self.commits_db[exact_date_and_time.date()].append(commit)
                else:
                    self.commits_db[exact_date_and_time.date()] = [commit]
        else:
            print('No contribution found')
            sys.exit(0)

    def init_daily_contribution_map(self):
        """
        Initialize daily contribution maps with 0 contributions on each day
        """
        logger.debug("init contributions")

        self.daily_contribution_map = defaultdict(float)

        today = datetime.date.today()
        last_year = today - relativedelta(years=1, days=7)

        #  iterate through from last year date + 7 days and init dict with zeros
        delta = today - last_year
        flag_skip_til_first_sunday = True
        for i in range(delta.days + 1):
            current_day = last_year + datetime.timedelta(days=i)
            # we need to start from the first sunday, so skip anything before it
            if flag_skip_til_first_sunday:
                if current_day.strftime("%A") != 'Sunday':
                    continue
                else:
                    flag_skip_til_first_sunday = False

            # update self.months with the months in the graph
            year_month = datetime.date(current_day.year, current_day.month, 1)
            if year_month not in self.months:
                self.months.append(year_month)

            self.daily_contribution_map[current_day] = 0.0

        self.display_months_toggle = [False] * len(self.months)

    def reset_daily_contribution_map(self):
        """
        Resets daily contribution map to zero values
        """
        logger.debug("resetting contributions")

        for d in self.daily_contribution_map:
            self.daily_contribution_map[d] = 0.0

    def compute_daily_contribution_map(self):
        """
        Compute how many commits were committed on each day
        """
        logger.debug("Computing contributions")

        # update dict with contributions
        for commits_on_day in self.commits_db:
            for commit in self.commits_db[commits_on_day]:

                #  if user specified what days to show, skip commit if from that day
                if self.days and commit.date.strftime("%A") not in self.days:
                    continue

                #  if user specified what months to show, skip commit from that month
                if self.display_months and datetime.date(commit.date.year,
                                                         commit.date.month,
                                                         1) not in self.display_months:
                    continue

                contribution_day = datetime.date(commit.date.year,
                                                 commit.date.month,
                                                 commit.date.day)

                if contribution_day in self.daily_contribution_map:
                    self.daily_contribution_map[contribution_day] += 1.0

    def normalize_daily_contribution_map(self, x1=0, x2=5):
        """
        Normalizes daily contribution to values between [x1, x2]
        Default is set to [0, 5] because we have 6 colors
        :param x2: range to
        :param x1: range from
        """
        logger.debug("Normalizing contributions")

        # normalize values to be between [x1, x2]
        self.daily_contribution_map = helpers.normalize_dict(self.daily_contribution_map,
                                                             x1, x2)

    def recompute_daily_contribution_map(self):
        """
        Recompute daily contribution and new normalized values
        """
        logger.debug("Recomputing contributions")

        self.reset_daily_contribution_map()
        self.compute_daily_contribution_map()
        self.normalize_daily_contribution_map()

    def print_graph_month_header(self):
        """
        Prints and returns a list of months abbreviations header

        """
        # TODO: align months correctly with its month block
        # months = get_months_with_last_same_as_first(datetime.date.today(), 12)
        #
        # for month in months:
        #     print(colorize(month, ansi=MONTHS_COLOR),
        #           end=" " * 8,
        #           )
        # print()
        # return months
        raise NotImplementedError

    def get_matrix_width(self, matrix):
        """
        Returns the width of the matrix with the gaps and breaks
        :param matrix:
        :return:
        """

        if self.month_merge:
            start_date = matrix[0].col[0][0]
            end_date = [x[0] for x in matrix[-1].col if x[0] is not None][-1]
            delta = end_date - start_date
            width = delta.days // 7
        else:
            width = len(matrix)

        return width * len(self.width)

    def compute_graph_matrix(self):
        """
        Compute and return contribution graph matrix

        """
        logger.debug("Printing graph")

        sorted_normalized_daily_contribution = sorted(self.daily_contribution_map)
        matrix = []
        first_day = sorted_normalized_daily_contribution[0]
        if first_day.strftime("%A") != "Sunday":
            c = self._Column(self.width)
            d = first_day - datetime.timedelta(days=1)
            while d.strftime("%A") != "Saturday":
                d = d - datetime.timedelta(days=1)
                c.append([None, self.width])
            matrix.append(c)
        else:
            new_column = self._Column(self.width)
            matrix.append(new_column)
        for current_day in sorted_normalized_daily_contribution:
            last_week_col = matrix[-1]
            day_contribution_color_index = int(self.daily_contribution_map[current_day])
            color = self.colors[day_contribution_color_index]

            try:
                last_week_col.append([current_day, colorize(self.width,
                                                            ansi=0,
                                                            ansi_bg=color)])

            except ValueError:  # column (e.g. week) has ended
                new_column = self._Column(self.width)
                matrix.append(new_column)
                last_week_col = matrix[-1]
                last_week_col.append([current_day, colorize(self.width,
                                                            ansi=0,
                                                            ansi_bg=color)])

            next_day = current_day + datetime.timedelta(days=1)
            if next_day.month != current_day.month:
                #  if the column we're at isn't 7 days yet, fill it with empty blocks
                last_week_col.fill()

                #  make new empty col to separate months
                matrix.append(self._Column(self.width, full_empty_col=True))

                matrix.append(self._Column(self.width))
                last_week_col = matrix[-1]  # update to the latest column

                #  if next_day (which is first day of new month) starts in middle of the
                #  week, prepend empty blocks in the column before inserting 'next day'
                next_day_num = DAYS.index(next_day.strftime("%A"))
                last_week_col.fill_by(next_day_num)

        # make sure that the most current week (last col of matrix) col is of size 7,
        #  so fill it if it's not
        matrix[-1].fill()

        return matrix

    def print_graph(self, matrix):
        """
        Prints graph matrix

        """
        #  for each day of the week
        for i in range(7):
            #  for the week column in the matrix
            for week in matrix:

                if self.month_merge:
                    #  check if value in that week is just empty spaces and not colorize
                    if week.col[i][1] == self.width:
                        continue

                print("{}{}".format(week.col[i][1], self.block_separation_show), end="")
            print("{}".format("\n" if self.block_separation_show else ''))

    def print_inline(self):
        """
        Prints a whole year of contribution in inline form

        """
        logger.debug("Printing inline")

        sorted_normalized_daily_contribution = sorted(self.daily_contribution_map)
        for current_day in sorted_normalized_daily_contribution:
            norm_day_contribution = int(self.daily_contribution_map[current_day])
            color = self.colors[norm_day_contribution]
            print(colorize(self.width, ansi=0, ansi_bg=color),
                  end=" {}{}".format(current_day.strftime("%b %d, %Y"), '\n')
                  )

    def get_top_n_commiters(self, commits_list, n=5, normailze_values=False):
        """
        Returns a list of names of the top n commiters from a list of commits
        """
        if not commits_list:
            return None
        commits_authors = [c.author for c in commits_list]
        counter = Counter(commits_authors)
        top_n = counter.most_common(n)
        if normailze_values:
            top_n = helpers.normalize_tuple_list(top_n, 1, 5)
        return top_n

    def print_stats(self):
        """
        Prints contribution statistics

        """
        logger.debug("Printing stats")
        n = self.stat_number if self.stat_number else 5

        top_n = self.get_top_n_commiters(
                list(itertools.chain.from_iterable(self.commits_db.values())),
                n
        )

        if top_n:
            print("Top {} committers:".format(n))
            for idx, info in enumerate(top_n):
                print("{}. {}: {}".format(idx + 1, info[0], info[1]))

    def run(self):
        """
        Githeat execution logic

        """
        self.parse_commits()
        self.init_daily_contribution_map()
        self.compute_daily_contribution_map()
        self.normalize_daily_contribution_map()

        if self.gtype == 'inline':
            self.print_inline()
        else:
            matrix = self.compute_graph_matrix()
            _, width = os.popen('stty size', 'r').read().split()
            matrix_width = self.get_matrix_width(matrix)
            if matrix_width > int(width):
                print("Your terminal width is smaller than the heatmap. Please "
                      "consider using the --width {thin, reg, thick},  resizing your "
                      "terminal, or merging months by including --month-merge")
                return
            self.print_graph(matrix)

        if self.stat:
            print()
            self.print_stats()
