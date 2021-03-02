import pytest
import moin2hugo.moinutils


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('target="_blank",&do=get', {'target': '_blank', '&do': 'get'}),
    ]
)
def test_links(data, expected):
    _, ret, _ = moin2hugo.moinutils.parse_quoted_separated(data)
    assert ret == expected
