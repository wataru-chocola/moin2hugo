from moin2hugo.page_tree import (
    PageRoot, PageElement,
    Macro, Comment, Smiley, Remark,
    ParsedText,
    Table, TableRow, TableCell,
    Emphasis, Strong, Big, Small, Underline, Strike, Sup, Sub, Code,
    BulletList, NumberList, Listitem,
    DefinitionList, DefinitionTerm, DefinitionDesc,
    Heading, HorizontalRule,
    Link, Pagelink, Url, AttachmentLink,
    Paragraph, Text, SGMLEntity,
    AttachmentTransclude, Transclude,
    AttachmentInlined, AttachmentImage, Image
)

from typing import List, Dict, Optional, Type


class PageBuilder(object):
    def __init__(self):
        self.page_root = PageRoot()
        self.cur = self.page_root

    # Helpers
    def assert_cur_elem(self, x: Type[PageElement]):
        if not isinstance(self.cur, x):
            emsg = "Tree Structure:\n" + self.page_root.print_structure() + "\n"
            emsg += "Current Elemnt: " + repr(self.cur)
            raise AssertionError(emsg)

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
        assert self.in_pre
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
    def in_li_of_current_list(self) -> bool:
        return self.cur.in_x([Listitem], upper_bound=[BulletList, NumberList, DefinitionList])

    @property
    def in_dd_of_current_list(self) -> bool:
        return self.cur.in_x([DefinitionDesc],
                             upper_bound=[BulletList, NumberList, DefinitionList])

    @property
    def in_list(self) -> bool:
        return self.cur.in_x([BulletList, NumberList, DefinitionList])

    @property
    def list_types(self) -> List[str]:
        list_types = []
        above_me = [self.cur] + self.cur.parents
        for e in reversed(above_me):
            if isinstance(e, BulletList):
                list_types.append('ul')
            elif isinstance(e, NumberList):
                list_types.append('ol')
            elif isinstance(e, DefinitionList):
                list_types.append('dl')
        return list_types

    # Helpers
    def _add_new_elem(self, e: PageElement):
        self.cur.add_child(e)

    def _start_new_elem(self, e: PageElement):
        self.cur.add_child(e)
        self.cur = e

    def _end_current_elem(self):
        self.cur = self.cur.parent

    # General Objects
    def paragraph_start(self):
        self._start_new_elem(Paragraph())

    def paragraph_end(self):
        self._end_current_elem()

    def text(self, text: str):
        self._add_new_elem(Text(content=text))

    def sgml_entity(self, text: str):
        self._add_new_elem(SGMLEntity(content=text))

    # Moinwiki Special Objects
    def macro(self, macro_name: str, macro_args: Optional[str], markup: str):
        self._add_new_elem(Macro(macro_name=macro_name, macro_args=macro_args, markup=markup))

    def comment(self, text: str):
        self._add_new_elem(Comment(content=text))

    def smiley(self, smiley: str):
        self._add_new_elem(Smiley(content=smiley))

    def remark_toggle(self):
        if not self.in_remark:
            self._start_new_elem(Remark())
        else:
            self.assert_cur_elem(Remark)
            self._end_current_elem()

    # Codeblock / ParsedText
    def parsed_text_start(self):
        e = ParsedText()
        self._start_new_elem(e)

    def parsed_text_parser(self, parser_name: str, parser_args: Optional[str] = None):
        self.assert_cur_elem(ParsedText)
        self.cur.parser_name = parser_name
        self.cur.parser_args = parser_args

    def parsed_text_end(self, lines: List[str]):
        self.assert_cur_elem(ParsedText)
        self.cur.content = ''.join(lines)
        self._end_current_elem()

    def preformatted(self, on):
        # TODO: needed?
        pass

    # Table
    def table_start(self, attrs: Dict[str, str] = {}):
        self._start_new_elem(Table(attrs=attrs))

    def table_end(self):
        self.assert_cur_elem(Table)
        self._end_current_elem()

    def table_row_start(self, attrs: Dict[str, str] = {}):
        self._start_new_elem(TableRow(attrs=attrs))

    def table_row_end(self):
        self.assert_cur_elem(TableRow)
        self._end_current_elem()

    def table_cell_start(self, attrs: Dict[str, str] = {}):
        self._start_new_elem(TableCell(attrs=attrs))

    def table_cell_end(self):
        self.assert_cur_elem(TableCell)
        self._end_current_elem()

    # Heading / Horizontal Rule
    def heading(self, depth: int, text: str):
        self._add_new_elem(Heading(depth=depth, content=text))

    def rule(self):
        self._add_new_elem(HorizontalRule())

    # Decoration
    def underline_toggle(self):
        if not self.in_underline:
            self._start_new_elem(Underline())
        else:
            self.assert_cur_elem(Underline)
            self._end_current_elem()

    def strike_toggle(self):
        if not self.in_strike:
            self._start_new_elem(Strike())
        else:
            self.assert_cur_elem(Strike)
            self._end_current_elem()

    def big_toggle(self):
        if not self.in_big:
            self._start_new_elem(Big())
        else:
            self.assert_cur_elem(Big)
            self._end_current_elem()

    def small_toggle(self):
        if not self.in_small:
            self._start_new_elem(Small())
        else:
            self.assert_cur_elem(Small)
            self._end_current_elem()

    def strong_toggle(self):
        if not self.in_strong:
            self._start_new_elem(Strong())
        else:
            self.assert_cur_elem(Strong)
            self._end_current_elem()

    def emphasis_toggle(self):
        if not self.in_emphasis:
            self._start_new_elem(Emphasis())
        else:
            self.assert_cur_elem(Emphasis)
            self._end_current_elem()

    def sup(self, text: str):
        self._add_new_elem(Sup(content=text))

    def sub(self, text: str):
        self._add_new_elem(Sub(content=text))

    def code(self, text: str):
        self._add_new_elem(Code(content=text))

    # Link
    def link_start(self, target: str, title: Optional[str] = None):
        # TODO: extra link attributes
        self._start_new_elem(Link(target=target, title=title))

    def link_end(self):
        self.assert_cur_elem(Link)
        self._end_current_elem()

    def pagelink_start(self, pagename: str = '', queryargs: Optional[Dict[str, str]] = None,
                       anchor: Optional[str] = None,
                       target: Optional[str] = None):
        # TODO: extra link attributes
        e = Pagelink(pagename=pagename, queryargs=queryargs, anchor=anchor)
        self._start_new_elem(e)

    def pagelink_end(self):
        self.assert_cur_elem(Pagelink)
        self._end_current_elem()

    def attachment_link_start(self, pagename: str, filename: str, title: Optional[str] = None,
                              queryargs: Optional[Dict[str, str]] = None):
        # TODO: extra link attributes
        e = AttachmentLink(pagename=pagename, filename=filename, title=title, queryargs=queryargs)
        self._start_new_elem(e)

    def attachment_link_end(self):
        self.assert_cur_elem(AttachmentLink)
        self._end_current_elem()

    def url(self, text: str):
        self._add_new_elem(Url(content=text))

    # Itemlist
    def bullet_list_start(self):
        self._start_new_elem(BulletList())

    def bullet_list_end(self):
        self.assert_cur_elem(BulletList)
        self._end_current_elem()

    def number_list_start(self, numtype: str = '1', numstart: str = '1'):
        self._start_new_elem(NumberList())

    def number_list_end(self):
        self.assert_cur_elem(NumberList)
        self._end_current_elem()

    def listitem_start(self):
        self._start_new_elem(Listitem())

    def listitem_end(self):
        self.assert_cur_elem(Listitem)
        self._end_current_elem()

    def definition_list_start(self):
        self._start_new_elem(DefinitionList())

    def definition_list_end(self):
        self.assert_cur_elem(DefinitionList)
        self._end_current_elem()

    def definition_term_start(self):
        self._start_new_elem(DefinitionTerm())

    def definition_term_end(self):
        self.assert_cur_elem(DefinitionTerm)
        self._end_current_elem()

    def definition_desc_start(self):
        self._start_new_elem(DefinitionDesc())

    def definition_desc_end(self):
        self.assert_cur_elem(DefinitionDesc)
        self._end_current_elem()

    # Transclude (Image Embedding)
    def transclusion_start(self, pagename: str, mimetype: str, title: Optional[str] = None,
                           width: Optional[str] = None):
        # TODO: extra object attributes
        e = Transclude(pagename=pagename, mimetype=mimetype, title=title, width=width)
        self._start_new_elem(e)

    def transclusion_end(self):
        self.assert_cur_elem(Transclude)
        self._end_current_elem()

    def attachment_transclusion_start(self, pagename: str, filename: str, mimetype: str,
                                      title: Optional[str] = None, width: Optional[str] = None):
        # TODO: extra object attributes
        e = AttachmentTransclude(pagename=pagename, filename=filename, mimetype=mimetype,
                                 title=title, width=width)
        self._start_new_elem(e)

    def attachment_transclusion_end(self):
        self.assert_cur_elem(AttachmentTransclude)
        self._end_current_elem()

    def attachment_image(self, pagename: str, filename: str, title: Optional[str] = None,
                         width: Optional[str] = None, height: Optional[str] = None,
                         alt: Optional[str] = '', align: Optional[str] = None):
        # TODO: extra image attributes
        e = AttachmentImage(pagename=pagename, filename=filename, title=title,
                            width=width, height=height, align=align)
        self._add_new_elem(e)

    def attachment_inlined(self, pagename: str, filename: str, link_text: str):
        self._add_new_elem(AttachmentInlined(pagename=pagename, filename=filename,
                                             link_text=link_text))

    def image(self, src: str, alt: str = '', title: Optional[str] = None,
              align: Optional[str] = None):
        # TODO: extra image attributes
        self._add_new_elem(Image(src=src, alt=alt, title=title, align=align))
