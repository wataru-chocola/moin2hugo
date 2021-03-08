from __future__ import annotations

import attr
from typing import Optional, List, Dict


@attr.s
class PageElement(object):
    content: str = attr.ib(default='')
    parent: Optional[PageElement] = attr.ib(default=None, init=False, repr=False, eq=False)
    children: List[PageElement] = attr.ib(default=attr.Factory(list), init=False)

    @property
    def parents(self) -> List[PageElement]:
        ret: List[PageElement] = []
        tmp = self.parent
        while tmp is not None:
            ret.append(tmp)
            tmp = tmp.parent
        return ret

    @property
    def prev_sibling(self) -> Optional[PageElement]:
        if self.parent is None:
            return None
        idx = [i for i, x in enumerate(self.parent.children) if x is self][0]
        if idx == 0:
            return None
        return self.parent.children[idx-1]

    @property
    def next_sibling(self) -> Optional[PageElement]:
        if self.parent is None:
            return None
        idx = [i for i, x in enumerate(self.parent.children) if x is self][0]
        if idx == len(self.parent.children) - 1:
            return None
        return self.parent.children[idx+1]

    def add_child(self, element: PageElement):
        self.children.append(element)
        element.parent = self


# General Objects
#
@attr.s
class PageRoot(PageElement):
    pass


@attr.s
class Paragraph(PageElement):
    pass


@attr.s
class Text(PageElement):
    pass


@attr.s
class Raw(PageElement):
    pass


# Moinwiki Special Objects
#
@attr.s
class Macro(PageElement):
    macro_name: str = attr.ib(kw_only=True)
    macro_args: Optional[str] = attr.ib(kw_only=True)
    markup: str = attr.ib(kw_only=True)


@attr.s
class Comment(PageElement):
    pass


@attr.s
class Smiley(PageElement):
    pass


@attr.s
class Span(PageElement):
    # TODO: needed?
    pass


# Codeblock (Parsed Text)
#
@attr.s
class ParsedText(PageElement):
    parser_name: str = attr.ib(default='')
    parser_args: Optional[str] = attr.ib(default=None)


# Table
#
@attr.s
class Table(PageElement):
    attrs: Dict[str, str] = attr.ib(default=attr.Factory(dict))


@attr.s
class TableRow(PageElement):
    attrs: Dict[str, str] = attr.ib(default=attr.Factory(dict))


@attr.s
class TableCell(PageElement):
    attrs: Dict[str, str] = attr.ib(default=attr.Factory(dict))


# Heading / Horizontal Rule
#
@attr.s
class Heading(PageElement):
    depth: int = attr.ib(kw_only=True)


@attr.s
class HorizontalRule(PageElement):
    pass


# Decorations
#
@attr.s
class Underline(PageElement):
    pass


@attr.s
class Strike(PageElement):
    pass


@attr.s
class Small(PageElement):
    pass


@attr.s
class Big(PageElement):
    pass


@attr.s
class Emphasis(PageElement):
    pass


@attr.s
class Strong(PageElement):
    pass


@attr.s
class Sup(PageElement):
    pass


@attr.s
class Sub(PageElement):
    pass


@attr.s
class Code(PageElement):
    pass


# Links
@attr.s
class Link(PageElement):
    target: str = attr.ib(kw_only=True)
    title: Optional[str] = attr.ib(default=None)


@attr.s
class Pagelink(PageElement):
    page_name: str = attr.ib(kw_only=True)
    queryargs: Optional[Dict[str, str]] = attr.ib(default=None)
    anchor: Optional[str] = attr.ib(default=None)


@attr.s
class AttachmentLink(PageElement):
    attach_name: str = attr.ib(kw_only=True)
    queryargs: Optional[Dict[str, str]] = attr.ib(default=None)
    title: Optional[str] = attr.ib(default=None)


@attr.s
class Url(PageElement):
    pass


# Itemlist
#
@attr.s
class BulletList(PageElement):
    pass


@attr.s
class NumberList(PageElement):
    pass


@attr.s
class DefinitionList(PageElement):
    pass


@attr.s
class DefinitionTerm(PageElement):
    pass


@attr.s
class DefinitionDesc(PageElement):
    pass


@attr.s
class Listitem(PageElement):
    pass


# Transclude (Image Embedding)
@attr.s
class AttachmentImage(PageElement):
    pass


@attr.s
class AttachmentIinline(PageElement):
    pass


@attr.s
class Image(PageElement):
    pass
