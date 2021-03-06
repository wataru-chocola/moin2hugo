import pytest
import os

from moin2hugo import __version__
from moin2hugo.moin2hugo import Moin2Hugo, MoinPageInfo, MoinAttachment


@pytest.fixture
def moin_sitedir():
    return os.path.join(os.path.dirname(__file__), 'data/moin_site')


@pytest.fixture
def moin2hugo_object(moin_sitedir):
    moin2hugo = Moin2Hugo(moin_sitedir, 'dst_dir')
    return moin2hugo


@pytest.fixture
def moin_abspath(moin_sitedir):
    def factory(path):
        return os.path.join(moin_sitedir, path)
    return factory


@pytest.fixture
def moin_pages(moin_sitedir, moin_abspath):
    pages = []

    pages.append(MoinPageInfo(
        name='テスト/page_test/ページ',
        filepath=moin_abspath('(e38386e382b9e383882f)page_test(2fe3839ae383bce382b8)/revisions/00000003'),  # NOQA
        attachments=[]))

    pages.append(MoinPageInfo(
        name='テスト/attachments_test',
        filepath=moin_abspath('(e38386e382b9e383882f)attachments_test/revisions/00000002'),
        attachments=[
            MoinAttachment(name='file_example_JPG_100kB.jpg',
                           filepath=moin_abspath('(e38386e382b9e383882f)attachments_test/attachments/file_example_JPG_100kB.jpg')),  # NOQA
            MoinAttachment(name='file_example_PNG_500kB.png',
                           filepath=moin_abspath('(e38386e382b9e383882f)attachments_test/attachments/file_example_PNG_500kB.png')),  # NOQA
            ]))
    return pages


def test_version():
    assert __version__ == '0.1.0'


def test_scan_pages(moin2hugo_object, moin_pages):
    expected = moin_pages
    for page in moin2hugo_object.scan_pages(moin2hugo_object.src_dir):
        for i, e in enumerate(expected):
            if page.name == e.name:
                assert page == e
                expected = expected[:i] + expected[i+1:]
                break
        else:
            raise AssertionError("%r in results doesn't exists in expected" % page)

    if expected:
        raise AssertionError("expected elems are missing: %r" % expected)
