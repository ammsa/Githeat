""" Test suite for the interactive module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the module is actually
being tested. If the library is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
import os
from subprocess import call
from sys import executable

import functools
import blessed

import pytest
from githeat import interactive
from xtermcolor import colorize

TEST_TERMINAL = functools.partial(blessed.Terminal, kind='xterm-256color')


@pytest.fixture(params=" ")
def command(request):
    """ Return the command to run.

    """
    return request.param

@pytest.fixture
def patch_terminal(monkeypatch):

    class test_terminal:
        class mydatetime:
            @classmethod
            def Terminal(cls):
                return TEST_TERMINAL

    monkeypatch.setattr(blessed, 'Terminal', test_terminal)


@pytest.fixture()
def patch_terminal_size(monkeypatch):
    term_width = '250'
    term_height = '60'
    monkeypatch.setitem(os.environ, 'COLUMNS', term_width)
    monkeypatch.setitem(os.environ, 'LINES', term_height)


def test_main(command):
    """ Test the main() function.

    """
    # Call with the --help option as a basic sanity check.
    with pytest.raises(SystemExit) as exinfo:
        interactive.main(("{:s}".format(command), "--help"))
    assert 0 == exinfo.value.code
    return


def test_script(command):
    """ Test command line execution.

    """
    # Call with the --help option as a basic sanity check.
    cmdl = "{:s} -m githeat.interactive --help".format(executable)
    assert 0 == call(cmdl.split())
    return


def test_print_left_header(patch_terminal_size):

    term = TEST_TERMINAL()
    with term.cbreak():
        inp = term.inkey(timeout=0.0001)
        screen = {}
        interactive.print_header_left(term, "left header", screen)
        assert len(screen) == 1
        assert screen[0, 0] == "left header"


def test_print_center_header(patch_terminal_size):

    term = TEST_TERMINAL()
    with term.cbreak():
        screen = {}
        text = "center header"
        interactive.print_header_center(term, text, screen)
        assert len(screen) == 1
        x = (term.width // 2) - len(text) // 2
        assert screen[0, x] == text


def test_print_right_header(patch_terminal_size):

    term = TEST_TERMINAL()
    with term.cbreak():
        screen = {}
        text = "right header"
        interactive.print_header_right(term, text, screen)
        assert len(screen) == 1
        x = term.width - len(text)
        print(screen)
        print(x)
        assert screen[0, x] == text


def test_print_footer_left(patch_terminal_size):
    term = TEST_TERMINAL()
    with term.cbreak():
        screen = {}
        text = "footer left"
        interactive.print_footer_left(term, text, screen)
        assert len(screen) == 1
        assert screen[term.height - 1, 0] == text


def test_top_authors_to_string():
    authors = [("John", 4), ("Jason", 3), ("James", 2), ("Jordon", 2), ("J", 0)]
    assert interactive.top_authors_to_string(authors) == "John, Jason, James, Jordon, J"


def test_top_authors_to_string_colorized():
    ansii_colors = [1, 2, 3, 4, 5]
    authors = [("John", 4), ("Jason", 3), ("James", 2), ("Jordon", 2), ("J", 0)]
    colored = []
    for tup in authors:
        colored.append(colorize(tup[0], ansi=ansii_colors[tup[1]]))
    colored = ", ".join(colored)
    assert interactive.top_authors_to_string(authors, colors=ansii_colors) == colored


def test_print_graph_legend(patch_terminal_size):
    term = TEST_TERMINAL()
    with term.cbreak():
        screen = {}
        colors = [1, 2, 3, 4, 5]
        block_width = "  "
        interactive.print_graph_legend(0, 0, block_width, 4, colors, screen, term)
        result = {(0, 16): block_width,
                  (0, 12): block_width,
                  (0, 8): block_width,
                  (0, 4): block_width,
                  (0, 0): block_width}
        assert screen == result


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main(__file__))
