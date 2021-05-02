from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter

import textwrap


def test_highlighted_python():
    code_block_text = """\
    {{{#!highlight python
    import sys
    sys.out.write("Hello, World")
    }}}
    """
    expected = """\
    ```python
    import sys
    sys.out.write("Hello, World")
    ```
    """.rstrip()
    data = textwrap.dedent(code_block_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_old_parser_irrsi():
    code_block_text = """\
    {{{#!irssi
    ...
    }}}
    """
    expected = """\
    ```irc
    ...
    ```
    """.rstrip()
    data = textwrap.dedent(code_block_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_csv_basic():
    text = """\
    {{{#!csv
    a,b,c
    d,e,f
    }}}
    """
    expected = """\
    | a | b | c |
    |---|---|---|
    | d | e | f |
    """
    data = textwrap.dedent(text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_csv_old_style_param():
    text = """\
    {{{#!csv .
    a.b.c
    d.e.f
    }}}
    """
    expected = """\
    | a | b | c |
    |---|---|---|
    | d | e | f |
    """
    data = textwrap.dedent(text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_csv_param1():
    text = """\
    {{{#!csv delimiter=. hide=a,b static_cols=d,e static_vals=D,E
    a.b.c
    d.e.f
    g.h.i
    }}}
    """
    expected = """\
    | c | d | e |
    |---|---|---|
    | f | D | E |
    | i | D | E |
    """
    data = textwrap.dedent(text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_csv_param2():
    text = """\
    {{{#!csv link=b
    a,b,c
    a1,http://example.com/link1 desc1,c1
    a2,b2,c2
    }}}
    """
    expected = """\
    | a | b | c |
    |---|---|---|
    | a1 | [desc1](http://example.com/link1) | c1 |
    | a2 | b2 | c2 |
    """
    data = textwrap.dedent(text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_codeblock_shortcode(caplog):
    code_block_text = """\
    {{{#!highlight python
    print("hello, {{< world >}}")
    }}}
    """
    expected = """\
    ```python
    print("hello, {{</* world */>}}")
    ```
    """.rstrip()
    data = textwrap.dedent(code_block_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data

    assert "cannot handle non-paired shortcode delimiter" not in caplog.text, page.tree_repr()
