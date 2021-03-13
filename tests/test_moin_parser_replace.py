import pytest
from unittest import mock
import textwrap

from moin2hugo.moin_parser import MoinParser, _getTableAttrs
from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("<<TableOfContents>>", ''),
        ("<<BR>>", '<br />'),
        ("<<UnsupportedMacro>>", '<<UnsupportedMacro>>'),
    ]
)
def test_macro(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    ret = formatter_object.format(page)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("## this is comment", ''),
        ("Hello, /* this is comment */ world", 'Hello,  world'),
    ]
)
def test_comment(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    ret = formatter_object.format(page)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (":)", ":simple_smile:"),
    ]
)
def test_smiley(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    ret = formatter_object.format(page)
    assert ret == expected


def test_codeblock(formatter_object):
    code_block_text = """\
    {{{#!highlight python
    import sys
    sys.out.write("Hello, World")
    }}}
    """
    # first line: moin parser makes empty paragraph before preformatted text.
    expected = """\

    ```python
    import sys
    sys.out.write("Hello, World")
    ```
    """.rstrip()
    page = MoinParser.parse(textwrap.dedent(code_block_text), 'PageName', formatter_object)
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


def test_table(formatter_object):
    table_text = """\
    ||'''A'''||'''B'''||'''C'''||
    ||1      || 2 ||3      ||
    """
    expected = """\
    | **A** | **B** | **C** |
    | 1 | 2 | 3 |
    """
    page = MoinParser.parse(textwrap.dedent(table_text), 'PageName', formatter_object)
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('<bgcolor="#00FF00" rowspan="2">', {'bgcolor': '"#00FF00"', 'rowspan': '"2"'}),
        ('<#TGIF rowspan="2">', {}),
    ]
)
def test_getTableAttrs(data, expected, formatter_object):
    ret = _getTableAttrs(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("= head1 =", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),
    ]
)
def test_heading(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("----", "----\n\n"),
        ("-----------------", "----\n\n"),
    ]
)
def test_horizontal_rules(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("__underlined text__", "<u>underlined text</u>"),
        ("__underlined\ntext__", "<u>underlined\ntext</u>"),
        ("--(stroke)--", "~~stroke~~"),
        ("''italic''", "*italic*"),
        ("'''strong'''", "**strong**"),
        ("'''''italic and strong'''''", "***italic and strong***"),
        ("''this is italic and '''this is strong'''''", "*this is italic and **this is strong***"),
        ("'''this is strong and ''this is italic'''''", "**this is strong and *this is italic***"),
        ("~-smaller-~", "<small>smaller</small>"),
        ("~+larger+~", "<big>larger</big>"),
    ]
)
def test_decorations_ml(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("^super^script", "<sup>super</sup>script"),   # TODO
        (",,sub,,script", "<sub>sub</sub>script"),   # TODO
        ("`inline code`", "`inline code`"),
        ("{{{this is ``code``}}}", "```this is ``code`` ```"),
    ]
)
def test_decorations_sl(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("MeatBall:InterWiki", "MeatBall:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ('[[free link]]', '[free link](free link)'),
        ('[[SamePage|Some Page]]', '[Some Page](SamePage)'),
        ('[[SamePage#subsection|subsection of Some Page]]', '[subsection of Some Page](SamePage#subsection)'),  # noqa
        # TODO: ('[[SomePage|{{attachment:imagefile.png}}]]', ''),
        # TODO: ('[[SomePage|some Page|target="_blank"]]', ''),
        ('[[attachment:SomePage/image.png]]', '[SomePage/image.png](SomePage/image.png)'),
        ('[[attachment:SomePage/image.png|image.png|title="png"]]', '[image.png](SomePage/image.png "png")'),  # noqa
        ('[[drawing:SomePage/image.png]]', '[[drawing:SomePage/image.png]]'),
        ('[[http://example.net/|example site]]', '[example site](http://example.net/)'),
        ('[[otherwiki:somepage]]', 'otherwiki:somepage'),
    ]
)
def test_links(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("&uuml;", "&uuml;"),
        ("&#42;", "&#42;"),
        ("&#x42;", "&#x42;"),
    ]
)
def test_entities(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


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
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


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
    """
    data = textwrap.dedent(moin_text)

    page = MoinParser.parse(data, 'PageName', formatter_object)
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


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

    page = MoinParser.parse(data, 'PageName', formatter_object)
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


def test_definition_lists(formatter_object):
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

    page = MoinParser.parse(data, 'PageName', formatter_object)
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        # attachment
        ("{{attachment:image.png}}", "![](filepath/PageName/image.png)"),
        ("{{attachment:image.png|title}}", '![](filepath/PageName/image.png "title")'),
        ('{{attachment:image.png|title|width=100 height=150 xxx=11}}', '![](filepath/PageName/image.png "title")'),  # noqa
        ("{{attachment:image.txt}}", "```\nhello\n```\n\n[image.txt](url/PageName/image.txt)"),
        ("{{attachment:image.pdf}}", '<object data="url/PageName/image.pdf" type="application/pdf">image.pdf</object>'),  # noqa
        # page
        ("{{pagename}}", '<object data="url/pagename" type="text/html">pagename</object>'),
        # drawing
        ("{{drawing:twikitest.tdraw}}", "{{drawing:twikitest.tdraw}}"),
        # external graphic
        ("{{http://example.net/image.png}}", "![](http://example.net/image.png)"),
        ('{{http://example.net/image.png|alt text|align="position"}}', '![alt text](http://example.net/image.png "alt text")'),  # noqa
    ]
)
def test_transclude(data, expected, formatter_object):
    mock_io = mock.mock_open(read_data="hello")
    page = MoinParser.parse(data, 'PageName', formatter_object)
    with mock.patch('moin2hugo.formatter.open', mock_io):
        assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("test\ntest", "test\ntest"),
        ("'''''test'''''\ntest", "***test***\ntest"),
    ]
)
def test_endling_newline(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected
