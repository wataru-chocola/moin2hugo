import re
import textwrap

from moin2hugo.page_tree import (
    PageRoot, PageElement,
    Macro, Comment, Smiley,
    Emphasis, Strong, Big, Small, Underline, Strike, Sup, Sub, Code,
    BulletList, NumberList, Listitem,
    DefinitionList, DefinitionTerm,
    Heading, HorizontalRule,
    ParsedText,
    Link, Pagelink, Url, AttachmentLink,
    Paragraph, Text, Raw
)

from typing import Optional, Dict, Callable, TypeVar, Type, Any

T_PageElement = TypeVar("T_PageElement", bound=PageElement)

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


class Formatter(object):
    def format(self, e: PageElement):
        dispatch_tbl: Dict[Type[PageElement], Callable[[Any], str]] = {
            PageRoot: self._generic_container,

            # General Objects
            Paragraph: self.paragraph,
            Text: self.text2,
            Raw: self.raw,

            # Moinwiki Special Objects
            Macro: self.macro,
            Comment: self.comment,
            Smiley: self.smiley,

            # Codeblock / ParsedText
            ParsedText: self.parsed_text,

            # Table
            # Table: self.table,

            # Heading / Horizontal Rule
            Heading: self.heading,
            HorizontalRule: self.rule,

            # Decorations
            Underline: self.underline,
            Strike: self.strike,
            Small: self.small,
            Big: self.big,
            Emphasis: self.emphasis,
            Strong: self.strong,
            Sup: self.sup,
            Sub: self.sub,
            Code: self.code,

            # Links
            Link: self.link,
            Pagelink: self.pagelink,
            AttachmentLink: self.attachment_link,
            Url: self.url,

            # Itemlist
            BulletList: self.bullet_list,
            NumberList: self.number_list,
            Listitem: self.listitem,

            # Transclude (Image Embedding)
            # Image: self.image,
        }
        return dispatch_tbl[type(e)](e)

    def _generic_container(self, e: PageElement) -> str:
        ret = ''
        for c in e.children:
            ret += self.format(c)
        return ret

    def _separator_line(self, e: PageElement) -> str:
        if e.prev_sibling is not None and type(e.prev_sibling) in (
                Paragraph, ParsedText, BulletList, NumberList, DefinitionList,
                Heading, HorizontalRule):
            return "\n"
        return ''

    # General Objects
    def paragraph(self, e: Paragraph) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def text(self, text: str) -> str:
        # TODO: escape markdown special characters, etc
        return text

    def text2(self, e: Text) -> str:
        return e.content

    def raw(self, e: Raw) -> str:
        return e.content

    # Moinwiki Special Objects
    def macro(self, e: Macro) -> str:
        if e.macro_name == 'BR':
            # TODO:
            return '<br />'
        elif e.macro_name == 'TableOfContents':
            # TODO
            return ''
        else:
            if e.markup:
                return self.text(e.markup)
        return ''

    def comment(self, comment: Comment) -> str:
        return ''

    def smiley(self, smiley: Smiley) -> str:
        # TODO: enableEmoji option?
        return smiley2emoji[smiley.content]

    # Codeblock
    def parsed_text(self, e: ParsedText) -> str:
        lines = e.content.splitlines()
        if lines and not lines[0]:
            lines = lines[1:]
        if lines and not lines[-1].strip():
            lines = lines[:-1]

        ret = self._separator_line(e)
        if e.parser_name == 'highlight':
            parser_args = e.parser_args or ''
            # TODO: take consideration of indentation
            ret += "```%s\n" % parser_args
            ret += "\n".join(lines)
            ret += "\n```"
        return ret

    # Table
    # def table(self, e: Table) -> str:
    #     ret = self._separator_line(e)
    #     pass

    # Heading / Horizontal Rule
    def heading(self, e: Heading) -> str:
        # TODO: support _id ?
        assert e.depth >= 1 and e.depth <= 6
        return '#' * e.depth + ' ' + e.content + "\n\n"

    def rule(self, e: HorizontalRule) -> str:
        return '-' * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, e: Strike) -> str:
        # TODO: unsafe
        return "<u>%s</u>" % self._generic_container(e)

    def strike(self, e: Strike) -> str:
        return "~~%s~~" % self._generic_container(e)

    def small(self, e: Small) -> str:
        # TODO: unsafe
        return "<small>%s</small>" % self._generic_container(e)

    def big(self, e: Big) -> str:
        # TODO: unsafe
        return "<big>%s</big>" % self._generic_container(e)

    def strong(self, e: Strong) -> str:
        # TODO: want to handle _ or * within content, but how?
        return "**%s**" % self._generic_container(e)

    def emphasis(self, e: Emphasis) -> str:
        # TODO: want to handle _ or *, but how?
        return "*%s*" % self._generic_container(e)

    # Decoration (cannot be multilined)
    def sup(self, e: Sup) -> str:
        # TODO: unsafe option?
        return "<sup>%s</sup>" % e.content

    def sub(self, e: Sub) -> str:
        # TODO: unsafe option?
        return "<sub>%s</sub>" % e.content

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
        return "<%s>" % (e.content)

    def link(self, e: Link) -> str:
        description = self._generic_container(e)
        return self._link(e.target, description, title=e.title)

    def _link(self, target: str, description: str, title: Optional[str] = None) -> str:
        if title is not None:
            return '[%s](%s "%s")' % (description, target, title)
        else:
            return "[%s](%s)" % (description, target)

    def pagelink(self, e: Pagelink) -> str:
        # TODO: convert page_name to link path
        link_path = e.page_name
        if e.queryargs:
            # TODO: maybe useless
            pass
        if e.anchor:
            link_path += "#%s" % e.anchor
        description = self._generic_container(e)
        return self._link(link_path, description)

    def attachment_link(self, e: AttachmentLink) -> str:
        # TODO: convert attach_name to link path
        link_path = e.attach_name
        if e.queryargs:
            # TODO: maybe useless
            pass
        description = self._generic_container(e)
        return self._link(link_path, description, e.title)

    # Itemlist
    def bullet_list(self, e: BulletList) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def number_list(self, e: NumberList) -> str:
        return self._separator_line(e) + self._generic_container(e)

    def definition_list(self, e: DefinitionList):
        # TODO
        ret = self._separator_line(e)
        return ret

    def listitem(self, e: Listitem):
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
                    else:
                        ret += paragraph_indent + line
        return ret

    # Image Embedding
    def image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"

    def attachment_image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"
