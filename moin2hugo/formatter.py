import re

from moin2hugo.page_tree import PageElement, PageRoot, Smiley, Paragraph, Text, Raw
from moin2hugo.page_tree import BulletList, Listitem
from moin2hugo.page_tree import Emphasis, Strong, Big, Small, Underline, Strike, Sup, Sub, Code
from moin2hugo.page_tree import Heading, HorizontalRule
from moin2hugo.page_tree import ParsedText
from moin2hugo.page_tree import Link, Pagelink, Url, AttachmentLink
from typing import Optional, Dict, List, Callable, TypeVar, Type, Any

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
    def __init__(self):
        self.in_p = False

    def format(self, e: PageElement):
        dispatch_tbl: Dict[Type[PageElement], Callable[[Any], str]] = {
            PageRoot: self._generic_container,

            # General Objects
            Paragraph: self.paragraph,
            Text: self.text2,

            Smiley: self.smiley,

            Underline: self.underline,
            Strike: self.strike,
            Big: self.big,
            Small: self.small,
            Emphasis: self.emphasis,
            Strong: self.strong,
            Sup: self.sup,
            Sub: self.sub,
            Code: self.code,

            Link: self.link,
            Pagelink: self.pagelink,
            Url: self.url,
            AttachmentLink: self.attachment_link,

            Heading: self.heading,
            HorizontalRule: self.rule,

            ParsedText: self.parsed_text,
            Raw: self.raw,

            BulletList: self.bullet_list,
            Listitem: self.listitem,
        }
        return dispatch_tbl[type(e)](e)

    def _generic_container(self, e: PageElement) -> str:
        ret = ''
        for c in e.children:
            ret += self.format(c)
        return ret

    # General Objects
    def paragraph(self, e: Paragraph) -> str:
        return self._generic_container(e)

    def text(self, text: str) -> str:
        # TODO: escape markdown special characters, etc
        return text

    def text2(self, e: Text) -> str:
        return e.content

    def raw(self, e: Raw) -> str:
        return e.content

    # Moinwiki Special Objects
    def macro(self, macro_obj, name, args, markup=None):
        # TODO:
        try:
            return macro_obj.execute(name, args)
        except ImportError as err:
            errmsg = str(err)
            if name not in errmsg:
                raise
            if markup:
                return (self.span(1, title=errmsg) +
                        self.text(markup) +
                        self.span(0))
            else:
                return self.text(errmsg)

    def smiley(self, smiley: Smiley):
        # TODO: enableEmoji option?
        return smiley2emoji[smiley.content]

    # Codeblock
    def parsed_text(self, e: ParsedText):
        lines = e.content.splitlines()
        if lines and not lines[0]:
            lines = lines[1:]
        if lines and not lines[-1].strip():
            lines = lines[:-1]

        ret = ''
        if e.parser_name == 'highlight':
            parser_args = e.parser_args or ''
            # TODO: take consideration of indentation
            ret += "```%s\n" % parser_args
            ret += "\n".join(lines)
            ret += "\n```"
        return ret

    # Heading / Horizontal Rule
    def heading(self, e: Heading) -> str:
        # TODO: support _id ?
        assert e.depth >= 1 and e.depth <= 6
        return '#' * e.depth + ' ' + e.content + "\n\n"

    def rule(self, e: HorizontalRule) -> str:
        return '-' * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, e: Strike) -> str:
        return "__%s__" % self._generic_container(e)

    def strike(self, e: Strike) -> str:
        return "~~%s~~" % self._generic_container(e)

    def small(self, e: Small) -> str:
        ret = ''
        ret += "<small>"
        for c in e.children:
            ret += self.format(c)
        ret += "</small>"
        return ret

    def big(self, e: Big) -> str:
        ret = ''
        ret += "<big>"
        for c in e.children:
            ret += self.format(c)
        ret += "</big>"
        return ret

    def strong(self, e: Strong) -> str:
        # TODO: want to handle _ or *, but how?
        ret = ''
        ret += "**"
        for c in e.children:
            ret += self.format(c)
        ret += "**"
        return ret

    def emphasis(self, e: Emphasis) -> str:
        # TODO: want to handle _ or *, but how?
        ret = ''
        ret += "*"
        for c in e.children:
            ret += self.format(c)
        ret += "*"
        return ret

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
    def bullet_list(self, bullet_list):
        ret = ""
        for item in bullet_list.children:
            ret += "* %s\n" % self.format(item)
        return ret

    def number_list(self):
        # TODO
        return "dummy"

    def definition_list(self):
        # TODO
        return "dummy"

    def listitem(self, e: Listitem):
        # TODO: unused?
        # TODO: indent?
        ret = ""
        for c in e.children:
            ret += self.format(c)
        return ret

    # Image Embedding
    def image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"

    def attachment_image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"

