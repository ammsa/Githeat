""" Implementation of interactive githeat.

"""
from __future__ import absolute_import
from __future__ import print_function

import collections
from argparse import ArgumentParser
from argparse import ArgumentTypeError

import functools
from git import Git

from blessed import Terminal
from dateutil.parser import parse as parse_date
import re
from xtermcolor import colorize
import os

from . import __version__
from .core import config
from .core import logger
from .githeat import Githeat

__all__ = "main",

DAY_REGEX = r"(?i)^(Sun|Mon|(T(ues|hurs))|Fri)(day|\.)" \
            r"?$|Wed(\.|nesday)?$|Sat(\.|urday)?$|T((ue?)|(hu?r?))\.?$"


def _cmdline(argv=None):
    """ Parse command line arguments.

    """

    def _check_negative(value):
        ivalue = int(value)
        if ivalue < 0:
            raise ArgumentTypeError("%s: invalid positive int value" % value)
        return ivalue

    def _is_valid_days_list(days):
        try:
            if 7 < len(days) < 1:
                raise ArgumentTypeError("Please enter a list of 7 days or less")
            for idx, day in enumerate(days):
                day = re.match(DAY_REGEX, day).group(0).title()

                if len(day) <= 3:
                    day = parse_date(day).strftime("%A")
                days[idx] = day
            return list(set(days))
        except Exception as e:
            raise ArgumentTypeError("String '%s' does not match required "
                                    "format: day abbreviation" % (days,))

    parser = ArgumentParser(prog="githeat.py",
                            description='githeat: Terminal Heatmap for your git repos')

    parser.add_argument('--gtype',
                        action="store",
                        choices=['inline', 'block'],
                        help='Choose how you want the graph to be displayed',
                        default='block')

    parser.add_argument('--width',
                        action="store",
                        choices=['thick', 'reg', 'thin'],
                        help='Choose how wide you want the graph blocks to be',
                        default='reg')

    parser.add_argument('--days',
                        action='store',
                        type=str,
                        dest='days',
                        nargs='+',
                        help="Choose what days to show. Please enter list of day "
                             "abbreviations or full name of week")

    parser.add_argument('--color',
                        choices=['grass', 'fire', 'sky'],
                        help='Choose type of coloring you want for your graph',
                        default='grass')

    parser.add_argument('--stat-number',
                        dest='stat_number',
                        type=_check_negative,
                        help='Number of top committers to show in stat')

    parser.add_argument('--stat', '-s',
                        dest='stat',
                        action='store_true',
                        help='Show commits stat',
                        default=False)

    parser.add_argument('--separate', '-b',
                        dest='separate',
                        action='store_true',
                        help='Separate each day',
                        default=False)

    parser.add_argument('--month-merge',
                        dest='month_merge',
                        action='store_false',
                        help='Separate each month',
                        default=True)

    parser.add_argument('--author', '-a',
                        help='Filter heatmap by author. You can also write regex here')

    parser.add_argument("-c", "--config",
                        action="append",
                        help="config file [etc/config.yml]")

    parser.add_argument("-v", "--version",
                        action="version",
                        version="githeat {:s}".format(__version__),
                        help="print version and exit")

    parser.add_argument("--logging",
                        dest="logging_level",
                        default="CRITICAL",
                        choices=['CRITICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG', 'NOTSET'],
                        help="logger level")

    args = parser.parse_args(argv)

    if args.days:
        args.days = _is_valid_days_list(args.days)

    if not args.config:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config = ["etc/config.yml"]
    return args


# python 2/3 compatibility, provide 'echo' function as an
# alias for "print without newline and flush"

try:
    # pylint: disable=invalid-name
    #         Invalid constant name "echo"
    echo = functools.partial(print, end='', flush=True)
    echo(u'')
except TypeError:
    # TypeError: 'flush' is an invalid keyword argument for this function
    import sys


    def echo(text):
        """Display ``text`` and flush output."""
        sys.stdout.write(u'{}'.format(text))
        sys.stdout.flush()

#
# def input_filter(keystroke):
#     """
#     For given keystroke, return whether it should be allowed as input.
#
#     This somewhat requires that the interface use special
#     application keys to perform functions, as alphanumeric
#     input intended for persisting could otherwise be interpreted as a
#     command sequence.
#     """
#     if keystroke.is_sequence:
#         # Namely, deny multi-byte sequences (such as '\x1b[A'),
#         return False
#     if ord(keystroke) < ord(u' '):
#         # or control characters (such as ^L),
#         return False
#     return True


def echo_yx(cursor, text):
    """Move to ``cursor`` and display ``text``."""
    echo(cursor.term.move(cursor.y, cursor.x) + text)


Cursor = collections.namedtuple('Cursor', ('y', 'x', 'term'))


# def readline(term, width=20):
#     """A rudimentary readline implementation."""
#     text = u''
#     while True:
#         inp = term.inkey()
#         if inp.code == term.KEY_ENTER:
#             break
#         elif inp.code == term.KEY_ESCAPE or inp == chr(3):
#             text = None
#             break
#         elif not inp.is_sequence and len(text) < width:
#             text += inp
#             echo(inp)
#         elif inp.code in (term.KEY_BACKSPACE, term.KEY_DELETE):
#             text = text[:-1]
#             echo(u'\b \b')
#     return text


