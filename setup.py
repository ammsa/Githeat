""" Setup script for the githeat application.

"""
from distutils import log
from itertools import chain
from os import walk
from os.path import join
from subprocess import check_call
from subprocess import CalledProcessError

from setuptools import Command
from setuptools import find_packages
from setuptools import setup


def _listdir(root):
    """ Recursively list all files under 'root'.

    """
    for path, _, names in walk(root):
        yield path, tuple(join(path, name) for name in names)
    return


_DATA = "etc/",

_CONFIG = {
    "name": "githeat",
    "author": "Mustafa Abualsaud",
    "author_email": "mabualsaud@outlook.com",
    "url": "",
    "package_dir": {"": "lib"},
    "packages": find_packages("lib"),
    "entry_points": {
        "console_scripts": ["githeat = githeat:main",
                            "githeat.interactive = githeat.interactive:main",
                            ],
    },
    "install_requires": [
        "blessed",
        "gitdb",
        "githeat",
        "GitPython",
        "py",
        "pytest",
        "python-dateutil",
        "pytz",
        "PyYAML",
        "six",
        "smmap",
        "wcwidth",
        "wheel",
        "xtermcolor",
    ],
    "data_files": list(chain.from_iterable(_listdir(root) for root in _DATA))

}


def version():
    """ Get the local package version.

    """
    path = join("lib", _CONFIG["name"], "__version__.py")
    with open(path) as stream:
        exec(stream.read())
    return __version__


class _CustomCommand(Command):
    """ Abstract base class for a custom setup command.

    """
    # Each user option is a tuple consisting of the option's long name (ending
    # with "=" if it accepts an argument), its single-character alias, and a
    # description.
    description = ""
    user_options = []  # this must be a list

    def initialize_options(self):
        """ Set the default values for all user options.

        """
        return

    def finalize_options(self):
        """ Set final values for all user options.

        This is run after all other option assignments have been completed
        (e.g. command-line options, other commands, etc.)

        """
        return

    def run(self):
        """ Execute the command.

        Raise SystemExit to indicate failure.

        """
        raise NotImplementedError


class UpdateCommand(_CustomCommand):
    """ Custom setup command to pull from a remote branch.

    """
    description = "update from a remote branch"
    user_options = [
        ("remote=", "r", "remote name [default: tracking remote]"),
        ("branch=", "b", "branch name [default: tracking branch]"),
    ]

    def initialize_options(self):
        """ Set the default values for all user options.

        """
        self.remote = ""  # default to tracking remote
        self.branch = ""  # default to tracking branch
        return

    def run(self):
        """ Execute the command.

        """
        args = {"remote": self.remote, "branch": self.branch}
        cmdl = "git pull --ff-only {remote:s} {branch:s}".format(**args)
        try:
            check_call(cmdl.split())
        except CalledProcessError:
            raise SystemExit(1)
        log.info("package version is now {:s}".format(version()))
        return


class VirtualenvCommand(_CustomCommand):
    """ Custom setup command to create a virtualenv environment.

    """
    description = "create a virtualenv environment"
    user_options = [
        ("name=", "m", "environment name [default: venv]"),
        ("python=", "p", "Python interpreter"),
        ("requirements=", "r", "pip requirements file"),
    ]

    def initialize_options(self):
        """ Set the default values for all user options.

        """
        self.name = "venv"
        self.python = None  # default to version used to install virtualenv
        self.requirements = None
        return

    def run(self):
        """ Execute the command.

        """
        venv = "virtualenv {:s}"
        if self.python:
            venv += " -p {:s}"
        pip = "{0:s}/bin/pip install -r {2:s}" if self.requirements else None
        args = self.name, self.python, self.requirements
        try:
            check_call(venv.format(*args).split())
            if pip:
                log.info("installing requirements")
                check_call(pip.format(*args).split())
        except CalledProcessError:
            raise SystemExit(1)
        return


def main():
    """ Execute the setup commands.

    """
    _CONFIG["version"] = version()
    _CONFIG["cmdclass"] = {
        "virtualenv": VirtualenvCommand,
        "update": UpdateCommand,
    }
    setup(**_CONFIG)
    return 0


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
