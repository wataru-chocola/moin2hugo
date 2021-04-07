from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.page_tree import Table, TableRow, TableCell

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


def test_table_attrs():
    table_text = """\
    ||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
    ||<^> 1 ||<colspan=2> 2 ||
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    table = page.children[0]
    assert isinstance(table, Table)

    row1, row2 = table.children
    assert isinstance(row1, TableRow)
    assert isinstance(row2, TableRow)

    cell_11, cell_12, cell_13 = row1.children
    cell_21, cell_22 = row2.children
    assert isinstance(cell_11, TableCell)
    assert isinstance(cell_12, TableCell)
    assert isinstance(cell_13, TableCell)
    assert isinstance(cell_21, TableCell)
    assert isinstance(cell_22, TableCell)

    assert table.attrs.class_ is None, table.tree_repr()
    assert table.attrs.style == "width: 90%;", table.tree_repr()

    assert row1.attrs.class_ == "header", table.tree_repr()
    assert row1.attrs.style == "width: 30%;", table.tree_repr()

    assert cell_21.attrs.valign == "top", table.tree_repr()
    assert cell_22.attrs.colspan == 2, table.tree_repr()


def test_extended_table():
    # TODO
    pass
