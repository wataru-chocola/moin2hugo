import csv
from typing import Iterator, List, Optional, Set, Tuple

import attr

from moin2hugo.page_tree import Link, Table, TableCell, TableRow, Text

from .base import ParserExtensionAbstract


@attr.s
class CSVArguments:
    delimiter: Optional[str] = attr.ib(default=None)
    quotechar: str = "\x00"  # can't be entered
    quoting: int = csv.QUOTE_NONE


@attr.s
class TableArguments:
    visible: Set[str] = attr.ib(default=attr.Factory(set))
    hiddenindexes: Set[int] = attr.ib(default=attr.Factory(set))
    hiddencols: Set[str] = attr.ib(default=attr.Factory(set))
    linkindexes: Set[int] = attr.ib(default=attr.Factory(set))
    linkcols: Set[str] = attr.ib(default=attr.Factory(set))

    staticcols: List[str] = attr.ib(default=attr.Factory(list))
    staticvals: List[str] = attr.ib(default=attr.Factory(list))

    autofiltercols: Set[str] = attr.ib(default=attr.Factory(set))
    name: Optional[str] = None
    num_cols: int = 0


class ParserCSV(ParserExtensionAbstract):
    name: str = "csv"
    extensions: List[str] = [".csv"]

    @classmethod
    def parse(cls, text: str, parser_name: str, parser_arg_string: Optional[str]) -> Table:
        table = Table()
        first_row = None

        lines = text.lstrip("\n").split("\n")
        csv_args, tbl_args = cls._parse_args(parser_arg_string)
        r = cls._csv_reader(lines, csv_args=csv_args)

        cols: List[str] = r.__next__()
        tbl_args.num_cols = len(cols)

        if cols:
            cols += tbl_args.staticcols
            tbl_args = cls._parse_cols(cols, tbl_args)

            table_row = cls._create_table_row(cols, tbl_args, is_header=True)
            table.add_child(table_row)
        else:
            try:
                first_row = r.__next__()
                tbl_args = cls._parse_cols(
                    tbl_args.staticcols, tbl_args, dummy_col_num=len(first_row)
                )
            except StopIteration:
                pass

        if first_row:
            table_row = cls._create_table_row(first_row, tbl_args)
            table.add_child(table_row)

        for row in r:
            if not row:
                continue
            table_row = cls._create_table_row(row, tbl_args)
            table.add_child(table_row)

        return table

    @classmethod
    def _parse_args(cls, format_args: Optional[str]) -> Tuple[CSVArguments, TableArguments]:
        csv_args = CSVArguments()
        tbl_args = TableArguments()

        if format_args is None:
            return csv_args, tbl_args

        arglist = csv.reader([format_args.strip()], delimiter=" ").__next__()
        for arg in arglist:
            try:
                key, val = arg.split("=", 1)
            except ValueError:
                # handle compatibility with original 'csv' parser
                if arg.startswith("-"):
                    try:
                        tbl_args.hiddenindexes.add(int(arg[1:]) - 1)
                    except ValueError:
                        pass
                else:
                    csv_args.delimiter = arg
                continue

            if key == "separator" or key == "delimiter":
                csv_args.delimiter = val
            elif key == "quotechar":
                csv_args.quotechar = val
                csv_args.quoting = csv.QUOTE_MINIMAL

            elif key == "show":
                tbl_args.visible = set(val.split(","))
            elif key == "hide":
                tbl_args.hiddencols = set(val.split(","))
            elif key == "autofilter":
                tbl_args.autofiltercols = set(val.split(","))
            elif key == "name":
                tbl_args.name = val
            elif key == "static_cols":
                tbl_args.staticcols = val.split(",")
            elif key == "static_vals":
                tbl_args.staticvals = val.split(",")
            elif key == "link":
                tbl_args.linkcols = set(val.split(","))

        diff_colnum = len(tbl_args.staticcols) - len(tbl_args.staticvals)
        if diff_colnum > 0:
            tbl_args.staticvals.extend([""] * diff_colnum)
        elif diff_colnum < 0:
            tbl_args.staticvals = tbl_args.staticvals[: len(tbl_args.staticcols)]

        return csv_args, tbl_args

    @classmethod
    def _csv_reader(cls, lines: List[str], csv_args: CSVArguments) -> Iterator[list]:
        if csv_args.delimiter is None:
            csv_args.delimiter = ";"
            if lines[0]:
                try:
                    preferred_delimiters = [",", "\t", ";", " ", ":"]
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(lines[0], "".join(preferred_delimiters))
                    csv_args.delimiter = dialect.delimiter or ";"
                except csv.Error:
                    pass

        r = csv.reader(
            lines,
            delimiter=csv_args.delimiter,
            quotechar=csv_args.quotechar,
            quoting=csv_args.quoting,
        )
        return r

    @classmethod
    def _parse_cols(
        cls, cols: List[str], tbl_args: TableArguments, dummy_col_num: int = 0
    ) -> TableArguments:
        for colidx, col in enumerate(cols):
            if tbl_args.visible and col not in tbl_args.visible:
                tbl_args.hiddenindexes.add(colidx + dummy_col_num)
            if col in tbl_args.hiddencols:
                tbl_args.hiddenindexes.add(colidx + dummy_col_num)
            if col in tbl_args.linkcols:
                tbl_args.linkindexes.add(colidx + dummy_col_num)
        return tbl_args

    @classmethod
    def _create_table_row(
        cls, row: List[str], table_args: TableArguments, is_header: bool = False
    ) -> TableRow:
        table_row = TableRow(is_header=is_header)

        if len(row) > table_args.num_cols:
            row = row[: table_args.num_cols]
        elif len(row) < table_args.num_cols:
            row.extend([""] * (table_args.num_cols - len(row)))

        if is_header:
            row += table_args.staticcols
        else:
            row += table_args.staticvals

        for colidx, item in enumerate(row):
            if colidx in table_args.hiddenindexes:
                continue

            cell = TableCell()
            if colidx in table_args.linkindexes:
                try:
                    url, item = item.split(" ", 1)
                    if url == "":
                        cell.add_child(Text(item))
                    else:
                        link = Link(url=url)
                        link.add_child(Text(item))
                        cell.add_child(link)
                except ValueError:
                    cell.add_child(Text(item))
            else:
                cell.add_child(Text(item))

            table_row.add_child(cell)

        return table_row
