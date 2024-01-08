import textwrap

import pytest

from moin2kibun.formatter import KibunFormatter
from moin2x.moin_parser import MoinParser


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (" . hoge", "* hoge"),
        (" * hoge", "* hoge"),
        (" 1. hoge", "1. hoge"),
        (" a. hoge", "1. hoge"),
        (" hoge", "* hoge"),  # indent list
    ],
)
def test_itemlists_simple(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_itemlists_multi_items():
    moin_text = """\
    Preamble.

     * one.
       * one-2.
       * one-3.
         1. num1
         2. num2
     * two
     * three
       * three-1.
    """
    expected = """\
    Preamble.

    * one.
        * one-2.
        * one-3.
            1. num1
            1. num2
    * two
    * three
        * three-1.
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_itemlists_containing_paragraph():
    moin_text = """\
    Preamble.

     * one.
       * one-2.

       {{{#!highlight python
    import sys
    sys.stdout.write("hello, world")
    }}}
       * one-3.
     * two
    """
    expected = """\
    Preamble.

    * one.
        * one-2.

          ```python
          import sys
          sys.stdout.write("hello, world")
          ```
        * one-3.
    * two
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_definition_lists_1():
    moin_text = """\
    Preamble.

     term:: definition
     object::
     :: description 1
        * a
        * b
     :: description 2

     {{{#!highlight python
    import sys
    sys.stdout.write("hello, world")
    }}}
     :: description 3
    """
    expected = """\
    Preamble.

    term
    :   definition

    object
    :   description 1
        * a
        * b
    :   description 2

        ```python
        import sys
        sys.stdout.write("hello, world")
        ```
    :   description 3
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_definition_lists_2():
    moin_text = """\
    Preamble.

     term1 ::
     description 1
    """
    expected = """\
    Preamble.

    term1
    :   description 1
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_definition_lists_3():
    """Original moin-1.9 parser wrongly parses table inside definition description."""
    moin_text = """\
    Preamble.

     term1::
     text1-1.

       * item1
       * item2

     text1-2.

     ||a ||b ||c ||
     ||x ||y ||z ||

     term2::
     text2.
    """
    expected = """\
    Preamble.

    term1
    :   text1-1.
        * item1
        * item2

        text1-2.
        |   |   |   |
        |---|---|---|
        | a | b | c |
        | x | y | z |

    term2
    :   text2.
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


def test_definition_lists_4():
    moin_text = """\
    Preamble.

     term1 ::
      * item1
      * item2

     term2 ::
     text2.
    """
    expected = """\
    Preamble.

    term1
    :   * item1
        * item2

    term2
    :   text2.
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, "PageName")
    expected = textwrap.dedent(expected)
    assert KibunFormatter.format(page, pagename="PageName") == expected, page.tree_repr()
    assert page.source_text == data
