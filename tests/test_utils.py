import pytest
from moin2hugo.utils import safe_path_join


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
