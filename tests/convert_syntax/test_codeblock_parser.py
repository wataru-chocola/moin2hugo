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
