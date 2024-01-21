import textwrap

import pytest

from moin2kibun.formatter import KibunFormatter
from moin2x.moin_parser import MoinParser


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            """\
         __missing closing delimiter for underline

         xyz
         """,
            """\
         <u>missing closing delimiter for underline
         </u>

         xyz
         """,
        ),
        ("'''__hoge'''", "**<u>hoge</u>** "),
    ],
)
def test_unclosed_element(data: str, expected: str):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    page = MoinParser.parse(data, "PageName")
    assert KibunFormatter.format(page, pagename="PageName") == expected, page.tree_repr()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            """\
         __missing closing delimiter for underline

         xyz
         """,
            """\
         <u>missing closing delimiter for underline
         </u>

         xyz
         """,
        ),
        ("'''__hoge'''", "**<u>hoge</u>** "),
    ],
)
def test_unclosed_element_in_strict_mode(data: str, expected: str):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    with pytest.raises(AssertionError):
        _ = MoinParser.parse(data, "PageName", strict_mode=True)
