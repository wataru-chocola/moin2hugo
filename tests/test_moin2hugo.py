import pytest
import os
import tempfile
import filecmp
import difflib
from datetime import datetime

from moin2hugo import __version__
from moin2hugo.moin2hugo import Moin2Hugo, MoinPageInfo, MoinAttachment


@pytest.fixture
def moin_sitedir():
    return os.path.join(os.path.dirname(__file__), 'data/moin_site')


@pytest.fixture
def hugo_sitedir():
    return os.path.join(os.path.dirname(__file__), 'data/hugo_site')


@pytest.fixture
def moin2hugo_object(moin_sitedir):
    with tempfile.TemporaryDirectory() as d:
        moin2hugo = Moin2Hugo(moin_sitedir, d)
        yield moin2hugo


@pytest.fixture
def moin_abspath(moin_sitedir):
    def factory(path):
        return os.path.join(moin_sitedir, path)
    return factory


@pytest.fixture
def moin_pages(moin_sitedir, moin_abspath):
    pages = []

    pages.append(MoinPageInfo(
        name='FrontPage',
        filepath=moin_abspath('FrontPage/revisions/00000002'),
        updated=datetime(2019, 5, 22, 13, 16, 17, 699187),
        attachments=[]))

    pages.append(MoinPageInfo(
        name='テスト',
        filepath=moin_abspath('(e38386e382b9e38388)/revisions/00000002'),
        updated=datetime(2019, 5, 22, 13, 54, 54, 621428),
        attachments=[
            MoinAttachment(name='file_example_JPG_100kB.jpg',
                           filepath=moin_abspath('(e38386e382b9e38388)/attachments/file_example_JPG_100kB.jpg')),  # NOQA
            ]))

    pages.append(MoinPageInfo(
        name='テスト/page_test/ページ',
        updated=datetime(2012, 2, 2, 18, 34, 47),
        filepath=moin_abspath('(e38386e382b9e383882f)page_test(2fe3839ae383bce382b8)/revisions/00000003'),  # NOQA
        attachments=[]))

    pages.append(MoinPageInfo(
        name='テスト/attachments_test',
        updated=datetime(2019, 5, 22, 13, 54, 54, 621428),
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


def test_hugo_site_structure(moin2hugo_object):
    assert moin2hugo_object.hugo_site_structure[''] == moin2hugo_object.BRANCH_BUNDLE
    assert moin2hugo_object.hugo_site_structure['テスト'] == moin2hugo_object.BRANCH_BUNDLE
    assert moin2hugo_object.hugo_site_structure['テスト/attachments_test'] == moin2hugo_object.LEAF_BUNDLE  # noqa
    assert moin2hugo_object.hugo_site_structure['テスト/page_test/ページ'] == moin2hugo_object.LEAF_BUNDLE  # noqa


def assert_equal_directory(dcmp: filecmp.dircmp):
    assert not dcmp.left_only, dcmp.left_only
    assert not dcmp.right_only, dcmp.right_only
    if dcmp.diff_files:
        diff_text = ""
        for filename in dcmp.diff_files:
            left_filepath = os.path.join(dcmp.left, filename)
            right_filepath = os.path.join(dcmp.right, filename)
            diffs = difflib.unified_diff(open(left_filepath, 'r').read().splitlines(),
                                         open(right_filepath, 'r').read().splitlines(),
                                         fromfile=left_filepath, tofile=right_filepath)
            diff_text += "\n".join(diffs)
            diff_text += "\n"
        raise AssertionError("found diff\n" + diff_text)

    for subdir, subdir_dcmp in dcmp.subdirs.items():
        print("subdir:" + subdir)
        assert_equal_directory(subdir_dcmp)


def test_convert(moin_sitedir, hugo_sitedir):
    with tempfile.TemporaryDirectory() as d:
        moin2hugo = Moin2Hugo(moin_sitedir, d)
        moin2hugo.convert()
        dcmp = filecmp.dircmp(d, hugo_sitedir)
        assert_equal_directory(dcmp)
