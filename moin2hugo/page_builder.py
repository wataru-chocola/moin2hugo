from moin2hugo.page_tree import (
    PageRoot, PageElement,
    Smiley,
    Emphasis, Strong, Big, Small, Underline, Strike, Sup, Sub, Code,
    BulletList, NumberList, Listitem,
    DefinitionList, DefinitionTerm,
    Heading, HorizontalRule,
    ParsedText,
    Link, Pagelink, Url, AttachmentLink,
    Paragraph, Text, Raw)

from typing import List, Dict, Optional


class PageBuilder(object):
    def __init__(self):
        self.page_root = PageRoot()
        self.cur = self.page_root

    # Page Bulding Status
    @property
    def in_pre(self) -> bool:
        return isinstance(self.cur, ParsedText)

    def is_found_parser(self) -> bool:
        assert self.in_pre
        return bool(self.cur.parser_name)

    # Helpers
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

    def text(self, text: str):
        self.cur.add_child(Text(content=text))

    # Moinwiki Special Objects
    def macro(self):
        pass

    def comment(self):
        pass

    def smiley(self, smiley: str):
        self.cur.add_child(Smiley(content=smiley))

    def span(self):
        pass

    def attachment_image(self):
        pass

    def attachment_inlined(self):
        pass

    def attachment_link_start(self, attach_name: str, title: Optional[str] = None,
                              queryargs: Optional[Dict[str, str]] = None):
        e = AttachmentLink(attach_name=attach_name, title=title, queryargs=queryargs)
        self.cur.add_child(e)
        self.cur = e

    def attachment_link_end(self):
        self.cur = self.cur.parent

    def heading(self, depth: int, text: str):
        self.cur.add_child(Heading(depth=depth, content=text))

    def rule(self):
        self.cur.add_child(HorizontalRule())

    # Decoration
    def strike(self, on: bool):
        if on:
            e = Strike()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def underline(self, on: bool):
        if on:
            e = Underline()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def big(self, on: bool):
        if on:
            e = Big()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def small(self, on: bool):
        if on:
            e = Small()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def strong(self, on: bool):
        if on:
            e = Strong()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def emphasis(self, on: bool):
        if on:
            e = Emphasis()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def sup(self, text: str):
        self.cur.add_child(Sup(content=text))

    def sub(self, text: str):
        self.cur.add_child(Sub(content=text))

    def code(self, text: str):
        self.cur.add_child(Code(content=text))

    def image(self):
        pass

    def bullet_list(self, on: bool):
        if on:
            e = BulletList()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def number_list(self, on: bool, numtype: str = '1', numstart: str = '1'):
        # TODO
        if on:
            e = NumberList()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def listitem(self, on: bool):
        if on:
            e = Listitem()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def definition_list(self, on: bool):
        if on:
            e = DefinitionList()
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    def definition_term(self):
        pass

    def definition_desc(self):
        pass

    def link_start(self, target: str, title: Optional[str] = None):
        e = Link(target=target, title=title)
        self.cur.add_child(e)
        self.cur = e

    def link_end(self):
        self.cur = self.cur.parent

    def pagelink(self, on: bool, page_name: str = '', queryargs: Optional[Dict[str, str]] = None,
                 anchor: Optional[str] = None):
        if on:
            e = Pagelink(page_name=page_name, queryargs=queryargs, anchor=anchor)
            self.cur.add_child(e)
            self.cur = e
        else:
            self.cur = self.cur.parent

    # TODO
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
        pass

    def raw(self, text: str):
        self.cur.add_child(Raw(content=text))

    def table(self, on, attrs):
        pass

    def table_cell(self):
        pass

    def table_row(self):
        pass

    def transclusion(self):
        pass

    def url(self, text: str):
        self.cur.add_child(Url(content=text))
