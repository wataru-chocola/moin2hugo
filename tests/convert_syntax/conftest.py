import pytest

from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()
