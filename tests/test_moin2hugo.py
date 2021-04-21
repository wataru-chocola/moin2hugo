import pytest
import os
import tempfile
import filecmp
import difflib

from moin2hugo.moin2hugo import Moin2Hugo


@pytest.fixture
def moin2hugo_object(moin_sitedir):
    with tempfile.TemporaryDirectory() as d:
        moin2hugo = Moin2Hugo(moin_sitedir, d)
        yield moin2hugo


def test_hugo_site_structure(moin2hugo_object):
    assert moin2hugo_object.hugo_site_structure[''] == moin2hugo_object.BRANCH_BUNDLE
    assert moin2hugo_object.hugo_site_structure['テスト'] == moin2hugo_object.BRANCH_BUNDLE
    assert moin2hugo_object.hugo_site_structure['テスト/attachments_test'] == moin2hugo_object.LEAF_BUNDLE  # noqa
    assert moin2hugo_object.hugo_site_structure['テスト/page_test/ページ'] == moin2hugo_object.LEAF_BUNDLE  # noqa


def assert_equal_directory(dcmp: filecmp.dircmp):
    dcmp.left_only = list(filter(lambda x: not x.startswith("."), dcmp.left_only))
    dcmp.right_only = list(filter(lambda x: not x.startswith("."), dcmp.right_only))
    assert not dcmp.left_only, dcmp.left_only
    assert not dcmp.right_only, dcmp.right_only

    dcmp.diff_files = list(filter(lambda x: not x.startswith("."), dcmp.diff_files))
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
