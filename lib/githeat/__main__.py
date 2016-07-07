""" Main application entry point.

    python -m githeat  ...

"""
from __future__ import absolute_import
from __future__ import print_function

from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import RawDescriptionHelpFormatter
from dateutil.parser import parse as parse_date
from git import Git
from git.exc import GitCommandError
from git.exc import GitCommandNotFound
from git.exc import InvalidGitRepositoryError
import re
import os

from . import __version__
from .core import config
from .core import logger

from .githeat import Githeat


DAY_REGEX = r"(?i)^(Sun|Mon|(T(ues|hurs))|Fri)(day|\.)" \
            r"?$|Wed(\.|nesday)?$|Sat(\.|urday)?$|T((ue?)|(hu?r?))\.?$"


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
                            description='githeat: Terminal Heatmap for your git repos',
                            parents=[conf_parser])

    parser.set_defaults(**defaults)

    parser.add_argument('--gtype',
                        action="store",
                        choices=['inline', 'block'],
                        help='Choose how you want the graph to be displayed')

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
                             "abbreviations or full name of week")

    parser.add_argument('--color',
                        choices=['grass', 'fire', 'sky'],
                        help='Choose type of coloring you want for your graph')

    parser.add_argument('--stat-number',
                        dest='stat_number',
                        type=_check_negative,
                        help='Number of top committers to show in stat')

    parser.add_argument('--stat', '-s',
                        dest='stat',
                        action='store_true',
                        help='Show commits stat')

    parser.add_argument('--separate', '-b',
                        dest='separate',
                        action='store_true',
                        help='Separate each day')

    parser.add_argument('--month-merge',
                        dest='month_merge',
                        action='store_true',
                        help='Separate each month')

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


def main(argv=None):
    """ Execute the application.

    Arguments are taken from sys.argv by default.

    """
    args = _cmdline(argv)
    logger.start(args.logging_level)
    logger.info("executing githeat")

    try:
        g = Git(os.getcwd())
        githeat = Githeat(g, **vars(args))
        githeat.run()

    except (InvalidGitRepositoryError, GitCommandError, GitCommandNotFound):
        print('Are you sure your in an initialized git directory?')

    logger.info("successful completion")
    return 0

# Make it executable.

if __name__ == "__main__":
    try:
        status = main()
    except:
        logger.critical("shutting down due to fatal error")
        raise  # print stack trace
    else:
        raise SystemExit(status)
