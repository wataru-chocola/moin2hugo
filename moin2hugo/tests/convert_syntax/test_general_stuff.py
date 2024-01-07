import textwrap

import pytest

from moin2hugo.formatter import HugoFormatter
from moin2x.moin_parser import MoinParser


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("test\ntest", "test\ntest"),
        ("'''''test'''''\ntest", "***test***\ntest"),
    ],
)
def test_endling_newline(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    # all markdown escaping are located in test_hugo_formatter.py
    ("data", "expected"),
    [
        ("line with spaces  \ntest", "line with spaces\ntest"),
        ("line1\n/* xyz */    line2", "line1\nline2"),
        ("line1  /* xyz */  \nline2", "line1\nline2"),
        ("_test_", r"\_test\_"),
        ("'''***'''", r"**\*\*\*** "),
    ],
)
def test_escape(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("<<TableOfContents>>", ""),
        ("<<BR>>", "  \n"),
        ("||a||b<<BR>>c||", "|   |   |\n|---|---|\n| a | b<br />c |\n"),
        ("<<UnsupportedMacro>>", r"\<\<UnsupportedMacro\>\>"),
    ],
)
def test_macro(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("## this is comment", ""),
        ("Hello, /* this is comment */ world", "Hello,  world"),
        ("Hello, /* ''' comment */ world", "Hello,  world"),
    ],
)
def test_comment(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (":)", ":simple_smile:"),
    ],
)
def test_smiley(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            """\
         ||a ||b ||
         ||1 ||2 ||
         = head1 =
         """,
            """\
         |   |   |
         |---|---|
         | a | b |
         | 1 | 2 |

         ## head1

         """,
        ),
        (
            """\
         == head1 ==

         Preamble.

          * aaaaaaaaaaaaa
          * baaaaaaaaaaaa

         == head1 ==
         """,
            """\
         ### head1

         Preamble.

         * aaaaaaaaaaaaa
         * baaaaaaaaaaaa

         ### head1

         """,
        ),
    ],
)
def test_continuous_blocks(data: str, expected: str):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected, page.tree_repr()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("&uuml;", "&uuml;"),
        ("&#42;", "&#42;"),
        ("&#x42;", "&#x42;"),
    ],
)
def test_entities(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("__a ~+larger+~ a__", "<u>a <big>larger</big> a</u>"),
        (r"__aaa{{< test bbb__", r"<u>aaa{{&lt; test bbb</u>"),
        (r"__aaa{{% test bbb__", r"<u>aaa{{&#37; test bbb</u>"),
    ],
)
def test_shortcode_within_tag(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("`{{<abc>}}`", "`{{</*abc*/>}}`"),
        (
            """\
         {{{
         {{< abc `bar
         baz` xyz >}}
         }}}
         """,
            """\
         ```
         {{</* abc `bar
         baz` xyz */>}}
         ```
         """,
        ),
    ],
)
def test_shortcode_within_pre(data: str, expected: str):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected).rstrip()
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data
