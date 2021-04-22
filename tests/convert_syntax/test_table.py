from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.page_tree import Table, TableRow, TableCell
from moin2hugo.config import HugoConfig

import textwrap


def test_basic_table():
    table_text = """\
    ||'''A'''||'''B'''||'''C'''||
    ||1      || 2 ||3      ||
    """
    expected = """\
    | A | B | C |
    |---|---|---|
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
    |---|---|---|
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
    ||<tablestyle="width: 90%;" rowclass="header"> A || B || C ||
    ||<rowstyle="width: 30%;" rowwidth="100px" rowheight="50px"> a || b || c ||
    ||<^> 1 ||<colspan=2> 2 ||
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    table = page.children[0]
    assert isinstance(table, Table)

    row1, row2, row3 = table.children
    assert isinstance(row1, TableRow)
    assert isinstance(row2, TableRow)
    assert isinstance(row3, TableRow)

    cell_11, cell_12, cell_13 = row1.children
    cell_21, cell_22, cell_23 = row2.children
    cell_31, cell_32 = row3.children
    assert isinstance(cell_11, TableCell)
    assert isinstance(cell_12, TableCell)
    assert isinstance(cell_13, TableCell)
    assert isinstance(cell_21, TableCell)
    assert isinstance(cell_22, TableCell)
    assert isinstance(cell_23, TableCell)
    assert isinstance(cell_31, TableCell)
    assert isinstance(cell_32, TableCell)

    assert table.attrs.class_ is None, table.tree_repr()
    assert table.attrs.style == "width: 90%;", table.tree_repr()
    assert table.attrs.width == "90%", table.tree_repr()

    assert row1.attrs.class_ == "header", table.tree_repr()
    assert row2.attrs.style == "width: 30%;", table.tree_repr()
    assert row2.attrs.width == "30%", table.tree_repr()
    assert row2.attrs.height == "50px", table.tree_repr()

    assert cell_31.attrs.valign == "top", table.tree_repr()
    assert cell_32.attrs.colspan == 2, table.tree_repr()


def test_detect_header_heuristically_1():
    table_text = """\
    || '''A''' || '''B''' || '''C''' ||
    ||a ||b || c ||
    """
    expected = """\
    | A | B | C |
    |---|---|---|
    | a | b | c |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    config = HugoConfig(detect_table_header_heuristically=True)
    assert HugoFormatter.format(page, config=config, pagename='PageName') == expected
    assert page.source_text == data


def test_detect_header_heuristically_2():
    table_text = """\
    ||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
    ||a ||b || c ||
    """
    expected = """\
    | A | B | C |
    |---|---|---|
    | a | b | c |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    config = HugoConfig(use_extended_markdown_table=True)
    assert HugoFormatter.format(page, config=config, pagename='PageName') == expected
    assert page.source_text == data


def test_column_alignment():
    table_text = """\
    ||<rowclass="header"> A || B || C || D ||
    ||<(>a ||<:>b ||<)> c || d ||
    ||<style="text-align: left">a ||<style="text-align: center">b ||<style="text-align: right">c ||d ||
    ||a ||b || c || d ||
    """  # noqa
    expected = """\
    | A | B | C | D |
    |:--|:-:|--:|---|
    | a | b | c | d |
    | a | b | c | d |
    | a | b | c | d |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    config = HugoConfig(detect_table_header_heuristically=True)
    assert HugoFormatter.format(page, config=config, pagename='PageName') == expected
    assert page.source_text == data


def test_extended_table_without_extended_markdown_table():
    table_text = """\
    ||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
    ||<|3>a ||<colspan=2>b ||
    ||b ||<rowspan=2>c ||
    ||b ||
    """
    expected = """\
    | A | B | C |
    |:-:|---|---|
    | a |  | b |
    |  | b | c |
    |  | b |  |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_normal_table_with_extended_markdown_table():
    table_text = """\
    ||A ||B ||C ||
    ||a ||b ||c ||
    """
    expected = """\
    |   |   |   |
    |---|---|---|
    | A | B | C |
    | a | b | c |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    config = HugoConfig(use_extended_markdown_table=True)
    assert HugoFormatter.format(page, config=config, pagename='PageName') == expected
    assert page.source_text == data


def test_extended_table_with_extended_markdown_table():
    table_text = """\
    ||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
    ||<|3>a ||<colspan=2>b ||
    ||b ||<rowspan=2>c ||
    ||b ||
    ||a ||<rowspan=2 colspan=2>b ||
    ||a ||
    """
    expected = """\
    {{< extended-markdown-table >}}
    | A | B | C |
    |:-:|---|---|
    | a | > | b |
    | ^ | b | c |
    | ^ | b | ^ |
    | a | > | b |
    | a | ^ | ^ |
    {{< /extended-markdown-table >}}
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    config = HugoConfig(use_extended_markdown_table=True)
    assert HugoFormatter.format(page, config=config, pagename='PageName') == expected
    assert page.source_text == data


def test_invalid_span():
    table_text = """\
    ||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
    ||<|3>a ||<colspan=2>b ||
    """
    expected = """\
    | A | B | C |
    |:-:|---|---|
    | a |  | b |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_all_rows_having_rowstyle():
    table_text = """\
    ||<rowstyle="background-color:#444; color:#eee; text-align:center;">A ||B ||
    ||<rowstyle="text-align:center;">a1 ||b1 ||
    ||<rowstyle="text-align:center;">a2 ||b2 ||
    """
    expected = """\
    | A | B |
    |:-:|:-:|
    | a1 | b1 |
    | a2 | b2 |
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


def test_every_row_seems_header():
    table_text = """\
    ||<rowstyle="background-color:#444; color:#eee; text-align:center;">A ||B ||
    ||<rowstyle="background-color:#444; color:#eee; text-align:center;">a1 ||b1 ||
    ||<rowstyle="background-color:#444; color:#eee; text-align:center;">a2 ||b2 ||
    """
    expected = """\
    | A | B |
    | a1 | b1 |
    | a2 | b2 |
    |---|---|
    """
    data = textwrap.dedent(table_text)
    page = MoinParser.parse(data, 'PageName')
    expected = textwrap.dedent(expected)
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data
