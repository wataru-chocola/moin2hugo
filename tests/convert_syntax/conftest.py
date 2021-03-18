import pytest

from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()


@pytest.fixture
def formatter_without_unsafe_object():
    f = Formatter()
    f.config.goldmark_unsafe = False
    return f
