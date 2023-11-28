import difflib
import filecmp
import os
import tempfile
from typing import Iterator, TypeAlias
from unittest.mock import patch

import pytest

from moin2hugo.moin2hugo import Moin2Hugo, print_version

from .conftest import HugoSitedirFixture, MoinSitedirFixture

Moin2HuogObjectFixture: TypeAlias = Iterator[Moin2Hugo]


@pytest.fixture
def moin2hugo_object(moin_sitedir: MoinSitedirFixture) -> Moin2Hugo:
    with tempfile.TemporaryDirectory() as d:
        moin2hugo = Moin2Hugo(moin_sitedir, d)
        return moin2hugo


def test_print_version():
    print_version()


def test_hugo_site_structure(moin2hugo_object: Moin2Hugo):
    assert moin2hugo_object.hugo_site_structure[""] == moin2hugo_object.BRANCH_BUNDLE
    assert moin2hugo_object.hugo_site_structure["テスト"] == moin2hugo_object.BRANCH_BUNDLE
    assert (
        moin2hugo_object.hugo_site_structure["テスト/attachments_test"]
        == moin2hugo_object.LEAF_BUNDLE
    )  # noqa
    assert (
        moin2hugo_object.hugo_site_structure["テスト/page_test/ページ"] == moin2hugo_object.LEAF_BUNDLE
    )  # noqa


def assert_equal_directory(dcmp: filecmp.dircmp[str]):
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
            diffs = difflib.unified_diff(
                open(left_filepath, "r").read().splitlines(),
                open(right_filepath, "r").read().splitlines(),
                fromfile=left_filepath,
                tofile=right_filepath,
            )
            diff_text += "\n".join(diffs)
            diff_text += "\n"
        raise AssertionError("found diff\n" + diff_text)

    for subdir, subdir_dcmp in dcmp.subdirs.items():
        print("subdir:" + subdir)
        assert_equal_directory(subdir_dcmp)


def test_convert(moin_sitedir: MoinSitedirFixture, hugo_sitedir: HugoSitedirFixture):
    with tempfile.TemporaryDirectory() as d:
        dstdir = os.path.join(d, "output")
        moin2hugo = Moin2Hugo(moin_sitedir, dstdir)
        moin2hugo.convert()
        dcmp = filecmp.dircmp(dstdir, hugo_sitedir)
        assert_equal_directory(dcmp)


def test_convert_assertion_error(
    moin_sitedir: MoinSitedirFixture,
    hugo_sitedir: HugoSitedirFixture,
    caplog: pytest.LogCaptureFixture,
):
    with tempfile.TemporaryDirectory() as d:
        dstdir = os.path.join(d, "output")
        moin2hugo = Moin2Hugo(moin_sitedir, dstdir)
        with patch.object(moin2hugo, "convert_page", side_effect=AssertionError):
            moin2hugo.convert()
    assert "fail to convert" in caplog.text, caplog.text
