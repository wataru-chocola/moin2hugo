import pytest
import os


@pytest.fixture
def moin_sitedir():
    return os.path.join(os.path.dirname(__file__), 'data/moin_site')


@pytest.fixture
def moin_abspath(moin_sitedir):
    def factory(path):
        return os.path.join(moin_sitedir, path)
    return factory


@pytest.fixture
def hugo_sitedir():
    return os.path.join(os.path.dirname(__file__), 'data/hugo_site')
