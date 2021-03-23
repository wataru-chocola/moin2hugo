import re
import textwrap
import collections
import html
import urllib.parse
import logging

from .base import FormatterBase
from moin2hugo.page_tree import (
    PageRoot, PageElement,
    Macro, Comment, Smiley, Remark,
    ParsedText,
    Table, TableRow, TableCell,
    Emphasis, Strong, Big, Small, Underline, Strike, Sup, Sub, Code,
    BulletList, NumberList, Listitem,
    DefinitionList, DefinitionTerm, DefinitionDesc,
    Heading, HorizontalRule,
    Link, Pagelink, Interwikilink, Url, AttachmentLink,
    Paragraph, Text, SGMLEntity,
    AttachmentTransclude, Transclude,
    AttachmentInlined, AttachmentImage, Image
)
from moin2hugo.config import HugoConfig

from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

smiley2emoji = {
    'X-(': ':angry:',
    ':D': ':smiley:',
    '<:(': ':frowning:',
    ':o': ':astonished:',

    ':(': ':frowning:',
    ':)': ':simple_smile:',
    'B)': ':sunglasses:',
    ':))': ':simple_smile:',

    ';)': ':wink:',
    '/!\\': ':exclamation:',
    '<!>': ':exclamation:',
    '(!)': ':bulb:',

    ':-?': ':stuck_out_tongue_closed_eyes:',
    ':\\': ':astonished:',
    '>:>': ':angry:',
    '|)': ':innocent:',

    ':-(': ':frowning:',
    ':-)': ':simple_smile:',
    'B-)': ':sunglasses:',
    ':-))': ':simple_smile:',

    ';-)': ':wink:',
    '|-)': ':innocent:',
    '(./)': ':white_check_mark:',
    '{OK}': ':thumbsup:',

    '{X}': ':negative_squared_cross_mark:',
    '{i}': ':information_source:',
    '{1}': ':one:',
    '{2}': ':two:',

    '{3}': ':three:',
    '{*}': ':star:',
    '{o}': ':star2:',
}


class MarkdownEscapedText(str):
    pass


def escape_markdown_symbols(text: str, symbols: List[str] = [],
                            all_symbols: bool = False) -> MarkdownEscapedText:
    '''escape all occurences of these symbols no matter which context they are on.
    '''
    escapable_chars = set([
        '\\',
        '[', ']', '{', '}', '(', ')', '<', '>',
        '*', '+', '-',
        '_', ':', '`', '#', '|',
        '"', '~',    # can be escaped at least with commonmark
    ])
    if all_symbols:
        symbols = list(escapable_chars)
    assert escapable_chars.issuperset(set(symbols)), "not escapable symbol found: " + str(symbols)

    symbol_re = re.compile('([%s])' % re.escape("".join(symbols)))
    text = re.sub(symbol_re, r'\\\1', text)
    return MarkdownEscapedText(text)


def escape_markdown_all(text: str) -> MarkdownEscapedText:
    '''escape all occurences of these symbols no matter which context they are on.
    '''
    return escape_markdown_symbols(text, all_symbols=True)


def urlquote(text: str) -> str:
    return urllib.parse.quote(text)


