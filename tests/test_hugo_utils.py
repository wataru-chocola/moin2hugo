import pytest
import textwrap
from datetime import datetime

from moin2hugo.path_builder import HugoPathBuilder
from moin2hugo.formatter import HugoFormatter


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo", "PageName/foo/bar"), "bar"),
        (("PageName/foo1", "PageName/foo2/bar"), "/PageName/foo2/bar"),
        ((None, "PageName"), "/PageName"),
        (("PageName/foo", "PageName/foo"), ""),
    ]
)
def test_page_url(data, expected):
    base, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True)
    url = path_builder.page_url(target, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo1", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar"),
    ]
)
def test_page_url_with_root_path(data, expected):
    base, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True, root_path='/hugo')
    url = path_builder.page_url(target, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "a.png", "PageName/foo"), "foo/a.png"),
        (("PageName/foo", "a.png", "PageName/foo/bar"), "bar/a.png"),
        (("PageName/foo1", "a.png", "PageName/foo2/bar"), "/PageName/foo2/bar/a.png"),
        ((None, "a.png", "PageName"), "/PageName/a.png"),
        (("PageName/foo", "a.png", "PageName/foo"), "a.png"),
    ]
)
def test_attachment_url(data, expected):
    base, filename, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True)
    url = path_builder.attachment_url(target, filename, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "a.png", "PageName/foo"), "foo/a.png"),
        (("PageName/foo1", "a.png", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar/a.png"),
    ]
)
def test_attachment_url_with_root_path(data, expected):
    base, filename, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True, root_path='/hugo')
    url = path_builder.attachment_url(target, filename, base)
    assert url == expected


@pytest.mark.parametrize(
    ("pagename", "updated", "expected"), [
        ("PageName/てすと", datetime(2019, 5, 22, 13, 54, 54, 621428),
         """\
         ---
         title: "てすと"
         date: 2019-05-22T13:54:54.621428
         ---"""),
        ("てすと", None,
         """\
         ---
         title: "てすと"
         ---"""),
    ]
)
def test_frontmatter(pagename, updated, expected):
    expected = textwrap.dedent(expected)
    ret = HugoFormatter.create_frontmatter(pagename, updated)
    assert ret == expected
