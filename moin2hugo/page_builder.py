from typing import Dict, List, Optional, Type

from moin2hugo.page_tree import (
    AttachmentImage,
    AttachmentInlined,
    AttachmentLink,
    AttachmentTransclude,
    Big,
    BulletList,
    Code,
    Comment,
    DefinitionDesc,
    DefinitionList,
    DefinitionTerm,
    Emphasis,
    Heading,
    HorizontalRule,
    Image,
    ImageAttr,
    ImageAttrDict,
    Interwikilink,
    Link,
    LinkAttr,
    LinkAttrDict,
    Listitem,
    Macro,
    NumberList,
    ObjectAttr,
    ObjectAttrDict,
    PageElement,
    Pagelink,
    PageRoot,
    Paragraph,
    ParsedText,
    Remark,
    SGMLEntity,
    Small,
    Smiley,
    Strike,
    Strong,
    Sub,
    Sup,
    Table,
    TableAttr,
    TableCell,
    TableCellAttr,
    TableRow,
    TableRowAttr,
    Text,
    Transclude,
    Underline,
    Url,
)


class PageBuilder(object):
    def __init__(self, verify_doc_structure: bool = False):
        self.page_root: PageRoot = PageRoot()
        self.cur: PageElement = self.page_root
        self.verify_doc_structure = verify_doc_structure

    # Page Bulding Status
    @property
    def in_p(self) -> bool:
        return self.cur.in_x([Paragraph])

    @property
    def in_pre(self) -> bool:
        return isinstance(self.cur, ParsedText)

    @property
    def in_remark(self) -> bool:
        return isinstance(self.cur, Remark)

    @property
    def in_table(self) -> bool:
        return self.cur.in_x([Table])

    @property
    def is_found_parser(self) -> bool:
        assert isinstance(self.cur, ParsedText)
        return bool(self.cur.parser_name)

    @property
    def in_underline(self) -> bool:
        return self.cur.in_x([Underline])

    @property
    def in_strike(self) -> bool:
        return self.cur.in_x([Strike])

    @property
    def in_small(self) -> bool:
        return self.cur.in_x([Small])

    @property
    def in_strong(self) -> bool:
        return self.cur.in_x([Strong])

    @property
    def in_emphasis(self) -> bool:
        return self.cur.in_x([Emphasis])

    @property
    def is_emphasis_before_strong(self) -> bool:
        assert self.in_strong
        assert self.in_emphasis
        found_strong = False
        found_emphasis = False

        above_me = [self.cur] + self.cur.parents
        for e in above_me:
            if isinstance(e, Strong):
                if found_emphasis:
                    return False
                found_strong = True
            if isinstance(e, Emphasis):
                if found_strong:
                    return True
                found_emphasis = True
        else:
            raise AssertionError("This mustn't be reached")

    @property
    def in_big(self) -> bool:
        return self.cur.in_x([Big])

    @property
    def in_table_row(self) -> bool:
        return self.cur.in_x([TableRow])

    @property
    def in_li_of_current_list(self) -> bool:
        return self.cur.in_x([Listitem], upper_bound=[BulletList, NumberList, DefinitionList])

    @property
    def in_dd_of_current_list(self) -> bool:
        return self.cur.in_x(
            [DefinitionDesc], upper_bound=[BulletList, NumberList, DefinitionList]
        )

    @property
    def in_list(self) -> bool:
        return self.cur.in_x([BulletList, NumberList, DefinitionList])

    @property
    def list_types(self) -> List[str]:
        list_types = []
        above_me = [self.cur] + self.cur.parents
        for e in reversed(above_me):
            if isinstance(e, BulletList):
                list_types.append("ul")
            elif isinstance(e, NumberList):
                list_types.append("ol")
            elif isinstance(e, DefinitionList):
                list_types.append("dl")
        return list_types

    # Helpers
    def _ensure_cur_elem(self, x: Type[PageElement]):
        if isinstance(self.cur, x):
            return

        if not self.verify_doc_structure and self.cur.in_x([x]):
            while not isinstance(self.cur, x):
                self._end_current_elem()
        else:
            emsg = "Tree Structure:\n" + self.page_root.tree_repr() + "\n"
            emsg += "Current Elemnt: " + repr(self.cur)
            raise AssertionError(emsg)

    def _add_new_elem(self, e: PageElement):
        self.cur.add_child(e)

    def _start_new_elem(self, e: PageElement):
        self.cur.add_child(e)
        self.cur = e

    def _end_current_elem(self):
        self.cur = self.cur.parent

    def _toggle_elem(self, cls: Type[PageElement], source_text: str = ""):
        if not self.cur.in_x([cls]):
            self._start_new_elem(cls(source_text=source_text))
        else:
            self._ensure_cur_elem(cls)
            self.feed_src(source_text)
            self._end_current_elem()

    # Building Source
    def feed_src(self, source_text: str):
        self.cur.add_source_text(source_text)

    # General Objects
    def paragraph_start(self):
        self._start_new_elem(Paragraph())

    def paragraph_end(self):
        self._ensure_cur_elem(Paragraph)
        self._end_current_elem()

    def text(self, text: str, source_text: str = ""):
        self._add_new_elem(Text(content=text, source_text=source_text))

    def sgml_entity(self, text: str, source_text: str = ""):
        self._add_new_elem(SGMLEntity(content=text, source_text=source_text))

    # Moinwiki Special Objects
    def macro(
        self, macro_name: str, macro_args: Optional[str], markup: str, source_text: str = ""
    ):
        self._add_new_elem(
            Macro(
                macro_name=macro_name,
                macro_args=macro_args,
                markup=markup,
                source_text=source_text,
            )
        )

    def comment(self, text: str, source_text: str = ""):
        self._add_new_elem(Comment(content=text, source_text=source_text))

    def smiley(self, smiley: str, source_text: str = ""):
        self._add_new_elem(Smiley(content=smiley, source_text=source_text))

    def remark_toggle(self, source_text: str = ""):
        self._toggle_elem(Remark, source_text=source_text)

    # Codeblock / ParsedText
    def parsed_text_start(self, source_text: str = ""):
        e = ParsedText(source_text=source_text)
        self._start_new_elem(e)

    def parsed_text_parser(self, parser_name: str, parser_args: Optional[str] = None):
        self._ensure_cur_elem(ParsedText)
        assert isinstance(self.cur, ParsedText)
        self.cur.parser_name = parser_name
        self.cur.parser_args = parser_args

    def add_parsed_text(self, content: str):
        self._ensure_cur_elem(ParsedText)
        self.cur.add_content(content)

    def parsed_text_end(self, source_text: str = ""):
        self._ensure_cur_elem(ParsedText)
        self.feed_src(source_text)
        self._end_current_elem()

    # Table
    def table_start(self, attrs: Dict[str, str] = {}):
        table_attrs = TableAttr.from_dict(attrs)
        self._start_new_elem(Table(attrs=table_attrs))

    def table_end(self):
        self._ensure_cur_elem(Table)
        self._end_current_elem()

    def table_row_start(self, attrs: Dict[str, str] = {}):
        row_attrs = TableRowAttr.from_dict(attrs)
        self._start_new_elem(TableRow(attrs=row_attrs))

    def table_row_end(self):
        self._ensure_cur_elem(TableRow)
        self._end_current_elem()

    def table_cell_start(self, attrs: Dict[str, str] = {}, source_text: str = ""):
        cell_attrs = TableCellAttr.from_dict(attrs)
        self._start_new_elem(TableCell(attrs=cell_attrs, source_text=source_text))

    def table_cell_end(self):
        self._ensure_cur_elem(TableCell)
        self._end_current_elem()

    # Heading / Horizontal Rule
    def heading(self, depth: int, text: str, source_text: str = ""):
        self._add_new_elem(Heading(depth=depth, content=text, source_text=source_text))

    def rule(self, source_text: str = ""):
        self._add_new_elem(HorizontalRule(source_text=source_text))

    # Decoration
    def underline_toggle(self, source_text: str = ""):
        self._toggle_elem(Underline, source_text=source_text)

    def strike_toggle(self, source_text: str = ""):
        self._toggle_elem(Strike, source_text=source_text)

    def big_toggle(self, source_text: str = ""):
        self._toggle_elem(Big, source_text=source_text)

    def small_toggle(self, source_text: str = ""):
        self._toggle_elem(Small, source_text=source_text)

    def strong_toggle(self, source_text: str = ""):
        self._toggle_elem(Strong, source_text=source_text)

    def emphasis_toggle(self, source_text: str = ""):
        self._toggle_elem(Emphasis, source_text=source_text)

    def sup(self, text: str, source_text: str = ""):
        self._add_new_elem(Sup(content=text, source_text=source_text))

    def sub(self, text: str, source_text: str = ""):
        self._add_new_elem(Sub(content=text, source_text=source_text))

    def code(self, text: str, source_text: str = ""):
        self._add_new_elem(Code(content=text, source_text=source_text))

    # Link
    def link_start(
        self,
        url: str,
        attrs: LinkAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        link_attrs = LinkAttr.from_dict(attrs)
        self._start_new_elem(
            Link(url=url, attrs=link_attrs, source_text=source_text, source_frozen=freeze_source)
        )

    def link_end(self):
        self._ensure_cur_elem(Link)
        self._end_current_elem()

    def pagelink_start(
        self,
        pagename: str,
        queryargs: Optional[Dict[str, str]] = None,
        anchor: Optional[str] = None,
        attrs: LinkAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        link_attrs = LinkAttr.from_dict(attrs)
        e = Pagelink(
            pagename=pagename,
            queryargs=queryargs,
            anchor=anchor,
            attrs=link_attrs,
            source_text=source_text,
            source_frozen=freeze_source,
        )
        self._start_new_elem(e)

    def pagelink_end(self):
        self._ensure_cur_elem(Pagelink)
        self._end_current_elem()

    def interwikilink_start(
        self,
        wikiname: str,
        pagename: str,
        queryargs: Optional[Dict[str, str]] = None,
        anchor: Optional[str] = None,
        attrs: LinkAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        link_attrs = LinkAttr.from_dict(attrs)
        e = Interwikilink(
            wikiname=wikiname,
            pagename=pagename,
            queryargs=queryargs,
            anchor=anchor,
            attrs=link_attrs,
            source_text=source_text,
            source_frozen=freeze_source,
        )
        self._start_new_elem(e)

    def interwikilink_end(self):
        self._ensure_cur_elem(Interwikilink)
        self._end_current_elem()

    def attachment_link_start(
        self,
        pagename: str,
        filename: str,
        queryargs: Optional[Dict[str, str]] = None,
        attrs: LinkAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        link_attrs = LinkAttr.from_dict(attrs)
        e = AttachmentLink(
            pagename=pagename,
            filename=filename,
            queryargs=queryargs,
            attrs=link_attrs,
            source_text=source_text,
            source_frozen=freeze_source,
        )
        self._start_new_elem(e)

    def attachment_link_end(self):
        self._ensure_cur_elem(AttachmentLink)
        self._end_current_elem()

    def url(self, text: str, source_text: str = ""):
        self._add_new_elem(Url(content=text, source_text=source_text))

    # Itemlist
    def bullet_list_start(self):
        self._start_new_elem(BulletList())

    def bullet_list_end(self):
        self._ensure_cur_elem(BulletList)
        self._end_current_elem()

    def number_list_start(self, numtype: str = "1", numstart: str = "1"):
        self._start_new_elem(NumberList())

    def number_list_end(self):
        self._ensure_cur_elem(NumberList)
        self._end_current_elem()

    def listitem_start(self):
        self._start_new_elem(Listitem())

    def listitem_end(self):
        self._ensure_cur_elem(Listitem)
        self._end_current_elem()

    def definition_list_start(self):
        self._start_new_elem(DefinitionList())

    def definition_list_end(self):
        self._ensure_cur_elem(DefinitionList)
        self._end_current_elem()

    def definition_term_start(self, source_text: str = "", freeze_source: bool = False):
        self._start_new_elem(DefinitionTerm(source_text=source_text, source_frozen=freeze_source))

    def definition_term_end(self):
        self._ensure_cur_elem(DefinitionTerm)
        self._end_current_elem()

    def definition_desc_start(self):
        self._start_new_elem(DefinitionDesc())

    def definition_desc_end(self):
        self._ensure_cur_elem(DefinitionDesc)
        self._end_current_elem()

    # Transclude (Image Embedding)
    def attachment_image(
        self, pagename: str, filename: str, attrs: ImageAttrDict = {}, source_text: str = ""
    ):
        image_attrs = ImageAttr.from_dict(attrs)
        e = AttachmentImage(
            pagename=pagename, filename=filename, attrs=image_attrs, source_text=source_text
        )
        self._add_new_elem(e)

    def image(self, src: str, attrs: ImageAttrDict = {}, source_text: str = ""):
        image_attrs = ImageAttr.from_dict(attrs)
        self._add_new_elem(Image(src=src, attrs=image_attrs, source_text=source_text))

    # Transclude (Object Embedding)
    def transclusion_start(
        self,
        pagename: str,
        attrs: ObjectAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        obj_attrs = ObjectAttr.from_dict(attrs)
        e = Transclude(
            pagename=pagename,
            attrs=obj_attrs,
            source_text=source_text,
            source_frozen=freeze_source,
        )
        self._start_new_elem(e)

    def transclusion_end(self):
        self._ensure_cur_elem(Transclude)
        self._end_current_elem()

    def attachment_transclusion_start(
        self,
        pagename: str,
        filename: str,
        attrs: ObjectAttrDict = {},
        source_text: str = "",
        freeze_source: bool = False,
    ):
        obj_attrs = ObjectAttr.from_dict(attrs)
        e = AttachmentTransclude(
            pagename=pagename,
            filename=filename,
            attrs=obj_attrs,
            source_text=source_text,
            source_frozen=freeze_source,
        )
        self._start_new_elem(e)

    def attachment_transclusion_end(self):
        self._ensure_cur_elem(AttachmentTransclude)
        self._end_current_elem()

    # Transclude (Other)
    def attachment_inlined(
        self, pagename: str, filename: str, link_text: str, source_text: str = ""
    ):
        self._add_new_elem(
            AttachmentInlined(
                pagename=pagename, filename=filename, link_text=link_text, source_text=source_text
            )
        )