# def save(screen, fname):
#     """Save screen contents to file."""
#     if not fname:
#         return
#     with open(fname, 'w') as fout:
#         cur_row = cur_col = 0
#         for (row, col) in sorted(screen):
#             char = screen[(row, col)]
#             while row != cur_row:
#                 cur_row += 1
#                 cur_col = 0
#                 fout.write(u'\n')
#             while col > cur_col:
#                 cur_col += 1
#                 fout.write(u' ')
#             fout.write(char)
#             cur_col += 1
#         fout.write(u'\n')


def redraw(term, screen, start=None, end=None):
    """Redraw the screen."""
    if start is None and end is None:
        echo(term.clear)
        start, end = (Cursor(y=min([y for (y, x) in screen or [(0, 0)]]),
                             x=min([x for (y, x) in screen or [(0, 0)]]),
                             term=term),
                      Cursor(y=max([y for (y, x) in screen or [(0, 0)]]),
                             x=max([x for (y, x) in screen or [(0, 0)]]),
                             term=term))
    lastcol, lastrow = -1, -1
    for row, col in sorted(screen):
        if start.y <= row <= end.y and start.x <= col <= end.x:
            if col >= term.width or row >= term.height:
                # out of bounds
                continue
            if not (row == lastrow and col == lastcol + 1):
                # use cursor movement
                echo_yx(Cursor(row, col, term), screen[row, col])
            else:
                # just write past last one
                echo(screen[row, col])


def within_boundary(boundary_right_most_x, boundary_top_most_y,
                    boundary_left_most_x, boundary_bottom_most_y,
                    cursor):
    """
    Checks if cursor is within given boundary

    :param boundary_right_most_x:
    :param boundary_top_most_y:
    :param boundary_left_most_x:
    :param boundary_bottom_most_y:
    :param cursor:
    :return: boolean
    """

    if cursor.y < boundary_top_most_y:
        return False
    elif cursor.y > boundary_bottom_most_y:
        return False
    elif cursor.x < boundary_left_most_x:
        return False
    elif cursor.x > boundary_right_most_x:
        return False

    return True


