import pytest

from moin2hugo.formatter.hugo import safe_path_join, page_url


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("tmp", "foo/bar"), "tmp/foo/bar"),
        (("tmp/", "foo/bar"), "tmp/foo/bar"),
        (("tmp/xyz", "foo/bar"), "tmp/xyz/foo/bar"),
        (("/tmp", "foo/bar"), "/tmp/foo/bar"),
    ]
)
def test_safe_path_join(data, expected):
    basepath, path = data
    ret = safe_path_join(basepath, path)
    assert ret == expected


@pytest.mark.parametrize(
    ("basepath", "path"), [
        ("tmp", "/foo/bar"),
        ("tmp/", "../foo"),
        ("tmp/xyz", "../foo"),
        ("/tmp", "/foo"),
    ]
)
def test_safe_path_join_error(basepath, path):
    with pytest.raises(ValueError):
        safe_path_join(basepath, path)


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo", "PageName/foo/bar"), "bar"),
        (("PageName/foo1", "PageName/foo2/bar"), "/PageName/foo2/bar"),
        (("PageName", None), "/PageName"),
        (("PageName/foo", "PageName/foo"), ""),
    ]
)
def test_page_url(data, expected):
    target, base = data
    page_url(target, base, disable_path_to_lower=False)
