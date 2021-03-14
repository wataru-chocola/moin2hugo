import pytest

import moin2hugo.moin_parser


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('class="link",unk="unk",&action=post', ({'class': "link"}, {'action': 'post'}))
    ]
)
def test_get_params(data, expected):
    params, qargs = moin2hugo.moin_parser._get_params(data, acceptable_attrs=['class'])
    assert params == expected[0]
    assert qargs == expected[1]


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('<bgcolor="#00FF00" rowspan="2">', {'bgcolor': '"#00FF00"', 'rowspan': '"2"'}),
        ('<#TGIF rowspan="2">', {}),
    ]
)
def test_getTableAttrs(data, expected):
    ret = moin2hugo.moin_parser._getTableAttrs(data)
    assert ret == expected
