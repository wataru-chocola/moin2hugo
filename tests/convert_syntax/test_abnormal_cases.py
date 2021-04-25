from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter

import pytest
import textwrap


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("""\
         __missing closing delimiter for underline

         xyz
         """,
         """\
         <u>missing closing delimiter for underline
         </u>

         xyz
         """),
        ("'''__hoge'''", "**<u>hoge</u>** "),
    ]
)
def test_unclosed_element(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected, page.tree_repr()


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("""\
         __missing closing delimiter for underline

         xyz
         """,
         """\
         <u>missing closing delimiter for underline
         </u>

         xyz
         """),
        ("'''__hoge'''", "**<u>hoge</u>** "),
    ]
)
def test_unclosed_element_in_strict_mode(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    with pytest.raises(AssertionError):
        _ = MoinParser.parse(data, 'PageName', strict_mode=True)
