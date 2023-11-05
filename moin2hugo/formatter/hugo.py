import collections
import copy
import html
import logging
import os.path
import re
import textwrap
from functools import partial
from typing import Callable, Dict, List, Optional, Tuple, Union

import attr

from moin2hugo.config import HugoConfig
from moin2hugo.moin_parser_extensions import (
    get_fallback_parser,
    get_parser,
    get_parser_info_from_ext,
)
from moin2hugo.page_tree import (
    AttachmentImage,
    AttachmentInlined,
    AttachmentLink,
    AttachmentTransclude,
    Big,
    BulletList,
    Code,
    Codeblock,
    Comment,
    DefinitionDesc,
    DefinitionList,
    DefinitionTerm,
    Emphasis,
    Heading,
    HorizontalRule,
    Image,
    ImageAttr,
    Interwikilink,
    Link,
    Listitem,
    Macro,
    NumberList,
    ObjectAttr,
    PageElement,
    Pagelink,
    PageRoot,
    Paragraph,
    ParsedText,
    Raw,
    Remark,
    SGMLEntity,
    Small,
    Smiley,
    Strike,
    Strong,
    Sub,
    Sup,
    Table,
    TableCell,
    TableCellAttr,
    TableRow,
    Text,
    Transclude,
    Underline,
    Url,
)
from moin2hugo.path_builder.hugo import HugoPathBuilder

from .base import FormatterBase
from .hugo_utils import (
    MarkdownEscapedText,
    comment_out_shortcode,
    escape_markdown_all,
    escape_markdown_symbols,
    escape_shortcode,
    make_shortcode,
    search_shortcode_delimiter,
)

logger = logging.getLogger(__name__)

smiley2emoji = {
    "X-(": ":angry:",
    ":D": ":smiley:",
    "<:(": ":frowning:",
    ":o": ":astonished:",
    ":(": ":frowning:",
    ":)": ":simple_smile:",
    "B)": ":sunglasses:",
    ":))": ":simple_smile:",
    ";)": ":wink:",
    "/!\\": ":exclamation:",
    "<!>": ":exclamation:",
    "(!)": ":bulb:",
    ":-?": ":stuck_out_tongue_closed_eyes:",
    ":\\": ":astonished:",
    ">:>": ":angry:",
    "|)": ":innocent:",
    ":-(": ":frowning:",
    ":-)": ":simple_smile:",
    "B-)": ":sunglasses:",
    ":-))": ":simple_smile:",
    ";-)": ":wink:",
    "|-)": ":innocent:",
    "(./)": ":white_check_mark:",
    "{OK}": ":thumbsup:",
    "{X}": ":negative_squared_cross_mark:",
    "{i}": ":information_source:",
    "{1}": ":one:",
    "{2}": ":two:",
    "{3}": ":three:",
    "{*}": ":star:",
    "{o}": ":star2:",
}


@attr.s
class TableProperty:
    num_of_columns: int = attr.ib(default=0)
    has_extended_attributes: bool = attr.ib(default=False)
    col_alignments: List[str] = attr.ib(default=attr.Factory(list))


def escape(
    text: str, markdown_escaper: Optional[Callable[[str], str]] = None, in_html: bool = False
) -> MarkdownEscapedText:
    if not in_html:
        if markdown_escaper:
            text = markdown_escaper(text)
    else:
        text = html.escape(text)
    return MarkdownEscapedText(escape_shortcode(text, in_html=in_html))


