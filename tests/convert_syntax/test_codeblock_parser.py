from moin2hugo.moin_parser import MoinParser

import textwrap


def test_highlighted_python(formatter_object):
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
    page = MoinParser.parse(textwrap.dedent(code_block_text), 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected
