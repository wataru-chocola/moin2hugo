import pytest
import moin2hugo.moinutils


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('target="_blank",&do=get', {'target': '_blank', '&do': 'get'}),
    ]
)
def test_parse_quoted_separated(data, expected):
    _, ret, _ = moin2hugo.moinutils.parse_quoted_separated(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('%E3%83%86%E3%82%B9%E3%83%88', 'テスト'),
    ]
)
def test_url_unquote(data, expected):
    ret = moin2hugo.moinutils.url_unquote(data)
    assert ret == expected
