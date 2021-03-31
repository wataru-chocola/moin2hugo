from abc import ABCMeta, abstractclassmethod

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
from typing import Dict, Callable, Type, Any, Optional


class FormatterBase(metaclass=ABCMeta):
    @abstractclassmethod
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

    @abstractclassmethod
    def page_root(self, e: PageRoot) -> str:
        pass

    @abstractclassmethod
    def paragraph(self, e: Paragraph) -> str:
        pass

    @abstractclassmethod
    def text(self, e: Text) -> str:
        pass

    @abstractclassmethod
    def sgml_entity(self, e: SGMLEntity) -> str:
        pass

    @abstractclassmethod
    def macro(self, e: Macro) -> str:
        pass

    @abstractclassmethod
    def comment(self, e: Comment) -> str:
        pass

    @abstractclassmethod
    def smiley(self, e: Smiley) -> str:
        pass

    @abstractclassmethod
    def remark(self, e: Remark) -> str:
        pass

    @abstractclassmethod
    def parsed_text(self, e: ParsedText) -> str:
        pass

    @abstractclassmethod
    def table(self, e: Table) -> str:
        pass

    @abstractclassmethod
    def table_row(self, e: TableRow) -> str:
        pass

    @abstractclassmethod
    def table_cell(self, e: TableCell) -> str:
        pass

    @abstractclassmethod
    def heading(self, e: Heading) -> str:
        pass

    @abstractclassmethod
    def rule(self, e: HorizontalRule) -> str:
        pass

    @abstractclassmethod
    def underline(self, e: Underline) -> str:
        pass

    @abstractclassmethod
    def strike(self, e: Strike) -> str:
        pass

    @abstractclassmethod
    def small(self, e: Small) -> str:
        pass

    @abstractclassmethod
    def big(self, e: Big) -> str:
        pass

    @abstractclassmethod
    def emphasis(self, e: Emphasis) -> str:
        pass

    @abstractclassmethod
    def strong(self, e: Strong) -> str:
        pass

    @abstractclassmethod
    def sup(self, e: Sup) -> str:
        pass

    @abstractclassmethod
    def sub(self, e: Sub) -> str:
        pass

    @abstractclassmethod
    def code(self, e: Code) -> str:
        pass

    @abstractclassmethod
    def link(self, e: Link) -> str:
        pass

    @abstractclassmethod
    def pagelink(self, e: Pagelink) -> str:
        pass

    @abstractclassmethod
    def interwikilink(self, e: Interwikilink) -> str:
        pass

    @abstractclassmethod
    def attachment_link(self, e: AttachmentLink) -> str:
        pass

    @abstractclassmethod
    def url(self, e: Url) -> str:
        pass

    @abstractclassmethod
    def bullet_list(self, e: BulletList) -> str:
        pass

    @abstractclassmethod
    def number_list(self, e: NumberList) -> str:
        pass

    @abstractclassmethod
    def listitem(self, e: Listitem) -> str:
        pass

    @abstractclassmethod
    def definition_list(self, e: DefinitionList) -> str:
        pass

    @abstractclassmethod
    def definition_term(self, e: DefinitionTerm) -> str:
        pass

    @abstractclassmethod
    def definition_desc(self, e: DefinitionDesc) -> str:
        pass

    @abstractclassmethod
    def attachment_transclude(self, e: AttachmentTransclude) -> str:
        pass

    @abstractclassmethod
    def transclude(self, e: Transclude) -> str:
        pass

    @abstractclassmethod
    def attachment_inlined(self, e: AttachmentInlined) -> str:
        pass

    @abstractclassmethod
    def attachment_image(self, e: AttachmentImage) -> str:
        pass

    @abstractclassmethod
    def image(self, e: Image) -> str:
        pass
