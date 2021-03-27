from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter

import textwrap


def test_basic_table():
    table_text = """\
    ||'''A'''||'''B'''||'''C'''||
    ||1      || 2 ||3      ||
    """
    expected = """\
    | **A** | **B** | **C** |
    | - | - | - |
    | 1 | 2 | 3 |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_table_escape():
    table_text = """\
    || A| || B| || C| ||
    || -- || -- || -- ||
    ||1   || 2  ||3   ||
    """
    expected = """\
    |   |   |   |
    | - | - | - |
    | A\\| | B\\| | C\\| |
    | \\-\\- | \\-\\- | \\-\\- |
    | 1 | 2 | 3 |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_extended_table():
    # TODO
    pass
