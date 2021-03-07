from __future__ import annotations

from typing import Optional, List, Dict


class PageElement(object):
    def __init__(self, content: str = ''):
        self.content: str = content
        self.parent: Optional[PageElement] = None
        self.children: List[PageElement] = []

    def __eq__(self, y: object) -> bool:
        if not isinstance(y, PageElement):
            return False
        if self.content != y.content:
            return False
        if self.children != y.children:
            return False
        return True

    def __repr__(self) -> str:
        x = "{classname}(content='{content}',children={children})".format(
            classname=self.__class__.__name__,
            content=self.content,
            children=self.children)
        return x

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


class PageRoot(PageElement):
    pass


class Macro(PageElement):
    pass


class Comment(PageElement):
    pass


class Smiley(PageElement):
    pass


class Span(PageElement):
    pass


class AttachmentImage(PageElement):
    pass


class AttachmentIinline(PageElement):
    pass


class Big(PageElement):
    pass


class Emphasis(PageElement):
    pass


class Strong(PageElement):
    pass


class Small(PageElement):
    pass


class Underline(PageElement):
    pass


class Strike(PageElement):
    pass


class Sup(PageElement):
    pass


class Sub(PageElement):
    pass


class Code(PageElement):
    pass


class BulletList(PageElement):
    pass


class NumberList(PageElement):
    pass


class DefinitionList(PageElement):
    pass


class DefinitionTerm(PageElement):
    pass


class Listitem(PageElement):
    pass


class Heading(PageElement):
    def __init__(self, depth: int, content: str = ''):
        self.depth = depth
        super().__init__(content=content)


class HorizontalRule(PageElement):
    pass


class Link(PageElement):
    def __init__(self, target: str, title: Optional[str] = None):
        self.target = target
        self.title = title
        super().__init__()


class Pagelink(PageElement):
    def __init__(self, page_name: str, queryargs: Optional[Dict[str, str]] = None,
                 anchor: Optional[str] = None):
        self.page_name = page_name
        self.queryargs = queryargs
        self.anchor = anchor
        super().__init__()


class AttachmentLink(PageElement):
    def __init__(self, attach_name: str, title: Optional[str],
                 queryargs: Optional[Dict[str, str]] = None, content: str = ''):
        self.attach_name = attach_name
        self.title = title
        self.queryargs = queryargs
        super().__init__(content=content)


class Url(PageElement):
    pass


class ParsedText(PageElement):
    def __init__(self, parser_name: str, parser_args: Optional[str] = '', content: str = ''):
        self.parser_name = parser_name
        self.parser_args = parser_args
        super().__init__(content=content)


class Paragraph(PageElement):
    pass


class Text(PageElement):
    pass


class Raw(PageElement):
    pass
