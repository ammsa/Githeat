""" Implementation of the command line interface.

"""
from __future__ import absolute_import
from __future__ import print_function

from argparse import ArgumentParser
from argparse import ArgumentTypeError
from dateutil.parser import parse as parse_date
import re

from . import __version__
from .core import config
from .core import logger


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

    parser = ArgumentParser(description='githeat: Terminal Heatmap for your git repos')

    parser.add_argument('--type', action="store",
                        choices=['inline', 'block'],
                        help='Choose how you want the graph to be displayed',
                        default='block')

    parser.add_argument('--width', action="store",
                        choices=['thick', 'reg', 'thin'],
                        help='Choose how wide you want the graph blocks to be',
                        default='reg')

    parser.add_argument('--days', action='store',
                        type=str,
                        dest='days',
                        nargs='+',
                        help="Choose what day to show. Please enter day abbreviation")

    parser.add_argument('--color',
                        choices=['grass', 'fire', 'sky'],
                        help='Choose how wide you want the graph blocks to be',
                        default='grass')

    parser.add_argument('--number', dest='number',
                        type=_check_negative,
                        help='Number of top committers to show in stat')

    parser.add_argument('--stat', '-s', dest='stat',
                        action='store_true',
                        help='Show commits stat',
                        default=False)

    parser.add_argument('--block', '-b', dest='block',
                        action='store_true',
                        help='Separate each day',
                        default=False)

    parser.add_argument('--merge',
                        dest='merge',
                        action='store_true',
                        help='Separate each month',
                        default=False)

    parser.add_argument('--author', '-a',
                        help='Filter heatmap by author. You can also write regex here')

    parser.add_argument("-c", "--config", action="append",
                        help="config file [etc/config.yml]")

    parser.add_argument("-v", "--version", action="version",
                        version="githeat {:s}".format(__version__),
                        help="print version and exit")

    parser.add_argument("--warn", default="WARNING",
                        help="logger warning level [WARNING]")

    args = parser.parse_args(argv)

    if args.days:
        args.days = _is_valid_days_list(args.days)

    if not args.config:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config = ["etc/config.yml"]
    return args


def main(argv=None):
    """ Execute the application CLI.

    Arguments are taken from sys.argv by default.

    """
    args = _cmdline(argv)
    logger.start(args.warn)
    logger.info("starting execution")
    config.load(args.config)
    args.command(**vars(args))
    logger.info("successful completion")
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
