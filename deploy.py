""" Deploy the githeat application.

The project will be cloned from a Git repo and installed into a self-contained
virtualenv environment. By default the repo HEAD will be deployed, but an
optional branch, tag, or commit can be specified. The deployed application will
have its own complete set of Python libraries.

The target machine must have Python 2.7, pip, and virtualenv installed.

"""
from argparse import ArgumentParser
from contextlib import contextmanager
from os import chdir
from os import getcwd
from os.path import abspath
from os.path imort isdir
from os.path import join
from shlex import split
from shutil import rmtree
from subprocess import check_call
from tempfile import mkdtemp


_NAME = "githeat"
_REPO = None  # FIXME: specify the default Git repo to use


def _cmdline(argv=None):
    """ Parse command line arguments.

    By default, sys.argv is parsed.

    """
    parser = ArgumentParser()
    parser.add_argument("--checkout", default="HEAD",
                        help="branch, tag, or commit to use [HEAD]")
    parser.add_argument("--name", default=_NAME,
                        help="application name [{:s}]".format(_NAME))
    parser.add_argument("--repo", default=_REPO,
                        help="source repo [{:s}]".format(_REPO))
    parser.add_argument("--test", action="store_true",
                        help="run test suite after installation")
    parser.add_argument("root", help="installation root")
    return parser.parse_args(argv)


def main(argv=None):
    """ Script execution.

    The project repo will be cloned to a temporary directory, and the desired
    branch, tag, or commit will be checked out. Then, the application will be
    installed into a self-contained virtualenv environment.

    """
    @contextmanager
    def tmpdir():
        """ Enter a self-deleting temporary directory. """
        cwd = getcwd()
        tmp = mkdtemp()
        try:
            chdir(tmp)
            yield tmp
        finally:
            rmtree(tmp)
            chdir(cwd)
        return

    def test():
        """ Execute the test suite. """
        install = "{:s} install -r requirements-test.txt".format(pip)
        check_call(split(install))
        python = join(path, "bin", "python")
        test = "{:s} -m pytest test".format(python)
        check_call(test.split())
        uninstall = "{:s} uninstall -y -r requirements-test.txt".format(pip)
        check_call(split(uninstall))
        return

    args = _cmdline(argv)
    path = join(abspath(args.root), args.name)
    repo = abspath(args.repo) if isdir(args.repo) else args.repo
    with tmpdir():
        clone = "git clone {:s} {:s}".format(repo, _NAME)
        check_call(split(clone))
        chdir(_NAME)
        checkout = "git checkout {:s}".format(args.checkout)
        check_call(split(checkout))
        virtualenv = "virtualenv {:s}".format(path)
        check_call(split(virtualenv))
        pip = join(path, "bin", "pip")
        install = "{:s} install -U -r requirements.txt .".format(pip)
        check_call(split(install))
        if args.test:
            test()
    return 0


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
