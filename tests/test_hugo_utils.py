import pytest

from moin2hugo.formatter.hugo import safe_path_join, page_url, attachment_url


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
        ((None, "PageName"), "/PageName"),
        (("PageName/foo", "PageName/foo"), ""),
    ]
)
def test_page_url(data, expected):
    base, target = data
    url = page_url(target, base, disable_path_to_lower=True)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo1", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar"),
    ]
)
def test_page_url_with_root_path(data, expected):
    base, target = data
    url = page_url(target, base, disable_path_to_lower=True, root_path='/hugo')
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
    url = attachment_url(target, filename, base, disable_path_to_lower=True)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "a.png", "PageName/foo"), "foo/a.png"),
        (("PageName/foo1", "a.png", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar/a.png"),
    ]
)
def test_attachment_url_with_root_path(data, expected):
    base, filename, target = data
    url = attachment_url(target, filename, base, disable_path_to_lower=True, root_path='/hugo')
    assert url == expected
