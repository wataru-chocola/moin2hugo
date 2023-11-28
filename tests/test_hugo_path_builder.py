import pytest

from moin2hugo.path_builder.hugo import HugoPathBuilder


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("xyz", "xyz"),
        ("abc/xyz.md", "abc/xyz.md"),
        ("ab%01cd", "ab%01cd"),
        ("ab%08cd", "ab08cd"),
        ("a-----b", "a-b"),
        ("a- b", "a-b"),
        ("中点・テスト", "中点テスト"),
        ("全角　スペース", "全角-スペース"),
    ],
)
def test_sanitize_path(data: str, expected: str):
    path_builder = HugoPathBuilder()
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
    path_builder = HugoPathBuilder(remove_path_accents=True)
    ret = path_builder._sanitize_path(data)  # type: ignore
    assert ret == expected
