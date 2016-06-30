from __future__ import print_function

import datetime
import itertools
import sys
from collections import Counter, defaultdict

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from xtermcolor import colorize
from .core import logger
from .util import helpers


days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

COLORS_GRASS = [0, 22, 28, 34, 40, 46]
COLORS_SKY = [0, 24, 31, 38, 45, 51]
COLORS_FIRE = [232, 220, 214, 208, 202, 196]

BLOCK_THICK = '   '
BLOCK_REG = '  '
BLOCK_THIN = ' '


class Commit:
    def __init__(self, date, author):
        self.date = date
        self.author = author

    def __cmp__(self, other):
        if hasattr(other, 'date'):
            return self.date.__cmp__(other.date)


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
                 gtype='block', width='reg', days=None, color='grass',
                 stat=False, stat_number=5, separate=True, month_merge=False,
                 author=None, config=None, logging_level="CRITICAL"
                 ):

        self.git_repo = git_repo

        self.gtype = gtype
        self.width = BLOCK_REG
        self.days = days
        self.color = COLORS_GRASS

        self.stat = stat
        self.stat_number = stat_number
        self.separate = separate
        self.block_separation_show = ' ' if separate else ''
        self.month_merge = month_merge
        self.author = author

        self.config = config

        self.commits_db = None
        self.commits_dates = None
        self.day_contribution_map = None

        if width:
            if width == 'thick':
                self.width = BLOCK_THICK
            elif width == 'thin':
                self.width = BLOCK_THIN

        if color:
            if color == 'sky':
                self.color = COLORS_SKY
            elif color == 'fire':
                self.color = COLORS_FIRE

        logger.start(logging_level)
        logger.debug("initialing githeat instance")

    def parse_commits(self):
        """
        Parses the 'git_repo' git log

        """
        logger.debug("parsing git log")

        git_log_args = ["--since=1 year 7 days",
                        "--pretty=format:'%ci ~ %an'"]
        if self.author:
            git_log_args.append('--author={}'.format(self.author))

        last_year_log_dates = self.git_repo.log(git_log_args)

        raw_commits = last_year_log_dates.replace("'", '').encode('utf-8').split("\n")
        commits_db = {}  # holds commits by date as key

        if raw_commits and raw_commits[0]:
            for rc in raw_commits:
                date, author = rc.split(" ~ ")
                date = parse_date(date)

                if self.days and date.strftime("%A") not in self.days:
                    continue

                commit = Commit(date, author)
                if date in commits_db:
                    commits_db[date].append(commit)
                else:
                    commits_db[date] = [commit]
        else:
            print('No contribution found')
            sys.exit(0)

        self.commits_dates = commits_db.keys()

    def compute_daily_contribution_map(self):
        """
        Compute how many commits were committed on each day
        """
        logger.debug("Computing contributions")

        self.day_contribution_map = defaultdict(float)

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

            self.day_contribution_map[current_day] = 0.0

        # update dict with contributions
        for dt in self.commits_dates:
            contribution_day = datetime.date(dt.year, dt.month, dt.day)
            if contribution_day in self.day_contribution_map:
                self.day_contribution_map[contribution_day] += 1.0

    def normalize_daily_contribution_map(self):
        logger.debug("Normalizing contributions")

        # normalize values between [0, 5] because we have six colors
        self.day_contribution_map = helpers.normalize(self.day_contribution_map, 0, 5)

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

    def print_graph(self):
        """
        Prints contribution graph

        """
        logger.debug("Printing graph")

        sorted_nomr_daily_contribution = sorted(self.day_contribution_map)
        matrix = []
        first_day = sorted_nomr_daily_contribution[0]
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
        for current_day in sorted_nomr_daily_contribution:
            last_week_col = matrix[-1]
            norm_day_contribution = int(self.day_contribution_map[current_day])
            color = self.color[norm_day_contribution]

            try:
                last_week_col.append([current_day, colorize(self.width,
                                                            ansi=0,
                                                            ansi_bg=color)])

            except ValueError:
                new_column = self._Column(self.width)
                matrix.append(new_column)
                last_week_col = matrix[-1]
                last_week_col.append([current_day, colorize(self.width,
                                                            ansi=0,
                                                            ansi_bg=color)])

            next_day = current_day + datetime.timedelta(days=1)
            if next_day.month != current_day.month:
                # if week isn't 7 days, fill it with empty blocks
                last_week_col.fill()

                #  make new empty col to separate months
                matrix.append(self._Column(self.width, full_empty_col=True))

                matrix.append(self._Column(self.width))
                last_week_col = matrix[-1]

                #  if next_day (which is first day of new month) starts in middle of the
                #  week, prepend empty blocks in the next col before inserting 'next day'
                next_day_num = days.index(next_day.strftime("%A"))
                last_week_col.fill_by(next_day_num)

        # make sure that most current week (last col of matrix) col is of size 7,
        #  so fill it if it's not
        matrix[-1].fill()

        for i in range(7):
            for week in matrix:

                if not self.month_merge:
                    if week.col[i][1] == self.width:
                        continue

                print("{}{}".format(week.col[i][1], self.block_separation_show), end="")
            print("{}".format("\n" if self.block_separation_show else ''))

    def print_inline(self):
        """
        Prints a whole year of contribution in inline form

        """
        logger.debug("Printing inline")

        sorted_nomr_daily_contribution = sorted(self.day_contribution_map)
        for current_day in sorted_nomr_daily_contribution:
            norm_day_contribution = int(self.day_contribution_map[current_day])
            color = self.color[norm_day_contribution]
            print(colorize(self.width, ansi=0, ansi_bg=color),
                  end=" {}{}".format(current_day.strftime("%b %d, %Y"), '\n')
                  )

    def print_stats(self):
        """
        Prints contribution statistics

        """
        logger.debug("Printing stats")

        commits_authors = [c.author for c in
                           list(itertools.chain.from_iterable(self.commits_db.values()))]
        counter = Counter(commits_authors)
        top_n = counter.most_common(self.stat_number)
        if top_n:
            print("Top {} committers:".format(self.stat_number))
            for idx, info in enumerate(top_n):
                print("{}. {}: {}".format(idx+1, info[0], info[1]))

    def run(self):
        """
        Githeat execution logic

        """
        self.parse_commits()
        self.compute_daily_contribution_map()
        self.normalize_daily_contribution_map()

        if self.gtype == 'inline':
            self.print_inline()
        else:
            self.print_graph()

        if self.stat:
            print()
            self.print_stats()
