#!/usr/bin/env python
""" Implementation of interactive githeat.

"""
from __future__ import absolute_import
from __future__ import print_function
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import RawDescriptionHelpFormatter
from blessed import Terminal
from dateutil.parser import parse as parse_date
import functools
from git import Git
import re
import os
from xtermcolor import colorize
from . import __version__
from .core import config
from .core import logger
from .util.interactive_navigation import Cursor
from .util import interactive_navigation as nav
from .githeat import Githeat

__all__ = "main",

DAY_REGEX = r"(?i)^(Sun|Mon|(T(ues|hurs))|Fri)(day|\.)" \
            r"?$|Wed(\.|nesday)?$|Sat(\.|urday)?$|T((ue?)|(hu?r?))\.?$"

ONE_TO_SEVEN_KEYS = [chr(number) for number in range(49, 56)]  # 1 to 7
Q_TO_QUOTES_KEYS = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\", "'"]
QUIT_KEYS = [chr(27), chr(3)]  # esc, ^c keys


def _cmdline(argv=None):
    """ Parse command line arguments.

    """

    conf_parser = ArgumentParser(
        description=__doc__,  # printed with -h/--help
        # Don't mess with format of description
        formatter_class=RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
    )
    conf_parser.add_argument("-c", "--config",
                             help="Specify YAML config file",
                             metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    defaults = {}
    if args.config:
        config.load([args.config])
    else:
        config.load([os.path.expanduser('~/.githeat')])
        defaults.update(config)

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
                            description='githeat: Terminal Heatmap for your git repos',
                            parents=[conf_parser])

    parser.set_defaults(**defaults)

    parser.add_argument('--width',
                        action="store",
                        choices=['thick', 'reg', 'thin'],
                        help='Choose how wide you want the graph blocks to be')

    parser.add_argument('--days',
                        action='store',
                        type=str,
                        dest='days',
                        nargs='+',
                        help="Choose what days to show. Please enter list of day "
                             "abbreviations or full name of week",
                        )

    parser.add_argument('--color',
                        choices=['grass', 'fire', 'sky'],
                        help='Choose type of coloring you want for your graph',
                        default='grass')

    parser.add_argument('--month-merge',
                        dest='month_merge',
                        action='store_true',
                        help='Separate each month')

    parser.add_argument('--hide-legend',
                        dest='legend',
                        action='store_true',
                        help="Hide legend")

    parser.add_argument('--author', '-a',
                        help='Filter heatmap by author. You can also write regex here')

    parser.add_argument('--grep', '-g',
                        help='Filter by keywords in commits')

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


def echo_yx(cursor, text):
    """Move to ``cursor`` and display ``text``."""
    echo(cursor.term.move(cursor.y, cursor.x) + text)


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


def clear(term, start, end):
    """
    Empty part of terminal, starting from start (top left) to end (bottom right)
    :param term:
    :param start:
    :param end:
    :return:
    """
    if is_within_boundary(0, 0, term.width, term.width, start) or \
            is_within_boundary(0, 0, term.width, term.width, end) or \
                    start.x > end.x or start.y > end.y:
        raise ValueError("NOT VALID ")
        return

    x = start.x
    y = start.y
    for j in range(abs(end.y - start.y)):
        for i in range(abs(end.x - start.x)):
            csr = Cursor(y, x, term)
            echo_yx(csr, " ")
            x += 1
        x = start.x
        y += 1


def top_authors_to_string(top_authors, colors=None):
    authors = []
    if top_authors:
        for tup in top_authors:
            if colors:
                author_string = colorize(tup[0], ansi=colors[int(tup[1])])
            else:
                author_string = tup[0]
            authors.append(author_string)

    top_n_authors = ", ".join(authors)
    return top_n_authors


def print_graph_legend(starting_x, y, width, block_seperation_width, colors, screen,
                       term):
    for color in colors:
        c = Cursor(y, starting_x, term)
        value = colorize(width, ansi=color, ansi_bg=color)
        echo_yx(c, value)
        screen[y, starting_x] = value
        starting_x += block_seperation_width