class HugoFormatter(FormatterBase):
    def __init__(
        self,
        config: Optional[HugoConfig] = None,
        pagename: Optional[str] = None,
        path_builder: Optional[HugoPathBuilder] = None,
    ):
        self.pagename = pagename
        if config:
            self.config = config
        else:
            self.config = HugoConfig()
        self._formatted: Dict[int, str] = {}

        if path_builder:
            self.path_builder = path_builder
        else:
            self.path_builder = HugoPathBuilder()

    def do_format(self, e: PageElement) -> str:
        e_id = id(e)
        if e_id in self._formatted:
            return self._formatted[e_id]
        formatted = self.format_dispatcher(e)
        self._formatted[e_id] = formatted
        return formatted

    def _warn_nontext_in_raw_html(self, e: PageElement):
        msgfmt = "unsupported: non-Text element within %s wouldn't be rendered as intended"
        if any((not isinstance(c, Text) for c in e.descendants)):
            logger.warning(msgfmt % e.__class__.__name__)

    def _separator_line(self, e: PageElement) -> str:
        if e.prev_sibling is not None and type(e.prev_sibling) in (
            Paragraph,
            ParsedText,
            BulletList,
            NumberList,
            DefinitionList,
            Table,
            Heading,
            HorizontalRule,
        ):
            prev_output_lines = self.do_format(e.prev_sibling).splitlines(keepends=True)
            if not prev_output_lines:
                return ""
            elif prev_output_lines[-1] == "\n":  # empty line
                return ""
            elif prev_output_lines[-1].endswith("\n"):
                return "\n"
            else:
                return "\n\n"
        return ""

    def _consolidate(self, e: PageElement) -> PageElement:
        """Consolidate page tree structure destructively."""
        prev = None
        new_children = []
        for c in e.children:
            if isinstance(c, Remark):
                continue
            if isinstance(c, Text):
                if prev and isinstance(prev, Text):
                    prev.content += c.content
                    prev.source_text += c.source_text
                    continue
            c = self._consolidate(c)
            new_children.append(c)
            prev = c
        e.children = new_children
        return e

    # General Objects
    def _generic_container(self, e: PageElement) -> str:
        ret = ""
        for c in e.children:
            ret += self.do_format(c)
        return ret

    def _raw_html(
        self, e: PageElement, tag: str, content: str, tag_attrs: Dict[str, str] = {}
    ) -> str:
        if self.config.goldmark_unsafe:
            self._warn_nontext_in_raw_html(e)
            if tag_attrs:
                tag_attrs_str = " ".join(['%s="%s"' % (k, v) for k, v in tag_attrs.items()])
                start_tag = "<%s %s>" % (tag, tag_attrs_str)
            else:
                start_tag = "<%s>" % tag
            end_tag = "</%s>" % tag
            return start_tag + content + end_tag
        else:
            logger.warning("unsupported: %s (set `goldmark_unsafe` option)" % e.__class__.__name__)
            return "%s" % escape_markdown_all(e.source_text)

    # Basic Elements
    def page_root(self, e: PageRoot) -> str:
        logger.debug("+ Consolidate page structure...")
        new_e = self._consolidate(e)
        logger.debug("+ Format page...")
        return self._generic_container(new_e)

    def raw(self, e: Raw) -> str:
        return escape(e.content, in_html=self._is_in_raw_html(e))

    def paragraph(self, e: Paragraph) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def _is_in_raw_html(self, e: PageElement) -> bool:
        raw_html_types = (Underline, Sup, Sub, Big, Small, AttachmentTransclude, Transclude)
        return any((isinstance(p, raw_html_types) for p in e.parents))

    def _is_at_beginning_of_line(self, e: PageElement) -> bool:
        prev = e.prev_sibling
        while prev:
            if isinstance(prev, Remark):
                prev = prev.prev_sibling
                continue
            if isinstance(prev, Text):
                if not prev.content:
                    prev = prev.prev_sibling
                    continue
                return self.do_format(prev).endswith("\n")
            else:
                return False
            break

        if e.parent and e.parent.in_x(
            [
                Table,
                Emphasis,
                Strong,
                Big,
                Small,
                Underline,
                Strike,
                Sup,
                Sub,
                Code,
                BulletList,
                NumberList,
                DefinitionList,
                Heading,
                Link,
                Pagelink,
                Interwikilink,
                Url,
                AttachmentLink,
                AttachmentTransclude,
                Transclude,
            ]
        ):
            return False

        return True

    def _escape_markdown_text(self, text: str, e: PageElement) -> MarkdownEscapedText:
        """escape markdown symbols depending on context."""
        # escape backslashes at first
        text = re.sub(r"\\", r"\\\\", text)

        # target symbols of which all occurences are escaped
        targets = set(["[", "]", "{", "}", "*", "_", "`", "~", "<", ">", "|", "#"])
        symbol_re = re.compile("([%s])" % re.escape("".join(targets)))

        is_at_beginning_of_line = self._is_at_beginning_of_line(e)

        lines = text.splitlines(keepends=True)
        new_lines = []
        first_line = True
        for line in lines:
            # remove trailing whitespaces pattern which means line break in markdown
            line = re.sub(r"\s+(?=\n)", "", line)

            if e.in_x([TableCell]):
                line = re.sub(r"([-])", r"\\\1", line)
            elif (first_line and is_at_beginning_of_line) or not first_line:
                # remove leading whitespaces
                line = line.lstrip()
                # avoid unintended listitem
                line = re.sub(r"^(\d)\.(?=\s)", r"\1\.", line)  # numbered list
                line = re.sub(r"^([-+])(?=\s)", r"\\\1", line)  # bullet list
                # horizontal rule or headling
                m = re.match(r"^([-=])\1*$", line)
                if m:
                    symbol = m.group(1)
                    line = line.replace(symbol, "\\" + symbol)

            # escape markdown syntax
            line = re.sub(r"\!(?=\[)", r"\!", line)  # image: ![title](image)
            line = re.sub(r":(\w+):", r"\:\1\:", line)  # smiley: :smiley:

            # escape markdown special symbols
            line = re.sub(symbol_re, r"\\\1", line)

            new_lines.append(line)
            first_line = False
        return MarkdownEscapedText("".join(new_lines))

    def text(self, e: Text) -> str:
        in_html = self._is_in_raw_html(e)
        ret = ""
        if not in_html:
            ret += self._separator_line(e)
        ret += escape(
            e.content, markdown_escaper=partial(self._escape_markdown_text, e=e), in_html=in_html
        )
        return ret

    def sgml_entity(self, e: SGMLEntity) -> str:
        return escape(e.content, in_html=self._is_in_raw_html(e))

    # Moinwiki Special Objects
    def macro(self, e: Macro) -> str:
        if e.macro_name == "BR":
            if not e.in_x([TableCell]):
                return "  \n"
            else:
                if self.config.goldmark_unsafe:
                    return "<br />"
                else:
                    logger.warning("unsupported: macro <<BR>> inside table")
                    return escape(
                        e.source_text,
                        markdown_escaper=escape_markdown_all,
                        in_html=self._is_in_raw_html(e),
                    )
        elif e.macro_name == "TableOfContents":
            return ""
        else:
            logger.warning("unsupported: macro <<%s>>" % e.macro_name)
            if e.markup:
                return self.text(Text(e.markup))
        return ""

    def comment(self, comment: Comment) -> str:
        return ""

    def smiley(self, smiley: Smiley) -> str:
        return smiley2emoji[smiley.content]

    def remark(self, remark: Remark) -> str:
        return ""

    # Codeblock
    def codeblock(self, e: Codeblock) -> str:
        lines = e.content.splitlines()
        if lines and not lines[0]:
            lines = lines[1:]
        if lines and not lines[-1].strip():
            lines = lines[:-1]

        codeblock_delimiter = "```"
        for line in lines:
            m = re.search(r"^`{3,}", line)
            if m and len(m.group(0)) >= len(codeblock_delimiter):
                codeblock_delimiter = "`" * (len(m.group(0)) + 1)

        content = "\n".join(lines)
        content = comment_out_shortcode(content)
        if search_shortcode_delimiter(content):
            logger.error("cannot handle non-paired shortcode delimiter in codeblock")
            logger.error("MUST modify it manually or hugo will fail to build")

        ret = self._separator_line(e)
        if e.syntax_id:
            ret += "%s%s\n" % (codeblock_delimiter, e.syntax_id)
        else:
            ret += "%s\n" % (codeblock_delimiter)
        ret += content
        ret += "\n%s" % codeblock_delimiter
        return ret

    def parsed_text(self, e: ParsedText) -> str:
        if e.parser_name == "":
            parser_name = "text"
        else:
            parser_name = e.parser_name

        parser = get_parser(parser_name)
        if not parser:
            logger.warning("unsupported: parser=%s" % e.parser_name)
            parser = get_fallback_parser()
        elem = parser.parse(e.content, e.parser_name, e.parser_args)
        return self.format(elem)

    # Table
    def _strip_table_cells(self, e: Table) -> Table:
        for row in e.children:
            assert isinstance(row, TableRow)
            for cell in row.children:
                assert isinstance(cell, TableCell)
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
        return e

    def _is_header_row(self, e: TableRow) -> bool:
        # check if table row is header row by heuristic
        if e.attrs.class_ or e.attrs.bgcolor:
            return True
        for cell in e.children:
            assert isinstance(cell, TableCell)
            for text in cell.children:
                if not isinstance(text, (Emphasis, Strong)):
                    return False
        return True

    def _destrongfy_table_header(self, row: TableRow):
        for cell in row.children:
            assert isinstance(cell, TableCell)
            new_elems = []
            for elem in cell.children:
                if isinstance(elem, (Emphasis, Strong)):
                    new_elems.extend(elem.children)
                else:
                    new_elems.append(elem)
            for i in range(len(cell.children)):
                cell.del_child(0)
            for new_elem in new_elems:
                cell.add_child(new_elem, propagate_source_text=False)

    def _make_table_header_heuristically(self, e: Table) -> Table:
        for row in e.children:
            assert isinstance(row, TableRow)
            if row.is_header:
                continue
            elif self._is_header_row(row):
                row.is_header = True
                self._destrongfy_table_header(row)
        return e

    def _get_table_colinfo(self, tbl: Table) -> Tuple[int, List[str]]:
        num_of_columns = 0
        alignments_of_col = collections.defaultdict(list)
        for i, row in enumerate(tbl.children):
            assert isinstance(row, TableRow)
            if len(row.children) > num_of_columns:
                num_of_columns = len(row.children)

            if not row.is_header:
                for colidx, cell in enumerate(row.children):
                    assert isinstance(cell, TableCell)
                    tmp_align = "none"
                    for align in (cell.attrs.align, row.attrs.align, tbl.attrs.align):
                        if align is not None:
                            tmp_align = align
                            break
                    alignments_of_col[colidx].append(tmp_align)

        col_alignments = []
        for i in range(num_of_columns):
            align = "none"
            counter = collections.Counter(alignments_of_col[i])
            tmp = counter.most_common(1)
            if tmp:
                align = tmp[0][0]
            col_alignments.append(align)

        return (num_of_columns, col_alignments)

    def _process_table_span(self, e: Table) -> Tuple[Table, bool]:
        def _gen_stub(text: str, attrs: TableCellAttr) -> TableCell:
            new_attrs = copy.deepcopy(attrs)
            stub_cell = TableCell(attrs=new_attrs)
            stub_cell.add_child(Raw(text))
            return stub_cell

        modified = False
        # first, process colspan within each row.
        for row in e.children:
            colidx = 0
            row_cells = copy.copy(row.children)
            for cell in row_cells:
                assert isinstance(cell, TableCell)
                if cell.attrs.colspan and cell.attrs.colspan > 1:
                    modified = True
                    for i in range(cell.attrs.colspan - 1):
                        stub_text = ">" if self.config.use_extended_markdown_table else ""
                        stub_cell = _gen_stub(stub_text, cell.attrs)
                        stub_cell.attrs.colspan = 1
                        row.add_child(_gen_stub(stub_text, cell.attrs), at=colidx)
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
                        stub_text = "^" if self.config.use_extended_markdown_table else ""
                        stub_cell = _gen_stub(stub_text, cell.attrs)
                        stub_cell.attrs.rowspan = 1
                        try:
                            e.children[rowidx + i + 1].add_child(stub_cell, at=colidx)
                        except IndexError:
                            logger.warning("invalid rowspan")
                            break
                    cell.attrs.rowspan = 1
                colidx += cell.attrs.colspan if cell.attrs.colspan else 1
        return e, modified

    def _process_table(self, e: Table) -> Tuple[Table, TableProperty]:
        e = self._strip_table_cells(e)
        if self.config.detect_table_header_heuristically:
            e = self._make_table_header_heuristically(e)
        e, has_extended_attributes = self._process_table_span(e)
        num_of_columns, col_alignments = self._get_table_colinfo(e)
        table_prop = TableProperty(
            num_of_columns=num_of_columns,
            col_alignments=col_alignments,
            has_extended_attributes=has_extended_attributes,
        )
        return e, table_prop

    def table(self, e: Table) -> str:
        ret = self._separator_line(e)
        md_table = ""
        e, table_prop = self._process_table(e)

        def _make_header_separator():
            map_sep = {"left": ":--", "right": "--:", "center": ":-:"}
            seps = [map_sep.get(align, "---") for align in table_prop.col_alignments]
            return "|%s|\n" % "|".join(seps)

        in_header = True
        for i, row in enumerate(e.children):
            assert isinstance(row, TableRow)
            if in_header and row.is_header is False:
                if i == 0:
                    md_table += "|%s|\n" % "|".join(["   "] * table_prop.num_of_columns)
                md_table += _make_header_separator()
                in_header = False
            md_table += self.do_format(row)
        if in_header:
            md_table += _make_header_separator()
            in_header = False

        if self.config.use_extended_markdown_table and table_prop.has_extended_attributes:
            shortcode = "extended-markdown-table"
            tmp = "{{< %s >}}\n" % shortcode
            tmp += "%s\n" % md_table.rstrip()
            tmp += "{{< /%s >}}\n" % shortcode
            md_table = tmp
        ret += md_table
        return ret

    def table_row(self, e: TableRow) -> str:
        ret = []
        for c in e.children:
            assert isinstance(c, TableCell)
            ret.append(self.do_format(c))
        return "|" + "|".join(ret) + "|\n"

    def table_cell(self, e: TableCell) -> str:
        return " %s " % self._generic_container(e).strip()

    # Heading / Horizontal Rule
    def heading(self, e: Heading) -> str:
        ret = self._separator_line(e)
        max_level = 6
        heading_level = e.depth
        if self.config.increment_heading_level:
            heading_level += 1
        heading_level = min(heading_level, max_level)
        content = escape(
            e.content,
            markdown_escaper=partial(self._escape_markdown_text, e=e),
            in_html=self._is_in_raw_html(e),
        )
        ret += "#" * heading_level + " " + content + "\n\n"
        return ret

    def rule(self, e: HorizontalRule) -> str:
        return "-" * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, e: Underline) -> str:
        return self._raw_html(e, "u", content=self._generic_container(e))

    def strike(self, e: Strike) -> str:
        return "~~%s~~" % self._generic_container(e)

    def small(self, e: Small) -> str:
        return self._raw_html(e, "small", content=self._generic_container(e))

    def big(self, e: Big) -> str:
        return self._raw_html(e, "big", content=self._generic_container(e))

    def _process_flanking_delimiter(self, e: Union[Strong, Emphasis]) -> Tuple[str, str, str]:
        preceding_text = ""
        inner_text = self._generic_container(e)
        following_text = ""

        if not self._is_at_beginning_of_line(e):
            m_leading_unicode_spaces = re.search(r"^\s+", inner_text)
            if m_leading_unicode_spaces:
                preceding_text = m_leading_unicode_spaces.group(0)
                inner_text = re.sub(r"^\s+", "", inner_text)
            elif re.search(r"^[^\w\s*]", inner_text):
                preceding_text = " "

        m_trailing_unicode_spaces = re.search(r"\s+$", inner_text)
        if m_trailing_unicode_spaces:
            following_text = m_trailing_unicode_spaces.group(0)
            inner_text = re.sub(r"\s+$", "", inner_text)
        elif re.search(r"[^\w\s]$", inner_text):
            if not re.search(r"(?<!\\)[*]$", inner_text):
                following_text = " "

        return preceding_text, inner_text, following_text

    def strong(self, e: Strong) -> str:
        preceding_text, inner_text, following_text = self._process_flanking_delimiter(e)
        return preceding_text + "**%s**" % inner_text + following_text

    def emphasis(self, e: Emphasis) -> str:
        preceding_text, inner_text, following_text = self._process_flanking_delimiter(e)
        return preceding_text + "*%s*" % inner_text + following_text

    # Decoration (cannot be multilined)
    def sup(self, e: Sup) -> str:
        content = escape(e.content, in_html=True)
        return self._raw_html(e, "sup", content=content)

    def sub(self, e: Sub) -> str:
        content = escape(e.content, in_html=True)
        return self._raw_html(e, "sub", content=content)

    def code(self, e: Code) -> str:
        text = e.content
        if text.startswith("`"):
            text = " " + text
        if text.endswith("`"):
            text = text + " "

        # noqa: refer: https://meta.stackexchange.com/questions/82718/how-do-i-escape-a-backtick-within-in-line-code-in-markdown
        text = comment_out_shortcode(text)
        if search_shortcode_delimiter(text):
            logger.error("cannot handle non-paired shortcode delimiter in code")
            logger.error("MUST modify it manually or hugo will fail to build")

        len_of_longest_backticks = 0
        if "`" in text:
            len_of_longest_backticks = max([len(s) for s in re.findall(r"`+", text)])
        delimiter = "`" * (len_of_longest_backticks + 1)
        return "%s%s%s" % (delimiter, text, delimiter)

    # Links
    def url(self, e: Url) -> str:
        # e.content must be valid as URL
        encoded_url = escape(
            e.content,
            markdown_escaper=partial(escape_markdown_symbols, symbols=["<", ">"]),
            in_html=self._is_in_raw_html(e),
        )
        return "<%s>" % encoded_url

    def _link(
        self,
        target: MarkdownEscapedText,
        description: MarkdownEscapedText,
        title: Optional[MarkdownEscapedText] = None,
    ) -> str:
        if title is not None:
            return '[%s](%s "%s")' % (description, target, title)
        else:
            return "[%s](%s)" % (description, target)

    def link(self, e: Link) -> str:
        url = escape(
            e.url,
            markdown_escaper=partial(escape_markdown_symbols, symbols=["(", ")", "[", "]", '"']),
            in_html=self._is_in_raw_html(e),
        )
        description = MarkdownEscapedText(self._generic_container(e))
        title = None
        if e.attrs.title is not None:
            title = escape(
                e.attrs.title,
                markdown_escaper=escape_markdown_all,
                in_html=self._is_in_raw_html(e),
            )
        return self._link(url, description, title=title)

    def pagelink(self, e: Pagelink) -> str:
        link_path = self.path_builder.page_url(e.pagename, relative_base=self.pagename)
        if e.queryargs:
            # just ignore them
            pass
        if e.anchor:
            link_path += "#%s" % e.anchor
        escaped_link_path = escape(
            link_path,
            markdown_escaper=partial(escape_markdown_symbols, symbols=["(", ")", "[", "]", '"']),
            in_html=self._is_in_raw_html(e),
        )
        description = MarkdownEscapedText(self._generic_container(e))
        return self._link(escaped_link_path, description)

    def interwikilink(self, e: Interwikilink) -> str:
        logger.warning("unsupported: interwiki=%s" % e.source_text)
        ret = escape(
            e.source_text,
            markdown_escaper=partial(self._escape_markdown_text, e=e),
            in_html=self._is_in_raw_html(e),
        )
        return ret

    def attachment_link(self, e: AttachmentLink) -> str:
        link_path = self.path_builder.attachment_url(
            e.pagename, e.filename, relative_base=self.pagename
        )
        if e.queryargs:
            # just ignore them
            pass
        escaped_link_path = escape_markdown_symbols(link_path, symbols=["(", ")", "[", "]", '"'])
        description = MarkdownEscapedText(self._generic_container(e))
        title = None
        if e.attrs.title is not None:
            title = escape(
                e.attrs.title,
                markdown_escaper=escape_markdown_all,
                in_html=self._is_in_raw_html(e),
            )
        return self._link(escaped_link_path, description, title)

    # Itemlist
    def bullet_list(self, e: BulletList) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def number_list(self, e: NumberList) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def listitem(self, e: Listitem) -> str:
        ret = ""
        if isinstance(e.parent, BulletList):
            marker = "* "
        elif isinstance(e.parent, NumberList):
            marker = "1. "
        else:
            raise Exception("Invalid Page Tree Structure")

        paragraph_indent = " " * len(marker)
        first_line = True
        for c in e.children:
            text = self.do_format(c)
            if isinstance(c, BulletList) or isinstance(c, NumberList):
                ret += textwrap.indent(text, " " * 4)
            elif isinstance(c, ParsedText):
                ret += "\n"
                ret += textwrap.indent(text, paragraph_indent)
                ret += "\n"
            else:
                for line in text.splitlines(keepends=True):
                    if first_line:
                        ret += marker + line
                        first_line = False
                    elif line in ["\n", ""]:
                        ret += line
                    else:
                        ret += paragraph_indent + line
        return ret

    def definition_list(self, e: DefinitionList) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def definition_term(self, e: DefinitionTerm) -> str:
        dt = self._generic_container(e)
        if not dt:
            return ""
        dt = dt.rstrip(" ")
        preceding_newline = ""
        if e.prev_sibling is not None:
            preceding_newline = "\n"
        return preceding_newline + dt + "\n"

    def definition_desc(self, e: DefinitionDesc) -> str:
        ret = ""
        indent = " " * 4
        marker = ":   "
        first_line = True
        for c in e.children:
            text = self.do_format(c)
            if isinstance(c, ParsedText):
                if c.prev_sibling is not None:
                    text = "\n" + text
                text += "\n"

            for line in text.splitlines(keepends=True):
                if first_line:
                    ret += marker + line
                    first_line = False
                elif line in ["\n", ""]:
                    ret += line
                else:
                    ret += indent + line
        return ret

    # Image / Object Embedding
    def _transclude(self, url: str, e: PageElement, objattr: Optional[ObjectAttr] = None) -> str:
        tag_attrs: dict[str, str] = collections.OrderedDict([("data", url)])
        if objattr:
            if objattr.mimetype:
                tag_attrs["type"] = escape(objattr.mimetype, in_html=True)
            if objattr.title:
                tag_attrs["name"] = escape(objattr.title, in_html=True)
            if objattr.width:
                tag_attrs["width"] = escape(objattr.width, in_html=True)
            if objattr.height:
                tag_attrs["height"] = escape(objattr.height, in_html=True)
        return self._raw_html(e, "object", content=self._generic_container(e), tag_attrs=tag_attrs)

    def attachment_transclude(self, e: AttachmentTransclude) -> str:
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)
        url = escape(url, in_html=True)
        return self._transclude(url, e, e.attrs)

    def transclude(self, e: Transclude) -> str:
        url = self.path_builder.page_url(e.pagename, relative_base=self.pagename)
        url = escape(url, in_html=True)
        return self._transclude(url, e, e.attrs)

    def attachment_inlined(self, e: AttachmentInlined) -> str:
        ret = ""
        in_html = self._is_in_raw_html(e)
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)
        escaped_url = escape(
            url,
            partial(escape_markdown_symbols, symbols=["(", ")", "[", "]", '"']),
            in_html=in_html,
        )

        filepath = self.path_builder.attachment_filepath(e.pagename, e.filename)
        with open(filepath, "r") as f:
            attachment_content = f.read()

        _, ext = os.path.splitext(e.filename)
        parser_name, parser_args = get_parser_info_from_ext(ext)
        if parser_name is None:
            parser_name = "text"
        ret += self.do_format(
            ParsedText(
                parser_name=parser_name, parser_args=parser_args, content=attachment_content
            )
        )
        if not ret.endswith("\n"):
            ret += "\n"
        ret += "\n"
        link_text = escape(e.link_text, markdown_escaper=escape_markdown_all, in_html=in_html)
        ret += self._link(escaped_url, link_text)
        return ret

    def _figure_shortcode(
        self, src: MarkdownEscapedText, e: PageElement, imgattr: Optional[ImageAttr] = None
    ) -> str:
        tag_attrs: Dict[str, Optional[str]] = collections.OrderedDict([("src", str(src))])
        if imgattr is not None:
            if imgattr.title is not None:
                tag_attrs["title"] = escape(imgattr.title, in_html=True)
            if imgattr.alt is not None:
                tag_attrs["alt"] = escape(imgattr.alt, in_html=True)
            if imgattr.width:
                tag_attrs["width"] = escape(imgattr.width, in_html=True)
            if imgattr.height:
                tag_attrs["height"] = escape(imgattr.height, in_html=True)
        return make_shortcode("figure", attrs=tag_attrs)

    def _image(
        self, src: MarkdownEscapedText, imgattr: Optional[ImageAttr] = None, in_html: bool = False
    ) -> str:
        if imgattr is not None and imgattr.alt is not None:
            alt = escape(imgattr.alt, markdown_escaper=escape_markdown_all, in_html=in_html)
        else:
            alt = MarkdownEscapedText("")

        if imgattr is not None and imgattr.title is not None:
            title = escape(imgattr.title, markdown_escaper=escape_markdown_all, in_html=in_html)
            return '![{alt}]({src} "{title}")'.format(alt=alt, src=src, title=title)
        else:
            return "![{alt}]({src})".format(alt=alt, src=src)

    def image(self, e: Image) -> str:
        in_html = self._is_in_raw_html(e)
        src = escape(
            e.src,
            markdown_escaper=partial(escape_markdown_symbols, symbols=['"', "[", "]", "(", ")"]),
            in_html=in_html,
        )
        if self.config.use_figure_shortcode and (e.attrs.width or e.attrs.height):
            return self._figure_shortcode(src, e, e.attrs)
        else:
            return self._image(src, e.attrs, in_html=in_html)

    def attachment_image(self, e: AttachmentImage) -> str:
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)
        in_html = self._is_in_raw_html(e)
        url = escape(
            url,
            markdown_escaper=partial(escape_markdown_symbols, symbols=['"', "[", "]", "(", ")"]),
            in_html=in_html,
        )
        if self.config.use_figure_shortcode and (e.attrs.width or e.attrs.height):
            return self._figure_shortcode(url, e, e.attrs)
        else:
            return self._image(url, e.attrs, in_html=in_html)