class HugoFormatter(FormatterBase):
    def __init__(self, config: Optional[HugoConfig] = None):
        if config:
            self.config = config
        else:
            self.config = HugoConfig()

    def format(self, e: PageElement) -> str:
        return self.format_dispatcher(e)

    def _warn_nontext_in_raw_html(self, e: PageElement):
        msgfmt = "unsupported: non-Text element within %s wouldn't be rendered as intended"
        if any((not isinstance(c, Text) for c in e.descendants)):
            logger.warning(msgfmt % e.__class__.__name__)

    def _separator_line(self, e: PageElement) -> str:
        if e.prev_sibling is not None and type(e.prev_sibling) in (
                Paragraph, ParsedText, BulletList, NumberList, DefinitionList,
                Heading, HorizontalRule):
            prev_output_lines = self.format(e.prev_sibling).splitlines(keepends=True)
            if not prev_output_lines:
                return ""
            elif prev_output_lines[-1] == "\n":  # empty line
                return ""
            elif prev_output_lines[-1].endswith("\n"):
                return "\n"
            else:
                return "\n\n"
        return ''

    def _consolidate(self, e: PageElement) -> PageElement:
        '''Consolidate page tree structure destructively.'''
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
        ret = ''
        for c in e.children:
            ret += self.format(c)
        return ret

    def _raw_html(self, e: PageElement, tag: str, content: str,
                  tag_attrs: Dict[str, str] = {}) -> str:
        if self.config.goldmark_unsafe:
            self._warn_nontext_in_raw_html(e)
            if tag_attrs:
                tag_attrs_str = " ".join(['%s="%s"' % (k, v) for k, v in tag_attrs.items()])
                start_tag = "<%s %s>" % (tag, tag_attrs_str)
            else:
                start_tag = "<%s>" % tag
            end_tag = "</%s>" % tag
            return start_tag + html.escape(content) + end_tag
        else:
            logger.warning("unsupported: %s (set `goldmark_unsafe` option)" % e.__class__.__name__)
            return "%s" % escape_markdown_all(e.source_text)

    # Basic Elements
    def page_root(self, e: PageRoot) -> str:
        logger.debug("+ Consolidate page structure...")
        new_e = self._consolidate(e)
        logger.debug("+ Format page...")
        return self._generic_container(new_e)

    def paragraph(self, e: Paragraph) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def _is_in_raw_html(self, e: Text) -> bool:
        raw_html_types = (Underline, Sup, Sub, Big, Small, AttachmentTransclude, Transclude)
        return any((isinstance(p, raw_html_types) for p in e.parents))

    def _is_at_beginning_of_line(self, e: Text) -> bool:
        prev = e.prev_sibling
        while prev:
            if isinstance(prev, Remark):
                prev = prev.prev_sibling
                continue
            if isinstance(prev, Text):
                if not prev.content:
                    prev = prev.prev_sibling
                    continue
                return self.format(prev).endswith("\n")
            else:
                return False
            break

        return True

    def _escape_markdown_text(self, e: Text) -> MarkdownEscapedText:
        '''escape markdown symbols depending on context.
        '''
        # escape backslashes at first
        text = e.content
        text = re.sub(r'\\', r'\\\\', text)

        # target symbols of which all occurences are escaped
        targets = set(['[', ']', '{', '}', '(', ')', '*', '_', ':', '`', '~', '<', '>', '|', '#'])
        symbol_re = re.compile('([%s])' % re.escape("".join(targets)))

        is_at_beginning_of_line = self._is_at_beginning_of_line(e)

        lines = text.splitlines(keepends=True)
        new_lines = []
        first_line = True
        for line in lines:
            # remove trailing whitespaces pattern which means line break in markdown
            line = re.sub(r'\s+(?=\n)', '', line)

            if e.in_x([TableCell]):
                line = re.sub(r'([-])', r'\\\1', line)
            elif (first_line and is_at_beginning_of_line) or not first_line:
                # remove leading whitespaces
                line = line.lstrip()
                # avoid unintended listitem
                line = re.sub(r'^(\d)\.(?=\s)', r'\1\.', line)   # numbered list
                line = re.sub(r'^([-+])(?=\s)', r'\\\1', line)   # bullet list
                # horizontal rule or headling
                m = re.match(r'^([-=])\1*$', line)
                if m:
                    symbol = m.group(1)
                    line = line.replace(symbol, "\\" + symbol)

            # escape markdown syntax
            line = re.sub(r'\!(?=\[)', r'\!', line)   # image: ![title](image)

            # escape markdown special symbols
            line = re.sub(symbol_re, r'\\\1', line)

            new_lines.append(line)
            first_line = False
        return MarkdownEscapedText("".join(new_lines))

    def text(self, e: Text) -> str:
        if self._is_in_raw_html(e):
            return e.content
        else:
            return self._separator_line(e) + self._escape_markdown_text(e)

    def sgml_entity(self, e: SGMLEntity) -> str:
        return e.content

    # Moinwiki Special Objects
    def macro(self, e: Macro) -> str:
        if e.macro_name == 'BR':
            if not e.in_x([TableCell]):
                return "  \n"
            else:
                if self.config.goldmark_unsafe:
                    return '<br />'
                else:
                    return escape_markdown_all(e.source_text)
        elif e.macro_name == 'TableOfContents':
            # TODO
            return ''
        else:
            if e.markup:
                return self.text(Text(e.markup))
        return ''

    def comment(self, comment: Comment) -> str:
        return ''

    def smiley(self, smiley: Smiley) -> str:
        return smiley2emoji[smiley.content]

    def remark(self, remark: Remark) -> str:
        return ''

    # Codeblock
    def parsed_text(self, e: ParsedText) -> str:
        lines = e.content.splitlines()
        if lines and not lines[0]:
            lines = lines[1:]
        if lines and not lines[-1].strip():
            lines = lines[:-1]

        codeblock_delimiter = "```"
        for line in lines:
            m = re.search(r'^`{3,}', line)
            if m and len(m.group(0)) >= len(codeblock_delimiter):
                codeblock_delimiter = "`" * (len(m.group(0)) + 1)

        ret = self._separator_line(e)
        if e.parser_name == 'highlight':
            parser_args = e.parser_args or ''
            ret += "%s%s\n" % (codeblock_delimiter, parser_args)
            ret += "\n".join(lines)
            ret += "\n%s" % codeblock_delimiter
        elif e.parser_name in ["text", ""]:
            ret += "%s\n" % codeblock_delimiter
            ret += "\n".join(lines)
            ret += "\n%s" % codeblock_delimiter
        return ret

    # Table
    def table(self, e: Table) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def table_row(self, e: TableRow) -> str:
        ret = []
        for c in e.children:
            assert isinstance(c, TableCell)
            ret.append(self.format(c))
        return "|" + "|".join(ret) + "|\n"

    def table_cell(self, e: TableCell) -> str:
        return " %s " % self._generic_container(e).strip()

    # Heading / Horizontal Rule
    def heading(self, e: Heading) -> str:
        assert e.depth >= 1 and e.depth <= 6
        return '#' * e.depth + ' ' + escape_markdown_all(e.content) + "\n\n"

    def rule(self, e: HorizontalRule) -> str:
        return '-' * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, e: Underline) -> str:
        return self._raw_html(e, 'u', content=self._generic_container(e))

    def strike(self, e: Strike) -> str:
        return "~~%s~~" % self._generic_container(e)

    def small(self, e: Small) -> str:
        return self._raw_html(e, 'small', content=self._generic_container(e))

    def big(self, e: Big) -> str:
        return self._raw_html(e, 'big', content=self._generic_container(e))

    def strong(self, e: Strong) -> str:
        return "**%s**" % self._generic_container(e)

    def emphasis(self, e: Emphasis) -> str:
        return "*%s*" % self._generic_container(e)

    # Decoration (cannot be multilined)
    def sup(self, e: Sup) -> str:
        return self._raw_html(e, 'sup', content=e.content)

    def sub(self, e: Sub) -> str:
        return self._raw_html(e, 'sub', content=e.content)

    def code(self, e: Code) -> str:
        # noqa: refer: https://meta.stackexchange.com/questions/82718/how-do-i-escape-a-backtick-within-in-line-code-in-markdown
        text = e.content
        if text.startswith("`"):
            text = " " + text
        if text.endswith("`"):
            text = text + " "

        len_of_longest_backticks = 0
        if "`" in text:
            len_of_longest_backticks = max([len(s) for s in re.findall(r"`+", text)])
        delimiter = "`" * (len_of_longest_backticks + 1)
        return "%s%s%s" % (delimiter, text, delimiter)

    # Links
    def url(self, e: Url) -> str:
        # e.content must be valid as URL
        return "<%s>" % (escape_markdown_symbols(e.content, symbols=['<', '>']))

    def _link(self, target: MarkdownEscapedText, description: MarkdownEscapedText,
              title: Optional[MarkdownEscapedText] = None) -> str:
        if title is not None:
            return '[%s](%s "%s")' % (description, target, title)
        else:
            return "[%s](%s)" % (description, target)

    def link(self, e: Link) -> str:
        url = escape_markdown_symbols(e.url, symbols=['(', ')', '[', ']', '"'])
        description = MarkdownEscapedText(self._generic_container(e))
        title = None if e.attrs.title is None else escape_markdown_all(e.attrs.title)
        return self._link(url, description, title=title)

    def pagelink(self, e: Pagelink) -> str:
        link_path = page_url(e.pagename)
        if e.queryargs:
            # just ignore them
            pass
        if e.anchor:
            link_path += "#%s" % e.anchor
        escaped_link_path = escape_markdown_symbols(link_path, symbols=['(', ')', '[', ']', '"'])
        description = MarkdownEscapedText(self._generic_container(e))
        return self._link(escaped_link_path, description)

    def interwikilink(self, e: Interwikilink) -> str:
        logger.warning("unsupported: interwiki=%s" % e.source_text)
        return escape_markdown_all(e.source_text)

    def attachment_link(self, e: AttachmentLink) -> str:
        link_path = attachment_url(e.pagename, e.filename)
        if e.queryargs:
            # just ignore them
            pass
        escaped_link_path = escape_markdown_symbols(link_path, symbols=['(', ')', '[', ']', '"'])
        description = MarkdownEscapedText(self._generic_container(e))
        title = None if e.attrs.title is None else escape_markdown_all(e.attrs.title)
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
            text = self.format(c)
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
        marker = ": "
        paragraph_indent = " " * len(marker)
        first_line = True
        for c in e.children:
            text = self.format(c)
            if isinstance(c, BulletList) or isinstance(c, NumberList):
                ret += textwrap.indent(text, " " * 4)
            elif isinstance(c, ParsedText):
                ret += "\n"
                ret += textwrap.indent(text, " " * 4)
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

    # Image / Object Embedding
    def _transclude(self, url: str, e: PageElement, mimetype: Optional[str] = None,
                    title: Optional[str] = None) -> str:
        tag_attrs = collections.OrderedDict([('data', url)])
        if mimetype:
            tag_attrs['type'] = html.escape(mimetype)
        if title:
            tag_attrs['name'] = html.escape(title)
        return self._raw_html(e, "object", content=self._generic_container(e), tag_attrs=tag_attrs)

    def attachment_transclude(self, e: AttachmentTransclude) -> str:
        url = attachment_url(e.pagename, e.filename)
        return self._transclude(url, e, e.attrs.mimetype, e.attrs.title)

    def transclude(self, e: Transclude) -> str:
        url = page_url(e.pagename)
        return self._transclude(url, e, e.attrs.mimetype, e.attrs.title)

    def attachment_inlined(self, e: AttachmentInlined) -> str:
        ret = ""
        url = attachment_url(e.pagename, e.filename)
        escaped_url = escape_markdown_symbols(url, symbols=['(', ')', '[', ']', '"'])
        filepath = attachment_filepath(e.pagename, e.filename)
        with open(filepath, 'r') as f:
            attachment_content = f.read()
        # TODO: parse content with corresponding parser
        # _, ext = os.path.splitext(e.filename)
        # Parser = wikiutil.getParserForExtension(self.request.cfg, ext)
        ret += self.format(ParsedText(parser_name="text", content=attachment_content))
        ret += "\n\n"
        ret += self._link(escaped_url, escape_markdown_all(e.link_text))
        return ret

    def _image(self, src: MarkdownEscapedText, alt: Optional[MarkdownEscapedText] = None,
               title: Optional[MarkdownEscapedText] = None) -> str:
        if alt is None:
            alt = MarkdownEscapedText('')
        if title is not None:
            return '![{alt}]({src} "{title}")'.format(alt=alt, src=src, title=title)
        else:
            return '![{alt}]({src})'.format(alt=alt, src=src)

    def image(self, e: Image) -> str:
        src = escape_markdown_symbols(e.src, symbols=['"', '[', ']', '(', ')'])
        title = None if e.attrs.title is None else escape_markdown_all(e.attrs.title)
        alt = None if e.attrs.alt is None else escape_markdown_all(e.attrs.alt)
        return self._image(src, alt, title)

    def attachment_image(self, e: AttachmentImage) -> str:
        url = escape_markdown_symbols(attachment_url(e.pagename, e.filename),
                                      symbols=['"', '[', ']', '(', ')'])
        title = None if e.attrs.title is None else escape_markdown_all(e.attrs.title)
        alt = None if e.attrs.alt is None else escape_markdown_all(e.attrs.alt)
        return self._image(url, alt, title)


def page_url(pagename: str) -> str:
    # TODO
    url = urlquote("url/" + pagename)
    return url


def attachment_filepath(pagename: str, filename: str) -> str:
    # TODO
    filepath = "filepath/" + pagename + "/" + filename
    return filepath


def attachment_url(pagename: str, filename: str) -> str:
    # TODO
    url = urlquote("url/" + pagename + "/" + filename)
    return url