def is_within_boundary(boundary_right_most_x, boundary_top_most_y,
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


def print_graph(term, screen, screen_dates, x, y, graph_left_most_x, matrix, githeat):
    """
    Prints graph

    :param term:
    :param screen:
    :param screen_dates:
    :param x:
    :param y:
    :param graph_left_most_x:
    :param matrix:
    :param githeat:
    """
    #  for each day of the week
    for i in range(7):
        #  for the week column in the matrix
        for week in matrix:

            if githeat.month_merge:
                #  check if value in that week is just empty spaces and not colorize
                if week.col[i][1] == githeat.width:
                    continue

            c = Cursor(y, x, term)
            value = week.col[i][1]
            screen[(c.y, c.x)] = value
            screen_dates[(c.y, c.x)] = week.col[i][0]

            echo_yx(c, value)

            x += len(githeat.width)

        # reset x
        x = graph_left_most_x
        y += 1


def print_header_left(term, text, screen={}):
    """
    Prints text at top left of terminal

    :param term:
    :param text:
    :param screen:
    """
    header_left = text
    location = Cursor(0, 0, term)
    value = term.bold(header_left)
    echo_yx(location, value)
    screen[location.y, location.x] = value


def print_header_center(term, text, screen={}):
    """
    Prints text at center top of terminal

    :param term:
    :param text:
    :param screen:
    """
    location = Cursor(0, (term.width // 2) - len(text) // 2, term)
    value = term.bold(text)
    echo_yx(location, value)
    screen[location.y, location.x] = value


def print_header_right(term, text, screen={}):
    """
    Prints text at top right of terminal

    :param term:
    :param text:
    :param screen:
    """
    location = Cursor(0, term.width - len(text), term)
    value = term.bold(text)
    echo_yx(location, value)
    screen[location.y, location.x] = value


def print_footer_left(term, text, screen={}):
    """
    Prints text at bottom left of terminal

    :param term:
    :param text:
    :param screen:
    :return:
    """
    location = Cursor(term.height - 1, 0, term)
    value = text
    echo_yx(location, value)
    screen[location.y, location.x] = value


def resize_until_fit(texts_list, width):
    """
    Removes from end of text_list such that the length of elements in text_lest fit width

    :param texts_list:
    :param width:
    :return: text_list modified to fit with width
    """

    lengths = sum([len(x) for x in texts_list])
    if lengths < width:
        return texts_list

    diff = lengths - width
    for idx, text in reversed(list(enumerate(texts_list))):
        texts_list[idx] = texts_list[idx][:-diff]
        lengths = sum([len(x) for x in texts_list])

        if lengths <= width:
            break

        diff = lengths - width

    return texts_list


def open_commits_terminal(new_cursor_date_value, commits_on_date):
    """
    Creates a new terminal window for showing commits info
    :param new_cursor_date_value:
    :param commits_on_date:
    :return:
    """
    screen = {}
    term = Terminal()
    with term.keypad():
        redraw(term=term, screen={})

        # Print header
        print_header_left(term, str(new_cursor_date_value), screen)
        text = u'GitHeat {}'.format(__version__)
        print_header_center(term, text, screen)
        text = u'ESC, to return'
        print_header_right(term, text, screen)

        #  hold the commit info that we will display depending on scrolling window edges
        commit_values_holder = []
        for commit in commits_on_date:
            commit_hash, cdate, spaces, subject, author, email, = resize_until_fit(
                    [
                        commit.abbr_commit_hash,
                        str(commit.date.strftime("%H:%M:%S %z")),
                        "  ",
                        commit.subject,
                        commit.author,
                        commit.author_email,
                    ],
                    term.width - 7  # for spaces and '<', '>' between emails
            )

            value = [
                colorize(commit_hash, ansi=3),
                cdate,
                spaces,
                term.bold(subject),
                colorize(author, ansi=6),
            ]

            if email:
                value.append(colorize("<{}>".format(email), ansi=14))

            value = " ".join(value)
            commit_values_holder.append(value)

        starting_y = 2
        x = 0
        range_from = 0
        range_to = term.height - starting_y
        for value in commit_values_holder[range_from:range_to]:
            location = Cursor(starting_y, x, term)
            echo_yx(location, value)
            starting_y += 1

        while True:
            inp = term.inkey()

            if inp in chr(27):  # ESC to return
                break
            elif inp == chr(3):  # ^c to exit
                sys.exit(0)

            # scrolling window on commits
            starting_y = 2  # to not override header text
            if inp.code == term.KEY_UP:
                if range_from == 0:
                    continue
                range_from -= 1
            elif inp.code == term.KEY_DOWN:
                #  skip scrolling if commits fit terminal height
                if len(commit_values_holder[range_from:]) < term.height:
                    continue
                range_from += 1

            redraw(term=term, screen=screen)
            #  echo the commits based on scrolling window
            for value in commit_values_holder[range_from:]:
                if starting_y > term.height:
                    break
                location = Cursor(starting_y, x, term)
                echo_yx(location, value)
                starting_y += 1


def update_most_committers_footer(location, githeat, date, term, screen):
    """
    Updates footer with most commiters info

    :param location:
    :param githeat:
    :param date:
    :param term:
    :param screen:
    :return:
    """

    #  uncomment condition below to hide top authors if not in user specified days
    if not githeat.commits_db.get(date):  # or date.strftime("%A") not in githeat.days:
        msg = "No commits"
    else:
        top_n = githeat.get_top_n_commiters(
                githeat.commits_db.get(date),
                normailze_values=True,
                n=5
        )

        names = top_authors_to_string(top_n, colors=githeat.colors)
        msg = "{} {}".format(term.bold_white("Most committers:"), names)

    footer = " ".join([term.bold_white(unicode(date)), msg])
    value = term.ljust(footer)
    print_footer_left(term, value, screen)


def main(argv=None):
    """ Execute the application CLI.

    Arguments are taken from sys.argv by default.

    """

    args = _cmdline(argv)
    logger.start(args.logging_level)
    logger.debug("starting execution")

    #  get repo and initialize GitHeat instance
    g = Git(os.getcwd())
    githeat = Githeat(g, **vars(args))
    githeat.parse_commits()
    githeat.init_daily_contribution_map()
    githeat.compute_daily_contribution_map()
    githeat.normalize_daily_contribution_map()
    matrix = githeat.compute_graph_matrix()

    term = Terminal()
    matrix_width = githeat.get_matrix_width(matrix)
    if matrix_width > term.width:
        print("Your terminal width is smaller than the heatmap. Please consider using "
              "the --width {thin, reg, thick} argument, resizing your terminal, or "
              "merging months by including --month-merge.")
        return 0
    new_width = (term.width - matrix_width) // 2
    csr = Cursor(term.height // 2 - 3, new_width, term)

    screen = {}
    screen_dates = {}
    with term.hidden_cursor(), \
         term.raw(), \
         term.location(), \
         term.fullscreen(), \
         term.keypad():

        # Print header
        print_header_left(term, unicode(os.getcwd()), screen)
        text = u'GitHeat {}'.format(__version__)
        print_header_center(term, text, screen)
        text = u'ESC, ^c to exit'
        print_header_right(term, text, screen)

        # Print footer
        text = u'Please move cursor to navigate through map'
        print_footer_left(term, term.bold(text), screen)

        graph_right_most_x = term.width  # initialized at terminal width
        graph_left_most_x = csr.x
        graph_top_most_y = csr.y
        graph_x, graph_y = csr.x, csr.y

        #  get graph boundaries
        for i in range(7):
            #  for the week column in the matrix
            for week in matrix:
                if githeat.month_merge:
                    #  check if value in that week is just empty spaces and not colorize
                    if week.col[i][1] == githeat.width:
                        continue
                graph_x += len(githeat.width)

            graph_right_most_x = graph_x
            graph_x = graph_left_most_x  # reset x
            graph_y += 1
        graph_bottom_most_y = graph_y - 1

        #  print graph
        graph_x, graph_y = csr.x, csr.y
        print_graph(term, screen, screen_dates, graph_x, graph_y,
                    graph_left_most_x, matrix, githeat)

        # print legend
        block_separation_width = 4
        legend_x = (term.width - len(githeat.colors) * block_separation_width) // 2
        legend_y = graph_bottom_most_y + 5
        if not githeat.hide_legend:
            print_graph_legend(legend_x, legend_y,
                               githeat.width,
                               block_separation_width,
                               githeat.colors,
                               screen,
                               term)

        while True:
            cursor_color = colorize(githeat.width, ansi=15, ansi_bg=15)
            echo_yx(csr, cursor_color)
            inp = term.inkey()

            if inp in QUIT_KEYS:
                # Esc or ^c pressed
                break
            elif inp == chr(99):
                # c pressed, thus change color
                githeat.switch_to_next_color()
                #  changing colors requires regenerating matrix,
                #  because values there are colorized strings, harder to change
                matrix = githeat.compute_graph_matrix()
                #  print changed color graph
                print_graph(term, screen, screen_dates, graph_x, graph_y,
                            graph_left_most_x, matrix, githeat)

                #  print changed color legend
                if not githeat.hide_legend:
                    print_graph_legend(legend_x, legend_y,
                                       githeat.width,
                                       block_separation_width,
                                       githeat.colors,
                                       screen,
                                       term)

                #  print changed color footer
                new_cursor_date_value = screen_dates.get((csr.y, csr.x))
                if new_cursor_date_value:  # only if it needs changing
                    location = nav.home(nav.bottom(csr))
                    update_most_committers_footer(location, githeat,
                                                  new_cursor_date_value, term, screen)
                continue
            elif inp.lower() in ONE_TO_SEVEN_KEYS or inp in Q_TO_QUOTES_KEYS:
                if inp.lower() in ONE_TO_SEVEN_KEYS:
                    #  key from 1 to 7 pressed.
                    githeat.toggle_day(int(inp) - 1)
                else:
                    # key from q to ' pressed
                    githeat.toggle_month(Q_TO_QUOTES_KEYS.index(inp.lower()))

                # re-computing new daily contributions with the specified days/months
                githeat.recompute_daily_contribution_map()
                matrix = githeat.compute_graph_matrix()
                #  print new filtered graph
                print_graph(term, screen, screen_dates, graph_x, graph_y,
                            graph_left_most_x, matrix, githeat)

                continue

            else:
                n_csr = nav.lookup_move(inp.code, csr, term, githeat)

            # only allow moves within the graph boundaries
            if not is_within_boundary(graph_right_most_x, graph_top_most_y,
                                  graph_left_most_x, graph_bottom_most_y,
                                  n_csr):
                continue

            # get value at new cursor block, if it exists
            new_cursor_date_value = screen_dates.get((n_csr.y, n_csr.x))
            if new_cursor_date_value:  # Cursor is on a date block with commits
                location = nav.home(nav.bottom(csr))
                update_most_committers_footer(location, githeat,
                                              new_cursor_date_value, term, screen)
            else:

                horizontal_empty = False

                #  jump through empty values
                while not new_cursor_date_value and is_within_boundary(
                                graph_right_most_x - 1,
                        graph_top_most_y,
                                graph_left_most_x + 1,
                        graph_bottom_most_y,
                        n_csr):

                    x = n_csr.x
                    y = n_csr.y
                    if n_csr.x > csr.x:  # right move
                        x += 1
                    elif n_csr.x < csr.x:  # left move
                        x -= 1
                    else:
                        horizontal_empty = True
                        break  # skip jumping on up or down moves

                    n_csr = Cursor(y, x, term)
                    new_cursor_date_value = screen_dates.get((n_csr.y, n_csr.x))
                    if new_cursor_date_value:
                        location = nav.home(nav.bottom(csr))
                        update_most_committers_footer(location, githeat,
                                                      new_cursor_date_value, term, screen)

                if horizontal_empty or not new_cursor_date_value:
                    continue

            if n_csr != csr:
                # erase old cursor,
                prev_value = screen.get((csr.y, csr.x), u'  ')
                echo_yx(csr, prev_value)
                csr = n_csr

            if inp == chr(13):
                # ENTER pressed on date block
                commits_on_date = githeat.commits_db.get(new_cursor_date_value)

                if commits_on_date:  # if block has contributions
                    #  open commits desc terminal
                    open_commits_terminal(new_cursor_date_value, commits_on_date)
                    # redraw base terminal after exiting commits desc terminal
                    redraw(term=term, screen=screen)
                else:
                    info = u'Please choose a date with contributions'
                    text = unicode(new_cursor_date_value) + ' ' + info
                    print_footer_left(term, text, screen)

    logger.debug("successful completion")
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
