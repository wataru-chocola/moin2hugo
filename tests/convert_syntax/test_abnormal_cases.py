import textwrap

import pytest

from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.moin_parser import MoinParser


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
    assert HugoFormatter.format(page, pagename="PageName") == expected, page.tree_repr()


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


@pytest.mark.parametrize(
    ("data"),
    [
        (
            """\
         {{{
         hello, {{%world!
         }}}
         """
        ),
        ("`hello, {{%world!`"),
    ],
)
def test_incomplete_shortcode_inside_code(data: str, caplog: pytest.LogCaptureFixture):
    data = textwrap.dedent(data)
    page = MoinParser.parse(data, "PageName")
    _ = HugoFormatter.format(page, pagename="PageName")
    assert "cannot handle non-paired shortcode delimiter" in caplog.text, page.tree_repr()
