import collections
import html
import logging
import os.path
import re
import textwrap
from functools import partial
from typing import Callable, Dict, Optional

import attr

from moin2x.formatter.base import FormatterBase
from moin2x.formatter.utils.markdown import (
    MarkdownEscapedText,
    adjust_surrounding_space_of_asterisk_text,
    escape_markdown_all,
    escape_markdown_symbols,
    escape_markdown_text,
    get_codeblock_delimiter,
)
from moin2x.formatter.utils.markdown_table import TableProperty, process_table
from moin2x.moin_parser_extensions import get_parser_info_from_ext
from moin2x.page_tree import (
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
    TableRow,
    Text,
    Transclude,
    Underline,
    Url,
)
from moin2x.path_builder import MarkdownPathBuilder, PathBuilder

from .utils.smiley2emoji import smiley2emoji

logger = logging.getLogger(__name__)


@attr.define
class MarkdownFormatterConfig:
    detect_table_header_heuristically: bool = True
    increment_heading_level: bool = True
    allow_raw_html: bool = True
    allow_emoji: bool = False
    # TODO
    use_extended_markdown_table: bool = False


class MarkdownFormatter(FormatterBase):
    # types of elements which generateis raw html
    raw_html_types = (Underline, Sup, Sub, Big, Small, AttachmentTransclude, Transclude)

    def __init__(
        self,
        *,
        config: Optional[MarkdownFormatterConfig] = None,
        pagename: Optional[str] = None,
        path_builder: Optional[PathBuilder] = None,
    ):
        self._formatted: dict[int, str] = {}

        self.pagename = pagename
        self.config = config if config is not None else MarkdownFormatterConfig()

        if path_builder:
            self.path_builder = path_builder
        else:
            self.path_builder = MarkdownPathBuilder()

    def do_format(self, e: PageElement) -> str:
        # cache format result because a lot of elements are formatted repeatedly
        e_id = id(e)
        if e_id in self._formatted:
            return self._formatted[e_id]
        formatted = self.format_dispatcher(e)
        self._formatted[e_id] = formatted
        return formatted

    def escape(
        self,
        text: str,
        markdown_escaper: Optional[Callable[[str], str]] = None,
        in_html: bool = False,
    ) -> MarkdownEscapedText:
        if in_html:
            return MarkdownEscapedText(html.escape(text))
        if markdown_escaper:
            return MarkdownEscapedText(markdown_escaper(text))
        return MarkdownEscapedText(text)

    def _newline_if_needed(self, e: PageElement) -> str:
        """Insert new line(s) to separate elements."""
        if e.prev_sibling is None:
            return ""

        if type(e.prev_sibling) not in (
            Paragraph,
            ParsedText,
            BulletList,
            NumberList,
            DefinitionList,
            Table,
            Heading,
            HorizontalRule,
        ):
            return ""

        prev_output_lines = self.do_format(e.prev_sibling).splitlines(keepends=True)
        if not prev_output_lines:
            return ""

        lastline = prev_output_lines[-1]
        if lastline == "\n":  # empty line
            return ""
        elif lastline.endswith("\n"):  # line with newline
            return "\n"
        else:  # line without newline
            return "\n\n"

    def _consolidate(self, e: PageElement) -> PageElement:
        """Consolidate page tree structure destructively."""
        prev = None
        new_children: list[PageElement] = []
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
    def _raw_html(
        self, e: PageElement, tag: str, content: str, tag_attrs: Dict[str, str] = {}
    ) -> str:
        if not self.config.allow_raw_html:
            logger.warning("unsupported: %s (set `allow_raw_html` option)" % e.__class__.__name__)
            return "%s" % escape_markdown_all(e.source_text)

        if any((not isinstance(c, Text) for c in e.descendants)):
            msgfmt = "unsupported: non-Text element within %s wouldn't be rendered as intended"
            logger.warning(msgfmt % e.__class__.__name__)

        if tag_attrs:
            tag_attrs_str = " ".join(['%s="%s"' % (k, v) for k, v in tag_attrs.items()])
            start_tag = "<%s %s>" % (tag, tag_attrs_str)
        else:
            start_tag = "<%s>" % tag
        end_tag = "</%s>" % tag
        return start_tag + content + end_tag

    # Basic Elements
    def page_root(self, e: PageRoot) -> str:
        logger.debug("+ Consolidate page structure...")
        new_e = self._consolidate(e)
        logger.debug("+ Format page...")
        return self.format_children(new_e)

    def raw(self, e: Raw) -> str:
        return self.escape(e.content, in_html=self._is_in_raw_html(e))

    def paragraph(self, e: Paragraph) -> str:
        return self._newline_if_needed(e) + self.format_children(e)

    def _is_in_raw_html(self, e: PageElement) -> bool:
        return self.config.allow_raw_html and any(
            (isinstance(p, self.raw_html_types) for p in e.parents)
        )

    # TODO: too weak for change
    def _is_at_beginning_of_line(self, e: PageElement) -> bool:
        # check if previous element at the same level ends with newline
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
            return False

        # check if parent element is something which starts with symbol
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

    def text(self, e: Text) -> str:
        in_html = self._is_in_raw_html(e)
        ret = ""
        if not in_html:
            ret += self._newline_if_needed(e)
        ret += self.escape(
            e.content,
            markdown_escaper=partial(
                escape_markdown_text, e=e, at_beginning_of_line=self._is_at_beginning_of_line(e)
            ),
            in_html=in_html,
        )
        return ret

    def sgml_entity(self, e: SGMLEntity) -> str:
        return self.escape(e.content, in_html=self._is_in_raw_html(e))

    def _macro_br(self, e: Macro) -> str:
        if e.in_x([TableCell]):
            if self.config.allow_raw_html:
                return "<br />"
            else:
                logger.warning("unsupported: macro <<BR>> inside table")
                return self.escape(
                    e.source_text,
                    markdown_escaper=escape_markdown_all,
                    in_html=self._is_in_raw_html(e),
                )
        return "  \n"

    # Moinwiki Special Objects
    def macro(self, e: Macro) -> str:
        match e.macro_name:
            case "BR":
                return self._macro_br(e)
            case "TableOfContents":
                return ""
            case _:
                logger.warning("unsupported: macro <<%s>>" % e.macro_name)
                if e.markup:
                    return self.text(Text(e.markup))
                return ""

    def comment(self, comment: Comment) -> str:
        return ""

    def smiley(self, smiley: Smiley) -> str:
        if not self.config.allow_emoji:
            return self.text(Text(smiley.content))
        return smiley2emoji(smiley.content)

    def remark(self, remark: Remark) -> str:
        return ""

    # Codeblock
    def codeblock(self, e: Codeblock) -> str:
        (codeblock_delimiter, content) = get_codeblock_delimiter(e.content)

        ret = self._newline_if_needed(e)
        if e.syntax_id:
            ret += "%s%s\n" % (codeblock_delimiter, e.syntax_id)
        else:
            ret += "%s\n" % (codeblock_delimiter)
        ret += content
        ret += "\n%s" % codeblock_delimiter
        return ret

    # Table
    def _table(self, e: Table, table_prop: TableProperty) -> str:
        md_table = ""

        def _make_header_separator():
            map_sep = {"left": ":--", "right": "--:", "center": ":-:"}
            seps = [map_sep.get(align, "---") for align in table_prop.col_alignments]
            return "|%s|\n" % "|".join(seps)

        in_header = True
        for i, row in enumerate(e.children):
            assert isinstance(row, TableRow)
            if in_header and row.is_header is False:
                if i == 0:
                    # add dummy header if no header found
                    md_table += "|%s|\n" % "|".join(["   "] * table_prop.num_of_columns)
                md_table += _make_header_separator()
                in_header = False
            md_table += self.do_format(row)
        if in_header:
            md_table += _make_header_separator()
            in_header = False

        return md_table

    def table(self, e: Table) -> str:
        ret = self._newline_if_needed(e)
        e, table_prop = process_table(
            e,
            detect_header_heuristic=self.config.detect_table_header_heuristically,
            use_extended_markdown_table=self.config.use_extended_markdown_table,
        )

        ret += self._table(e, table_prop)
        return ret

    def table_row(self, e: TableRow) -> str:
        ret: list[str] = []
        for c in e.children:
            assert isinstance(c, TableCell)
            ret.append(self.do_format(c))
        return "|" + "|".join(ret) + "|\n"

    def table_cell(self, e: TableCell) -> str:
        return " %s " % self.format_children(e).strip()

    # Heading / Horizontal Rule
    def heading(self, e: Heading) -> str:
        ret = self._newline_if_needed(e)
        max_level = 6
        heading_level = e.depth
        if self.config.increment_heading_level:
            heading_level += 1
        heading_level = min(heading_level, max_level)
        content = self.escape(
            e.content,
            markdown_escaper=partial(
                escape_markdown_text, e=e, at_beginning_of_line=self._is_at_beginning_of_line(e)
            ),
            in_html=self._is_in_raw_html(e),
        )
        ret += "#" * heading_level + " " + content + "\n\n"
        return ret

    def rule(self, e: HorizontalRule) -> str:
        return "-" * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, e: Underline) -> str:
        return self._raw_html(e, "u", content=self.format_children(e))

    def strike(self, e: Strike) -> str:
        return "~~%s~~" % self.format_children(e)

    def small(self, e: Small) -> str:
        return self._raw_html(e, "small", content=self.format_children(e))

    def big(self, e: Big) -> str:
        return self._raw_html(e, "big", content=self.format_children(e))

    def strong(self, e: Strong) -> str:
        preceding_text, inner_text, following_text = adjust_surrounding_space_of_asterisk_text(
            self.format_children(e), at_begenning_of_line=self._is_at_beginning_of_line(e)
        )
        return f"{preceding_text}**{inner_text}**{following_text}"

    def emphasis(self, e: Emphasis) -> str:
        preceding_text, inner_text, following_text = adjust_surrounding_space_of_asterisk_text(
            self.format_children(e), at_begenning_of_line=self._is_at_beginning_of_line(e)
        )
        return f"{preceding_text}*{inner_text}*{following_text}"

    # Decoration (cannot be multilined)
    def sup(self, e: Sup) -> str:
        content = self.escape(e.content, in_html=True)
        return self._raw_html(e, "sup", content=content)

    def sub(self, e: Sub) -> str:
        content = self.escape(e.content, in_html=True)
        return self._raw_html(e, "sub", content=content)

    def _code(self, codeText: str) -> str:
        # if codeText either starts or ends with a backtick, add a space to
        # avoid it being interpreted as a delimiter
        if codeText.startswith("`"):
            codeText = " " + codeText
        if codeText.endswith("`"):
            codeText = codeText + " "

        len_of_longest_backticks = 0
        if "`" in codeText:
            len_of_longest_backticks = max([len(s) for s in re.findall(r"`+", codeText)])
        delimiter = "`" * (len_of_longest_backticks + 1)
        return f"{delimiter}{codeText}{delimiter}"

    def code(self, e: Code) -> str:
        return self._code(e.content)

    # Links
    def url(self, e: Url) -> str:
        # e.content must be valid as URL
        encoded_url = self.escape(
            e.content,
            markdown_escaper=partial(escape_markdown_symbols, symbols=["<", ">"]),
            in_html=self._is_in_raw_html(e),
        )
        return f"<{encoded_url}>"

    def _link(
        self,
        target: str,
        description: str,
        *,
        title: Optional[str] = None,
        in_html: bool,
    ) -> str:
        escaped_target = self.escape(
            target,
            markdown_escaper=partial(escape_markdown_symbols, symbols=["(", ")", "[", "]", '"']),
            in_html=in_html,
        )
        if title is not None:
            escaped_title = self.escape(
                title,
                markdown_escaper=escape_markdown_all,
                in_html=in_html,
            )
            return f'[{description}]({escaped_target} "{escaped_title}")'
        return f"[{description}]({escaped_target})"

    def link(self, e: Link) -> str:
        description = self.format_children(e)
        return self._link(e.url, description, title=e.attrs.title, in_html=self._is_in_raw_html(e))

    def pagelink(self, e: Pagelink) -> str:
        link_path = self.path_builder.page_url(e.pagename, relative_base=self.pagename)
        if e.queryargs:
            # just ignore them
            pass
        if e.anchor:
            link_path += f"#{e.anchor}"
        description = self.format_children(e)
        return self._link(link_path, description, in_html=self._is_in_raw_html(e))

    def interwikilink(self, e: Interwikilink) -> str:
        logger.warning("unsupported: interwiki=%s" % e.source_text)
        text = e.replace_self(Text(e.source_text))
        return self.text(text)

    def attachment_link(self, e: AttachmentLink) -> str:
        link_path = self.path_builder.attachment_url(
            e.pagename, e.filename, relative_base=self.pagename
        )
        if e.queryargs:
            # just ignore them
            pass
        description = self.format_children(e)
        return self._link(
            link_path, description, title=e.attrs.title, in_html=self._is_in_raw_html(e)
        )

    # Itemlist
    def bullet_list(self, e: BulletList) -> str:
        return self._newline_if_needed(e) + self.format_children(e)

    def number_list(self, e: NumberList) -> str:
        return self._newline_if_needed(e) + self.format_children(e)

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
        return self._newline_if_needed(e) + self.format_children(e)

    def definition_term(self, e: DefinitionTerm) -> str:
        dt = self.format_children(e)
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
        url = self.escape(url, in_html=True)
        tag_attrs: dict[str, str] = collections.OrderedDict([("data", url)])
        if objattr:
            if objattr.mimetype:
                tag_attrs["type"] = self.escape(objattr.mimetype, in_html=True)
            if objattr.title:
                tag_attrs["name"] = self.escape(objattr.title, in_html=True)
            if objattr.width:
                tag_attrs["width"] = self.escape(objattr.width, in_html=True)
            if objattr.height:
                tag_attrs["height"] = self.escape(objattr.height, in_html=True)
        return self._raw_html(e, "object", content=self.format_children(e), tag_attrs=tag_attrs)

    def attachment_transclude(self, e: AttachmentTransclude) -> str:
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)
        return self._transclude(url, e, e.attrs)

    def transclude(self, e: Transclude) -> str:
        url = self.path_builder.page_url(e.pagename, relative_base=self.pagename)
        return self._transclude(url, e, e.attrs)

    def attachment_inlined(self, e: AttachmentInlined) -> str:
        ret = ""
        in_html = self._is_in_raw_html(e)
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)

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
        ret += self._link(url, e.link_text, in_html=in_html)
        return ret

    def _image(self, src: str, imgattr: Optional[ImageAttr] = None, in_html: bool = False) -> str:
        escaped_src = self.escape(
            src,
            markdown_escaper=partial(escape_markdown_symbols, symbols=['"', "[", "]", "(", ")"]),
            in_html=in_html,
        )
        alt = (
            self.escape(imgattr.alt, markdown_escaper=escape_markdown_all, in_html=in_html)
            if imgattr is not None and imgattr.alt is not None
            else MarkdownEscapedText("")
        )

        if imgattr is not None and imgattr.title is not None:
            title = self.escape(
                imgattr.title, markdown_escaper=escape_markdown_all, in_html=in_html
            )
            return f'![{alt}]({src} "{title}")'
        return f"![{alt}]({escaped_src})"

    def image(self, e: Image) -> str:
        in_html = self._is_in_raw_html(e)
        return self._image(e.src, e.attrs, in_html=in_html)

    def attachment_image(self, e: AttachmentImage) -> str:
        url = self.path_builder.attachment_url(e.pagename, e.filename, relative_base=self.pagename)
        in_html = self._is_in_raw_html(e)
        return self._image(url, e.attrs, in_html=in_html)