def main(argv=None):
    """ Execute the application CLI.

    Arguments are taken from sys.argv by default.

    """
    args = _cmdline(argv)
    logger.start(args.logging_level)
    logger.info("starting execution")
    config.load(args.config)
    logger.info("successful completion")

    """Program entry point."""
    above = lambda csr, n: (
        Cursor(y=max(0, csr.y - n),
               x=csr.x,
               term=csr.term))

    below = lambda csr, n: (
        Cursor(y=min(csr.term.height - 1, csr.y + n),
               x=csr.x,
               term=csr.term))

    right_of = lambda csr, n: (
        Cursor(y=csr.y,
               x=min(csr.term.width - 1, csr.x + n),
               term=csr.term))

    left_of = lambda csr, n: (
        Cursor(y=csr.y,
               x=max(0, csr.x - n),
               term=csr.term))

    home = lambda csr: (
        Cursor(y=csr.y,
               x=0,
               term=csr.term))

    end = lambda csr: (
        Cursor(y=csr.y,
               x=csr.term.width - 1,
               term=csr.term))

    bottom = lambda csr: (
        Cursor(y=csr.term.height - 1,
               x=csr.x,
               term=csr.term))

    center = lambda csr: Cursor(
            csr.term.height // 2,
            csr.term.width // 2,
            csr.term)

    lookup_move = lambda inp_code, csr, term: {
        # arrows, including angled directionals
        csr.term.KEY_END: below(left_of(csr, 1), 1),
        csr.term.KEY_KP_1: below(left_of(csr, 1), 1),

        csr.term.KEY_DOWN: below(csr, 1),
        csr.term.KEY_KP_2: below(csr, 1),

        csr.term.KEY_PGDOWN: below(right_of(csr, 1), 1),
        csr.term.KEY_LR: below(right_of(csr, 1), 1),
        csr.term.KEY_KP_3: below(right_of(csr, 1), 1),

        csr.term.KEY_LEFT: left_of(csr, 2),
        csr.term.KEY_KP_4: left_of(csr, 2),

        csr.term.KEY_CENTER: center(csr),
        csr.term.KEY_KP_5: center(csr),

        csr.term.KEY_RIGHT: right_of(csr, 2),
        csr.term.KEY_KP_6: right_of(csr, 2),

        csr.term.KEY_HOME: above(left_of(csr, 1), 1),
        csr.term.KEY_KP_7: above(left_of(csr, 1), 1),

        csr.term.KEY_UP: above(csr, 1),
        csr.term.KEY_KP_8: above(csr, 1),

        csr.term.KEY_PGUP: above(right_of(csr, 1), 1),
        csr.term.KEY_KP_9: above(right_of(csr, 1), 1),

        # shift + arrows
        csr.term.KEY_SLEFT: left_of(csr, 10),
        csr.term.KEY_SRIGHT: right_of(csr, 10),
        csr.term.KEY_SDOWN: below(csr, 10),
        csr.term.KEY_SUP: above(csr, 10),

        # carriage return
        csr.term.KEY_ENTER: home(below(csr, 1)),
    }.get(inp_code, csr)

    #  get repo
    g = Git("/Users/mustafa/Repos/tensorflow")
    githeat = Githeat(g, **vars(args))
    githeat.parse_commits()
    githeat.compute_daily_contribution_map()
    githeat.normalize_daily_contribution_map()
    matrix = githeat.get_graph_matrix()

    term = Terminal()
    csr = Cursor(term.height // 2, term.width // 2, term)
    new_width = (term.width - len(matrix) * 2) // 2
    csr = Cursor(term.height // 2 - 3, new_width, term)

    screen = {}
    screen_dates = {}
    with term.hidden_cursor(), \
         term.raw(), \
         term.location(), \
         term.fullscreen(), \
         term.keypad():

        # inp = None

        graph_right_most_x = term.width  # initialized at terminal width
        graph_left_most_x = csr.x
        graph_bottom_most_y = term.height  # initialized at terminal height
        graph_top_most_y = csr.y

        x = csr.x
        y = csr.y

        #  for each day of the week
        for i in range(7):
            #  for the week column in the matrix
            for week in matrix:

                if not githeat.month_merge:
                    #  check if value in that week is just empty spaces and not colorize
                    if week.col[i][1] == githeat.width:
                        continue
                c = Cursor(y, x, term)
                value = "{}".format(week.col[i][1])
                if value == '  ':
                    pass
                else:
                    value = week.col[i][1]
                    screen[(c.y, c.x)] = value
                    screen_dates[(c.y, c.x)] = week.col[i][0]

                echo_yx(c, value)

                x += 2

            graph_right_most_x = x - 2
            #  reset x
            x = graph_left_most_x
            y += 1
        graph_bottom_most_y = y - 1

        while True:
            c = colorize("  ", ansi=15, ansi_bg=15)
            echo_yx(csr, c)
            inp = term.inkey()

            if inp == chr(3):
                # ^c exits
                break

            # elif inp == chr(19):
            #     # ^s saves
            #     echo_yx(home(bottom(csr)),
            #             term.ljust(term.bold_white(u'Filename: ')))
            #     echo_yx(right_of(home(bottom(csr)), len(u'Filename: ')), u'')
            #     save(screen, readline(term))
            #     echo_yx(home(bottom(csr)), term.clear_eol)
            #     redraw(term=term, screen=screen,
            #            start=home(bottom(csr)),
            #            end=end(bottom(csr)))
            #     continue

            # elif inp == chr(12):
            #     # ^l refreshes
            #     redraw(term=term, screen=screen)

            else:
                n_csr = lookup_move(inp.code, csr, term)

            # check if cursor new move is within our graph boundaries
            if not within_boundary(graph_right_most_x, graph_top_most_y,
                                   graph_left_most_x, graph_bottom_most_y,
                                   n_csr):
                continue

            # get value at new cursor block, if it exists
            next_value = screen_dates.get((n_csr.y, n_csr.x))
            if next_value:
                # Cursor is on a date with commits
                echo_yx(home(bottom(csr)),
                        term.ljust(term.bold_white(unicode(next_value))))
                echo_yx(right_of(home(bottom(csr)), len(unicode(next_value))), u'')
            else:
                echo_yx(home(bottom(csr)), term.clear_eol)
                redraw(term=term, screen=screen,
                       start=home(bottom(csr)),
                       end=end(bottom(csr)))

                horizontal_empty = False
                while not next_value and within_boundary(graph_right_most_x,
                                                         graph_top_most_y,
                                                         graph_left_most_x,
                                                         graph_bottom_most_y,
                                                         n_csr):
                    x = n_csr.x
                    y = n_csr.y
                    if n_csr.x > csr.x:
                        x += 1
                    elif n_csr.x < csr.x:
                        x -= 1
                    else:
                        horizontal_empty = True
                        break
                    n_csr = Cursor(y, x, term)
                    next_value = screen_dates.get((n_csr.y, n_csr.x))
                if horizontal_empty:
                    continue

            if n_csr != csr:
                # erase old cursor,
                prev_value = screen.get((csr.y, csr.x), u'  ')
                echo_yx(csr, prev_value)
                csr = n_csr

            # elif input_filter(inp):
            #     echo_yx(csr, inp)
            #     screen[(csr.y, csr.x)] = inp.__str__()
            #     n_csr = right_of(csr, 1)
            #     if n_csr == csr:
            #         # wrap around margin
            #         n_csr = home(below(csr, 1))
            #     csr = n_csr

    return 0


# Make the module executable.

if __name__ == "__main__":
    try:
        status = main()
    except:
        logger.critical("shutting down due to fatal error")
        raise  # print stack trace
    else:
        raise SystemExit(status)
