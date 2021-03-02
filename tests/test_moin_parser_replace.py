import pytest

from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()


def test_heading(formatter_object, capsys):
    MoinParser.format("= head1 =", formatter_object)
    captured = capsys.readouterr()
    assert captured.out == '# head1\n\n'
