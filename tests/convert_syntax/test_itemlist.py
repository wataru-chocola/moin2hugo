from moin2hugo.moin_parser import MoinParser

import pytest
import textwrap


@pytest.mark.parametrize(
    ("data", "expected"), [
        (" . hoge", "* hoge"),
        (" * hoge", "* hoge"),
        (" 1. hoge", "1. hoge"),
        (" a. hoge", "1. hoge"),
        (" hoge", "* hoge"),  # indent list
    ]
)
def test_itemlists_simple(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_itemlists_multi_items(formatter_object):
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

    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_itemlists_containing_paragraph(formatter_object):
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

    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_definition_lists_1(formatter_object):
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
    : definition

    object
    : description 1
        * a
        * b
    : description 2

        ```python
        import sys
        sys.stdout.write("hello, world")
        ```
    : description 3
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_definition_lists_2(formatter_object):
    moin_text = """\
    Preamble.

     term1 ::
     description 1
    """
    expected = """\
    Preamble.

    term1
    : description 1
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_definition_lists_3(formatter_object):
    """Original moin-1.9 parser wrongly parses table inside definition description.
    """
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
    : text1-1.
        * item1
        * item2

      text1-2.
      | a | b | c |
      | x | y | z |

    term2
    : text2.
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected, page.tree_repr()
    assert page.source_text == data
