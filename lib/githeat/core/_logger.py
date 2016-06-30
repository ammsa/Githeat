""" Global application logging.

All modules use the same global logging object. No messages will be emitted
until the logger is started.

"""
from __future__ import absolute_import

from logging import getLogger
from logging import Formatter
from logging import Logger
from logging import NullHandler
from logging import StreamHandler


__all__ = "logger",


class _Logger(Logger):
    """ Log messages to STDERR.

    """
    LOGFMT = "%(asctime)s;%(levelname)s;%(name)s;%(msg)s"

    def __init__(self, name=None):
        """ Initialize this logger.

        The name defaults to the application name. Loggers with the same name
        refer to the same underlying object. Names are hierarchical, e.g.
        'parent.child' defines a logger that is a descendant of 'parent'.

        """
        super(_Logger, self).__init__(name or __name__.split(".")[0])
        self.addHandler(NullHandler())  # default to no output
        self.active = False
        return

    def start(self, level="WARN"):
        """ Start logging with this logger.

        Until the logger is started, no messages will be emitted. This applies
        to all loggers with the same name and any child loggers.

        Messages less than the given priority level will be ignored. The
        default level is 'WARN', which conforms to the *nix convention that a
        successful run should produce no diagnostic output. Available levels
        and their suggested meanings:

          DEBUG - output useful for developers
          INFO - trace normal program flow, especially external interactions
          WARN - an abnormal condition was detected that might need attention
          ERROR - an error was detected but execution continued
          CRITICAL - an error was detected and execution was halted

        """
        if self.active:
            return
        handler = StreamHandler()  # stderr
        handler.setFormatter(Formatter(self.LOGFMT))
        self.addHandler(handler)
        self.setLevel(level.upper())
        self.active = True
        return

    def stop(self):
        """ Stop logging with this logger.

        """
        if not self.active:
            return
        self.removeHandler(self.handlers[-1])
        self.active = False
        return


logger = _Logger()
