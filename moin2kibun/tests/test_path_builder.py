import pytest

from moin2kibun.path_builder import KibunPathBuilder


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("xyz", "xyz"),
        ("abc/xyz.md", "abc/xyz.md"),
        ("ab%01cd", "ab%01cd"),
        ("   abc ", "abc"),
        ("__abc ", "abc"),
    ],
)
def test_sanitize_path(data: str, expected: str):
    path_builder = KibunPathBuilder()
    ret = path_builder._sanitize_path(data)  # type: ignore
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("xyz", "xyz"),
        ("apresentação", "apresentacao"),
    ],
)
def test_sanitize_path_with_remove_path_accents(data: str, expected: str):
    path_builder = KibunPathBuilder(remove_path_accents=True)
    ret = path_builder._sanitize_path(data)  # type: ignore
    assert ret == expected
