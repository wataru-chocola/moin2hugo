import os
from typing import Callable, TypeAlias

import pytest

MoinSitedirFixture: TypeAlias = str


@pytest.fixture
def moin_sitedir() -> MoinSitedirFixture:
    return os.path.join(os.path.dirname(__file__), "data/moin_site")


MoinAbspathFixture: TypeAlias = Callable[[str], str]


@pytest.fixture
def moin_abspath(moin_sitedir: str):
    def factory(path: str):
        return os.path.join(moin_sitedir, path)

    return factory


HugoSitedirFixture: TypeAlias = str


@pytest.fixture
def hugo_sitedir() -> HugoSitedirFixture:
    return os.path.join(os.path.dirname(__file__), "data/hugo_site")
