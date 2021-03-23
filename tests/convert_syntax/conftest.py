import pytest

from moin2hugo.formatter import HugoFormatter


@pytest.fixture
def formatter_object():
    return HugoFormatter()


@pytest.fixture
def formatter_without_unsafe_object():
    f = HugoFormatter()
    f.config.goldmark_unsafe = False
    return f
