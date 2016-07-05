""" Test suite for the interactive module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the module is actually
being tested. If the library is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
import datetime
import pytest
from mock import Mock

from githeat.githeat import Githeat, Commit
from static.test_logs import test_logs

@pytest.fixture
def test_repo():

    def log(arguments):
        return test_logs

    repo = Mock(log=log)
    githeat = Githeat(repo)
    githeat.parse_commits()
    githeat.init_daily_contribution_map()
    githeat.compute_daily_contribution_map()
    githeat.normalize_daily_contribution_map()

    return githeat


def test_githeat_init(test_repo):
    assert len(test_repo.commits_db) == 367


def test_toggle_day_(test_repo):
    test_repo.toggle_day(0)
    assert test_repo.days == ["Sunday"]
    test_repo.toggle_day(0)
    assert test_repo.days == []
    test_repo.toggle_day(0)
    test_repo.toggle_day(1)
    test_repo.toggle_day(2)
    test_repo.toggle_day(3)
    test_repo.toggle_day(4)
    test_repo.toggle_day(5)
    test_repo.toggle_day(6)
    assert test_repo.days == ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                              'Friday', 'Saturday']


def test_toggle_day_invalid_day_num(test_repo):
    test_repo.toggle_day(-1)
    assert test_repo.days == []


def test_toggle_month(test_repo):
    test_repo.toggle_month(0)
    assert test_repo.display_months == [datetime.date(2015, 6, 1)]
    test_repo.toggle_month(0)
    assert test_repo.display_months == []


def test_reset_daily_contribution_map(test_repo):
    test_repo.reset_daily_contribution_map()
    for d in test_repo.daily_contribution_map:
        assert test_repo.daily_contribution_map[d] == 0.0


def test_compute_daily_contribution_map_specific_days(test_repo):
    test_repo.days = ["Sunday"]
    test_repo.reset_daily_contribution_map()
    test_repo.compute_daily_contribution_map()
    for d in test_repo.daily_contribution_map:
        if test_repo.daily_contribution_map[d] != 0.0:
            assert d.strftime("%A") == "Sunday"


def test_normalize_daily_contribution_map(test_repo):
    for d in test_repo.daily_contribution_map:
        assert 0 <= test_repo.daily_contribution_map[d] <= 5


def test_compute_graph_matrix(test_repo):
    matrix = test_repo.compute_graph_matrix()
    assert matrix[0].col[0][0].strftime("%A") == "Sunday"
    test_repo.month_merge = True
    test_repo.width = " "  # thin block
    assert test_repo.get_matrix_width(matrix) == 53
    test_repo.width = "   "  # thick block
    assert test_repo.get_matrix_width(matrix) == 159
    test_repo.width = "  "  # reg block
    assert test_repo.get_matrix_width(matrix) == 106


def test_get_top_n_commiters(test_repo):
    assert test_repo.get_top_n_commiters([]) is None
    authors_list = [Commit(None, None, "James", None, None)] * 3 + \
                   [Commit(None, None, "John", None, None),
                    Commit(None, None, "JJ", None, None)]
    assert test_repo.get_top_n_commiters(authors_list) == [('James', 3),
                                                           ('John', 1),
                                                           ('JJ', 1)]

    authors_list = [Commit(None, None, "James", None, None)] * 30 + \
                   [Commit(None, None, "John", None, None)] * 10 + \
                   [Commit(None, None, "JJ", None, None)] * 5
    assert test_repo.get_top_n_commiters(authors_list,
                                         normailze_values=True) == [('James', 5),
                                                                    ('John', 2),
                                                                    ('JJ', 1)]


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main(__file__))
