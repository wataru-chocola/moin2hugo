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

from typing import List, Dict, Optional


class PageBuilder(object):
    def __init__(self):
        self.page_root = PageRoot()
        self.cur = self.page_root

    # Page Bulding Status
    @property
    def in_p(self) -> bool:
        tmp = self.cur
        while tmp is not None:
            if isinstance(tmp, Paragraph):
                return True
            tmp = tmp.parent
        return False

    @property
    def in_pre(self) -> bool:
        return isinstance(self.cur, ParsedText)

    @property
    def is_found_parser(self) -> bool:
        assert self.in_pre
        return bool(self.cur.parser_name)

    # Helpers
    def _add_new_elem(self, e: PageElement):
        self.cur.add_child(e)

    def _start_new_elem(self, e: PageElement):
        self.cur.add_child(e)
        self.cur = e

    def _end_current_elem(self):
        self.cur = self.cur.parent

    # General Objects
    def paragraph(self, on: bool):
        if on:
            self._start_new_elem(Paragraph())
        else:
            self._end_current_elem()

    def paragraph_start(self):
        self._start_new_elem(Paragraph())

    def paragraph_end(self):
        self._end_current_elem()

    def text(self, text: str):
        self._add_new_elem(Text(content=text))

    def raw(self, text: str):
        self._add_new_elem(Raw(content=text))

    # Moinwiki Special Objects
    def macro(self, macro_name: str, macro_args: Optional[str], markup: str):
        self._add_new_elem(Macro(macro_name=macro_name, macro_args=macro_args, markup=markup))

    def comment(self, text: str):
        self._add_new_elem(Comment(content=text))

    def smiley(self, smiley: str):
        self._add_new_elem(Smiley(content=smiley))

    def span(self):
        # TODO: needed?
        pass

    # Codeblock / ParsedText
    def parsed_text(self, parser_name: str, parser_args: Optional[str], lines: List[str]):
        self.cur.add_child(ParsedText(parser_name=parser_name, parser_args=parser_args,
                                      content="\n".join(lines)))

    def parsed_text_start(self):
        e = ParsedText()
        self._start_new_elem(e)

    def parsed_text_parser(self, parser_name: str, parser_args: Optional[str]):
        assert isinstance(self.cur, ParsedText)
        self.cur.parser_name = parser_name
        self.cur.parser_args = parser_args

    def parsed_text_end(self, lines: List[str]):
        self.cur.content = '\n'.join(lines)
        self._end_current_elem()

    def preformatted(self, on):
        # TODO: needed?
        pass

    # Table
    def table(self, on, attrs):
        pass

    def table_row(self):
        pass

    def table_cell(self):
        pass

    # Heading / Horizontal Rule
    def heading(self, depth: int, text: str):
        self._add_new_elem(Heading(depth=depth, content=text))

    def rule(self):
        self._add_new_elem(HorizontalRule())

    # Decoration
    def underline(self, on: bool):
        if on:
            self._start_new_elem(Underline())
        else:
            self._end_current_elem()

    def strike(self, on: bool):
        if on:
            self._start_new_elem(Strike())
        else:
            self._end_current_elem()

    def big(self, on: bool):
        if on:
            self._start_new_elem(Big())
        else:
            self._end_current_elem()

    def small(self, on: bool):
        if on:
            self._start_new_elem(Small())
        else:
            self._end_current_elem()

    def strong(self, on: bool):
        if on:
            self._start_new_elem(Strong())
        else:
            self._end_current_elem()

    def emphasis(self, on: bool):
        if on:
            self._start_new_elem(Emphasis())
        else:
            self._end_current_elem()

    def sup(self, text: str):
        self._add_new_elem(Sup(content=text))

    def sub(self, text: str):
        self._add_new_elem(Sub(content=text))

    def code(self, text: str):
        self._add_new_elem(Code(content=text))

    # Link
    def link_start(self, target: str, title: Optional[str] = None):
        self._start_new_elem(Link(target=target, title=title))

    def link_end(self):
        self._end_current_elem()

    def pagelink(self, on: bool, page_name: str = '', queryargs: Optional[Dict[str, str]] = None,
                 anchor: Optional[str] = None):
        if on:
            e = Pagelink(page_name=page_name, queryargs=queryargs, anchor=anchor)
            self._start_new_elem(e)
        else:
            self._end_current_elem()

    def attachment_link_start(self, attach_name: str, title: Optional[str] = None,
                              queryargs: Optional[Dict[str, str]] = None):
        e = AttachmentLink(attach_name=attach_name, title=title, queryargs=queryargs)
        self._start_new_elem(e)

    def attachment_link_end(self):
        self._end_current_elem()

    def url(self, text: str):
        self._add_new_elem(Url(content=text))

    # Itemlist
    def bullet_list(self, on: bool):
        if on:
            self._start_new_elem(BulletList())
        else:
            self._end_current_elem()

    def number_list(self, on: bool, numtype: str = '1', numstart: str = '1'):
        # TODO
        if on:
            self._start_new_elem(NumberList())
        else:
            self._end_current_elem()

    def listitem(self, on: bool):
        if on:
            self._start_new_elem(Listitem())
        else:
            self._end_current_elem()

    def definition_list(self, on: bool):
        if on:
            self._start_new_elem(DefinitionList())
        else:
            self._end_current_elem()

    def definition_term(self):
        pass

    def definition_desc(self):
        pass

    # Transclude (Image Embedding)
    def transclusion(self):
        pass

    def attachment_image(self):
        pass

    def attachment_inlined(self):
        pass

    def image(self):
        pass
