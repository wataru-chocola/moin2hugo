import collections
import copy
import logging
from typing import DefaultDict, Tuple

import attr

from moin2x.page_tree import (
    Emphasis,
    PageElement,
    Raw,
    Strong,
    Table,
    TableCell,
    TableCellAttr,
    TableRow,
)

logger = logging.getLogger(__name__)


@attr.define
class TableProperty:
    num_of_columns: int = attr.ib(default=0)
    has_span: bool = attr.ib(default=False)
    col_alignments: list[str] = attr.field(factory=list)


def _is_header_row(e: TableRow) -> bool:
    # check if table row is header row by heuristic
    if e.attrs.class_ or e.attrs.bgcolor:
        return True

    # check if all cells are emphasized
    for cell in e.children:
        assert isinstance(cell, TableCell)
        for text in cell.children:
            if not isinstance(text, (Emphasis, Strong)):
                return False

    return True


def _destrongify_table_header(row: TableRow):
    for cell in row.children:
        assert isinstance(cell, TableCell)
        new_elems: list[PageElement] = []
        for elem in cell.children:
            if isinstance(elem, (Emphasis, Strong)):
                new_elems.extend(elem.children)
            else:
                new_elems.append(elem)
        for _i in range(len(cell.children)):
            cell.del_child(0)
        for new_elem in new_elems:
            cell.add_child(new_elem, propagate_source_text=False)


def _make_table_header_heuristically(e: Table) -> Table:
    for row in e.children:
        assert isinstance(row, TableRow)
        if row.is_header:
            continue
        if _is_header_row(row):
            row.is_header = True
            _destrongify_table_header(row)
    return e


def _strip_table_cell(cell: TableCell) -> None:
    for elem in cell.children:
        if elem.content.lstrip() or elem.children:
            elem.content = elem.content.lstrip()
            break
        cell.del_child(0)
    for elem in reversed(cell.children):
        if elem.content.rstrip() or elem.children:
            elem.content = elem.content.rstrip()
            break
        cell.del_child(len(cell.children) - 1)


def _strip_table_cells_in_row(row: TableRow) -> None:
    for cell in row.children:
        assert isinstance(cell, TableCell)
        _strip_table_cell(cell)


def _strip_table_cells(e: Table) -> Table:
    for row in e.children:
        assert isinstance(row, TableRow)
        _strip_table_cells_in_row(row)
    return e


def _get_table_colinfo(tbl: Table) -> Tuple[int, list[str]]:
    num_of_columns = 0
    alignments_of_col: DefaultDict[int, list[str]] = collections.defaultdict(list)
    for i, row in enumerate(tbl.children):
        assert isinstance(row, TableRow)
        if len(row.children) > num_of_columns:
            num_of_columns = len(row.children)

        if row.is_header:
            continue

        # save col's alignment
        for colidx, cell in enumerate(row.children):
            assert isinstance(cell, TableCell)
            tmp_align = "none"
            for align in (cell.attrs.align, row.attrs.align, tbl.attrs.align):
                if align is not None:
                    tmp_align = align
                    break
            alignments_of_col[colidx].append(tmp_align)

    col_alignments: list[str] = []
    for i in range(num_of_columns):
        align = "none"
        counter = collections.Counter(alignments_of_col[i])
        tmp = counter.most_common(1)
        if tmp:
            align = tmp[0][0]
        col_alignments.append(align)

    return (num_of_columns, col_alignments)


def _gen_stub_cell(text: str, attrs: TableCellAttr) -> TableCell:
    new_attrs = copy.deepcopy(attrs)
    stub_cell = TableCell(attrs=new_attrs)
    stub_cell.add_child(Raw(text))
    return stub_cell


def _process_table_span(
    e: Table, *, use_extended_markdown_table: bool = False
) -> Tuple[Table, bool]:
    modified = False

    colspan_stub_marker = ">" if use_extended_markdown_table else ""
    rowspan_stub_marker = "^" if use_extended_markdown_table else ""

    # first, process colspan within each row.
    for row in e.children:
        colidx = 0
        row_cells = copy.copy(row.children)
        for cell in row_cells:
            assert isinstance(cell, TableCell)
            if cell.attrs.colspan and cell.attrs.colspan > 1:
                modified = True
                for i in range(cell.attrs.colspan - 1):
                    stub_cell = _gen_stub_cell(colspan_stub_marker, cell.attrs)
                    stub_cell.attrs.colspan = 1
                    row.add_child(stub_cell, at=colidx)
                cell.attrs.colspan = 1
            colidx += cell.attrs.colspan if cell.attrs.colspan else 1

    # then, process rowspan
    for rowidx, row in enumerate(e.children):
        colidx = 0
        row_cells = copy.copy(row.children)
        for cell in row_cells:
            assert isinstance(cell, TableCell)
            if cell.attrs.rowspan and cell.attrs.rowspan > 1:
                modified = True
                for i in range(cell.attrs.rowspan - 1):
                    stub_cell = _gen_stub_cell(rowspan_stub_marker, cell.attrs)
                    stub_cell.attrs.rowspan = 1
                    try:
                        e.children[rowidx + i + 1].add_child(stub_cell, at=colidx)
                    except IndexError:
                        logger.warning("invalid rowspan")
                        break
                cell.attrs.rowspan = 1
            colidx += cell.attrs.colspan if cell.attrs.colspan else 1

    return e, modified


def process_table(
    e: Table, *, detect_header_heuristic: bool = False, use_extended_markdown_table: bool = False
) -> Tuple[Table, TableProperty]:
    e = _strip_table_cells(e)
    if detect_header_heuristic:
        e = _make_table_header_heuristically(e)

    e, has_span = _process_table_span(e, use_extended_markdown_table=use_extended_markdown_table)
    num_of_columns, col_alignments = _get_table_colinfo(e)
    table_prop = TableProperty(
        num_of_columns=num_of_columns,
        col_alignments=col_alignments,
        has_span=has_span,
    )
    return e, table_prop
