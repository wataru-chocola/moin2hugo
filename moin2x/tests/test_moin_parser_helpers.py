import textwrap
from typing import Tuple

import pytest

import moin2x.moin_parser
from moin2x.config import MoinSiteConfig
from moin2x.page_tree import Pagelink, PageRoot, Paragraph, Text


def test_src_build():
    text = textwrap.dedent(
        """\
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

    """
    )
    page = moin2x.moin_parser.MoinParser.parse(text, "PageName")
    assert page.source_text == text, page.tree_repr(include_src=True)


def test_bang_meta():
    moin_site_config = MoinSiteConfig(bang_meta=False)
    page = moin2x.moin_parser.MoinParser.parse("!WikiName", "PageName", moin_site_config)
    expected = PageRoot.from_dict(
        {
            "source_text": "!WikiName",
            "children": [
                (
                    Paragraph,
                    {
                        "source_text": "!WikiName",
                        "children": [
                            (
                                Pagelink,
                                {
                                    "anchor": "",
                                    "target_pagename": "WikiName",
                                    "current_pagename": "PageName",
                                    "source_text": "!WikiName",
                                    "children": [
                                        (
                                            Text,
                                            {"content": "!WikiName", "source_text": "!WikiName"},
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        }
    )
    assert page == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [('class="link",unk="unk",&action=post', ({"class": "link"}, {"action": "post"}))],
)
def test_get_params(data: str, expected: Tuple[dict[str, str], dict[str, str]]):
    params, qargs = moin2x.moin_parser._get_params(data, acceptable_attrs=["class"])  # type: ignore
    assert params == expected[0]
    assert qargs == expected[1]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ('<bgcolor="#00FF00" rowspan="2">', {"bgcolor": "#00FF00", "rowspan": "2"}),
        ('<#TGIF rowspan="2">', {}),
    ],
)
def test_getTableAttrs(data: str, expected: dict[str, str]):
    ret = moin2x.moin_parser._getTableAttrs(data)  # type: ignore
    assert ret == expected
