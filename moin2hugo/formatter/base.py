from abc import ABCMeta, abstractmethod

from moin2hugo.page_tree import (
    PageRoot, Raw, PageElement,
    Macro, Comment, Smiley, Remark,
    ParsedText, Codeblock,
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
from typing import Dict, Callable, Type, Any, Optional


class FormatterBase(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, config: Optional[Any] = None, pagename: Optional[str] = None,
                 path_builder: Optional[Any] = None):
        pass

    @classmethod
    def format(cls, e: PageElement, config: Optional[Any] = None, pagename: Optional[str] = None,
               path_builder: Optional[Any] = None) -> str:
        formatter = cls(config=config, pagename=pagename, path_builder=path_builder)
        return formatter.do_format(e)

    def do_format(self, e: PageElement) -> str:
        return self.format_dispatcher(e)

    def format_dispatcher(self, e: PageElement) -> str:
        dispatch_tbl: Dict[Type[PageElement], Callable[[Any], str]] = {
            PageRoot: self.page_root,
            Raw: self.raw,

            # General Objects
            Paragraph: self.paragraph,
            Text: self.text,
            SGMLEntity: self.sgml_entity,

            # Moinwiki Special Objects
            Macro: self.macro,
            Comment: self.comment,
            Smiley: self.smiley,
            Remark: self.remark,

            # Codeblock / ParsedText
            ParsedText: self.parsed_text,
            Codeblock: self.codeblock,

            # Table
            Table: self.table,
            TableRow: self.table_row,
            TableCell: self.table_cell,

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
            Interwikilink: self.interwikilink,
            AttachmentLink: self.attachment_link,
            Url: self.url,

            # Itemlist
            BulletList: self.bullet_list,
            NumberList: self.number_list,
            Listitem: self.listitem,
            DefinitionList: self.definition_list,
            DefinitionTerm: self.definition_term,
            DefinitionDesc: self.definition_desc,

            # Transclude (Image Embedding)
            AttachmentTransclude: self.attachment_transclude,
            Transclude: self.transclude,
            AttachmentInlined: self.attachment_inlined,
            AttachmentImage: self.attachment_image,
            Image: self.image,
        }
        return dispatch_tbl[type(e)](e)

    @abstractmethod
    def page_root(self, e: PageRoot) -> str:
        pass

    @abstractmethod
    def raw(self, e: Raw) -> str:
        pass

    @abstractmethod
    def paragraph(self, e: Paragraph) -> str:
        pass

    @abstractmethod
    def text(self, e: Text) -> str:
        pass

    @abstractmethod
    def sgml_entity(self, e: SGMLEntity) -> str:
        pass

    @abstractmethod
    def macro(self, e: Macro) -> str:
        pass

    @abstractmethod
    def comment(self, e: Comment) -> str:
        pass

    @abstractmethod
    def smiley(self, e: Smiley) -> str:
        pass

    @abstractmethod
    def remark(self, e: Remark) -> str:
        pass

    @abstractmethod
    def codeblock(self, e: Codeblock) -> str:
        pass

    @abstractmethod
    def parsed_text(self, e: ParsedText) -> str:
        pass

    @abstractmethod
    def table(self, e: Table) -> str:
        pass

    @abstractmethod
    def table_row(self, e: TableRow) -> str:
        pass

    @abstractmethod
    def table_cell(self, e: TableCell) -> str:
        pass

    @abstractmethod
    def heading(self, e: Heading) -> str:
        pass

    @abstractmethod
    def rule(self, e: HorizontalRule) -> str:
        pass

    @abstractmethod
    def underline(self, e: Underline) -> str:
        pass

    @abstractmethod
    def strike(self, e: Strike) -> str:
        pass

    @abstractmethod
    def small(self, e: Small) -> str:
        pass

    @abstractmethod
    def big(self, e: Big) -> str:
        pass

    @abstractmethod
    def emphasis(self, e: Emphasis) -> str:
        pass

    @abstractmethod
    def strong(self, e: Strong) -> str:
        pass

    @abstractmethod
    def sup(self, e: Sup) -> str:
        pass

    @abstractmethod
    def sub(self, e: Sub) -> str:
        pass

    @abstractmethod
    def code(self, e: Code) -> str:
        pass

    @abstractmethod
    def link(self, e: Link) -> str:
        pass

    @abstractmethod
    def pagelink(self, e: Pagelink) -> str:
        pass

    @abstractmethod
    def interwikilink(self, e: Interwikilink) -> str:
        pass

    @abstractmethod
    def attachment_link(self, e: AttachmentLink) -> str:
        pass

    @abstractmethod
    def url(self, e: Url) -> str:
        pass

    @abstractmethod
    def bullet_list(self, e: BulletList) -> str:
        pass

    @abstractmethod
    def number_list(self, e: NumberList) -> str:
        pass

    @abstractmethod
    def listitem(self, e: Listitem) -> str:
        pass

    @abstractmethod
    def definition_list(self, e: DefinitionList) -> str:
        pass

    @abstractmethod
    def definition_term(self, e: DefinitionTerm) -> str:
        pass

    @abstractmethod
    def definition_desc(self, e: DefinitionDesc) -> str:
        pass

    @abstractmethod
    def attachment_transclude(self, e: AttachmentTransclude) -> str:
        pass

    @abstractmethod
    def transclude(self, e: Transclude) -> str:
        pass

    @abstractmethod
    def attachment_inlined(self, e: AttachmentInlined) -> str:
        pass

    @abstractmethod
    def attachment_image(self, e: AttachmentImage) -> str:
        pass

    @abstractmethod
    def image(self, e: Image) -> str:
        pass
