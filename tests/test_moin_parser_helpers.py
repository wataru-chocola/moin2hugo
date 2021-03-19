import pytest
import textwrap

import moin2hugo.moin_parser


def test_src_build():
    text = textwrap.dedent("""\
    <<TableOfContents>>

    = Headling 1 =

    This is test /* inline comment */ for attaching src to each element.

     * item1
         * decoration: '''strong'''
         * decoration: '''''strong&emphasis''' emphasis''
         * decoration: ^super^test
         * word: WikiName
         * word: !WikiName
         * word: PageName
         * word: !PageName
     * item2

     {{{#!highlight python
    ...
    }}}

    {{attachment:test.png}}
    [[https://www.example.com/|{{attachment:test.png}}]]

    """)
    page = moin2hugo.moin_parser.MoinParser.parse(text, 'PageName')
    assert page.source_text == text, page.print_structure(include_src=True)


# TODO
# def test_bang_meta():
#     import moin2hugo.moin_site_config
#     moin2hugo.moin_site_config.bang_meta = False
#     page = moin2hugo.moin_parser.MoinParser.parse("!WikiName", 'PageName')
#     assert page.print_structure() == '', page.print_structure(include_src=True)


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
