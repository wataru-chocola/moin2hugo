import collections
import logging
from functools import partial
from typing import Callable, Dict, List, Optional

import attr

from moin2hugo.hugo_utils import (
    comment_out_shortcode,
    escape_shortcode,
    make_shortcode,
    search_shortcode_delimiter,
)
from moin2hugo.path_builder import HugoPathBuilder
from moin2x.formatter.markdown import MarkdownFormatter, MarkdownFormatterConfig
from moin2x.formatter.utils.markdown import (
    MarkdownEscapedText,
    escape_markdown_symbols,
    get_codeblock_delimiter,
)
from moin2x.formatter.utils.markdown_table import process_table
from moin2x.page_tree import AttachmentImage, Code, Codeblock, Image, ImageAttr, Table

logger = logging.getLogger(__name__)


@attr.define
class HugoFormatterConfig(MarkdownFormatterConfig):
    use_figure_shortcode: bool = True
    allow_emoji: bool = True


@attr.define
class TableProperty:
    num_of_columns: int = attr.ib(default=0)
    has_extended_attributes: bool = attr.ib(default=False)
    col_alignments: List[str] = attr.field(factory=list)


class HugoFormatter(MarkdownFormatter):
    config: HugoFormatterConfig

    def __init__(
        self,
        *,
        config: Optional[HugoFormatterConfig] = None,
        pagename: Optional[str] = None,
        path_builder: Optional[HugoPathBuilder] = None,
    ):
        super().__init__(
            config=config if config is not None else HugoFormatterConfig(),
            pagename=pagename,
            path_builder=path_builder,
        )

    def escape(
        self,
        text: str,
        markdown_escaper: Optional[Callable[[str], str]] = None,
        in_html: bool = False,
    ) -> MarkdownEscapedText:
        text = super().escape(text, markdown_escaper=markdown_escaper, in_html=in_html)
        return MarkdownEscapedText(escape_shortcode(text, in_html=in_html))

    # Codeblock
    def codeblock(self, e: Codeblock) -> str:
        (codeblock_delimiter, content) = get_codeblock_delimiter(e.content)

        content = comment_out_shortcode(content)
        if search_shortcode_delimiter(content):
            logger.error("cannot handle non-paired shortcode delimiter in codeblock")
            logger.error("MUST modify it manually or hugo will fail to build")

        ret = self._newline_if_needed(e)
        if e.syntax_id:
            ret += "%s%s\n" % (codeblock_delimiter, e.syntax_id)
        else:
            ret += "%s\n" % (codeblock_delimiter)
        ret += content
        ret += "\n%s" % codeblock_delimiter
        return ret

    # Table
    def table(self, e: Table) -> str:
        ret = self._newline_if_needed(e)
        e, table_prop = process_table(
            e,
            detect_header_heuristic=self.config.detect_table_header_heuristically,
            use_extended_markdown_table=self.config.use_extended_markdown_table,
        )

        md_table = self._table(e, table_prop)
        if self.config.use_extended_markdown_table and table_prop.has_span:
            shortcode = "extended-markdown-table"
            tmp = "{{< %s >}}\n" % shortcode
            tmp += "%s\n" % md_table.rstrip()
            tmp += "{{< /%s >}}\n" % shortcode
            md_table = tmp
        ret += md_table
        return ret

    # Decoration (can be multilined)
    def code(self, e: Code) -> str:
        # noqa: refer: https://meta.stackexchange.com/questions/82718/how-do-i-escape-a-backtick-within-in-line-code-in-markdown
        text = comment_out_shortcode(e.content)
        if search_shortcode_delimiter(text):
            logger.error("cannot handle non-paired shortcode delimiter in code")
            logger.error("MUST modify it manually or hugo will fail to build")

        return self._code(text)

    # Image / Object Embedding
    def _figure_shortcode(
        self, src: str, imgattr: Optional[ImageAttr] = None, *, in_html: bool
    ) -> str:
        src = self.escape(
            src,
            markdown_escaper=partial(escape_markdown_symbols, symbols=['"', "[", "]", "(", ")"]),
            in_html=in_html,
        )
        tag_attrs: Dict[str, Optional[str]] = collections.OrderedDict([("src", str(src))])
        if imgattr is not None:
            if imgattr.title is not None:
                tag_attrs["title"] = self.escape(imgattr.title, in_html=True)
            if imgattr.alt is not None:
                tag_attrs["alt"] = self.escape(imgattr.alt, in_html=True)
            if imgattr.width:
                tag_attrs["width"] = self.escape(imgattr.width, in_html=True)
            if imgattr.height:
                tag_attrs["height"] = self.escape(imgattr.height, in_html=True)
        return make_shortcode("figure", attrs=tag_attrs)

    def image(self, e: Image) -> str:
        if self.config.use_figure_shortcode and (e.attrs.width or e.attrs.height):
            in_html = self._is_in_raw_html(e)
            return self._figure_shortcode(e.src, e.attrs, in_html=in_html)
        return super().image(e)

    def attachment_image(self, e: AttachmentImage) -> str:
        if self.config.use_figure_shortcode and (e.attrs.width or e.attrs.height):
            url = self.path_builder.attachment_url(
                e.pagename, e.filename, relative_base=self.pagename
            )
            in_html = self._is_in_raw_html(e)
            return self._figure_shortcode(url, e.attrs, in_html=in_html)
        return super().attachment_image(e)
