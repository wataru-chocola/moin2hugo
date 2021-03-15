from moin2hugo.moin_parser import MoinParser

import textwrap


def test_basic_table(formatter_object):
    table_text = """\
    ||'''A'''||'''B'''||'''C'''||
    ||1      || 2 ||3      ||
    """
    expected = """\
    | **A** | **B** | **C** |
    | 1 | 2 | 3 |
    """
    page = MoinParser.parse(textwrap.dedent(table_text), 'PageName')
    expected = textwrap.dedent(expected)
    assert formatter_object.format(page) == expected


def test_extended_table(formatter_object):
    # TODO
    pass
