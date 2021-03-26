from moin2hugo.moin_parser import MoinParser

import textwrap


def test_basic_table(formatter_object):
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
    assert formatter_object.format(page) == expected, page.tree_repr()
    assert page.source_text == data


def test_table_escape(formatter_object):
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
    assert formatter_object.format(page) == expected
    assert page.source_text == data


def test_extended_table(formatter_object):
    # TODO
    pass
