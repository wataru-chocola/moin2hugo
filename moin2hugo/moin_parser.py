import re
import logging
from typing import List, Dict, Tuple, Optional, TypeVar

import moin2hugo.page_builder
import moin2hugo.moinutils as wikiutil
import moin2hugo.moin_settings as settings
from moin2hugo.page_tree import LinkAttrDict, LinkAttrKey
from moin2hugo.page_tree import ImageAttrDict, ImageAttrKey
from moin2hugo.page_tree import ObjectAttrDict, ObjectAttrKey
from moin2hugo.config import MoinSiteConfig

T = TypeVar('T')
logger = logging.getLogger(__name__)


class MoinParser(object):
    CHILD_PREFIX = wikiutil.CHILD_PREFIX
    PARENT_PREFIX = wikiutil.PARENT_PREFIX

    punct_pattern = re.escape('''"\'}]|:,.)?!''')
    url_scheme = '|'.join(settings.url_schemas)

    # some common rules
    url_rule = r'''
        (?:^|(?<=\W))  # require either beginning of line or some non-alphanum char (whitespace, punctuation) to the left
        (?P<url_target>  # capture whole url there
         (?P<url_scheme>%(url_scheme)s)  # some scheme
         \:
         \S+?  # anything non-whitespace
        )
        (?:$|(?=\s|[%(punct)s]+(\s|$)))  # require either end of line or some whitespace or some punctuation+blank/eol afterwards
    ''' % {  # NOQA
        'url_scheme': url_scheme,
        'punct': punct_pattern,
    }

    # this is for a free (non-bracketed) interwiki link - to avoid false positives,
    # we are rather restrictive here (same as in moin 1.5: require that the
    # interwiki_wiki name starts with an uppercase letter A-Z. Later, the code
    # also checks whether the wiki name is in the interwiki map (if not, it renders
    # normal text, no link):
    interwiki_rule = r'''
        (?:^|(?<=\W))  # require either beginning of line or some non-alphanum char (whitespace, punctuation) to the left
        (?P<interwiki_wiki>[A-Z][a-zA-Z]+)  # interwiki wiki name
        \:
        (?P<interwiki_page>  # interwiki page name
         (?=[^ ]*[%(u)s%(l)s0..9][^ ]*([\s%(punct)s]|\Z))  # make sure there is something non-blank with at least one alphanum letter following
         [^\s%(punct)s]+  # we take all until we hit some blank or punctuation char ...
        )
    ''' % {  # NOQA
        'u': settings.chars_upper,
        'l': settings.chars_lower,
        'punct': punct_pattern,
    }

    word_rule = r'''
        (?:
         (?<![%(u)s%(l)s/])  # require anything not upper/lower/slash before
         |
         ^  # ... or beginning of line
        )
        (?P<word_bang>\!)?  # configurable: avoid getting CamelCase rendered as link
        (?P<word_name>
         (?:
          (%(parent)s)*  # there might be either ../ parent prefix(es)
          |
          ((?<!%(child)s)%(child)s)?  # or maybe a single / child prefix (but not if we already had it before)
         )
         (
          ((?<!%(child)s)%(child)s)?  # there might be / child prefix (but not if we already had it before)
          (?:[%(u)s][%(l)s]+){2,}  # at least 2 upper>lower transitions make CamelCase
         )+  # we can have MainPage/SubPage/SubSubPage ...
         (?:
          \#  # anchor separator          TODO check if this does not make trouble at places where word_rule is used
          (?P<word_anchor>\S+)  # some anchor name
         )?
        )
        (?:
         (?![%(u)s%(l)s/])  # require anything not upper/lower/slash following
         |
         $  # ... or end of line
        )
    ''' % {  # NOQA
        'u': settings.chars_upper,
        'l': settings.chars_lower,
        'child': re.escape(CHILD_PREFIX),
        'parent': re.escape(PARENT_PREFIX),
    }

    # link targets:
    extern_rule = r'(?P<extern_addr>(?P<extern_scheme>%s)\:.*)' % url_scheme
    attach_rule = r'(?P<attach_scheme>attachment|drawing)\:(?P<attach_addr>.*)'
    page_rule = r'(?P<page_name>.*)'

    link_target_rules = r'|'.join([
        extern_rule,
        attach_rule,
        page_rule,
    ])
    link_target_re = re.compile(link_target_rules, re.VERBOSE | re.UNICODE)

    link_rule = r"""
        (?P<link>
            \[\[  # link target
            \s*  # strip space
            (?P<link_target>[^|]+?)
            \s*  # strip space
            (
                \|  # link description
                \s*  # strip space
                (?P<link_desc>
                    (?:  # 1. we have either a transclusion here (usually a image)
                        \{\{
                        \s*[^|]+?\s*  # usually image target (strip space)
                        (\|\s*[^|]*?\s*  # usually image alt text (optional, strip space)
                            (\|\s*[^|]*?\s*  # transclusion parameters (usually key="value" format, optional, strip space)
                            )?
                        )?
                        \}\}
                    )
                    |
                    (?:  # 2. or we have simple text here.
                        [^|]+?
                    )
                )?
                \s*  # strip space
                (
                    \|  # link parameters
                    \s*  # strip space
                    (?P<link_params>[^|]+?)?
                    \s*  # strip space
                )?
            )?
            \]\]
        )
    """  # NOQA

    transclude_rule = r"""
        (?P<transclude>
            \{\{
            \s*(?P<transclude_target>[^|]+?)\s*  # usually image target (strip space)
            (\|\s*(?P<transclude_desc>[^|]+?)?\s*  # usually image alt text (optional, strip space)
                (\|\s*(?P<transclude_params>[^|]+?)?\s*  # transclusion parameters (usually key="value" format, optional, strip space)
                )?
            )?
            \}\}
        )
    """  # NOQA
    text_rule = r"""
        (?P<simple_text>
            [^|]+  # some text (not empty, does not contain separator)
        )
    """
    # link descriptions:
    link_desc_rules = r'|'.join([
            transclude_rule,
            text_rule,
    ])
    link_desc_re = re.compile(link_desc_rules, re.VERBOSE | re.UNICODE)

    # transclude descriptions:
    transclude_desc_rules = r'|'.join([
            text_rule,
    ])
    transclude_desc_re = re.compile(transclude_desc_rules, re.VERBOSE | re.UNICODE)

    # lists:
    ol_rule = r"""
        ^\s+  # indentation
        (?:[0-9]+|[aAiI])\. # arabic, alpha, roman counting
        (?:\#\d+)?  # optional start number
        \s  # require one blank afterwards
    """
    ol_re = re.compile(ol_rule, re.VERBOSE | re.UNICODE)

    dl_rule = r"""
        ^\s+  # indentation
        .*?::  # definition term::
        \s  # require on blank afterwards
    """
    dl_re = re.compile(dl_rule, re.VERBOSE | re.UNICODE)

    # others
    indent_re: re.Pattern = re.compile(r"^\s*", re.UNICODE)

    # this is used inside parser/pre sections (we just want to know when it's over):
    parser_unique = ''
    parser_scan_rule = r"""
(?P<parser_end>
    %s\}\}\}\n?  # in parser/pre, we only look for the end of the parser/pre
)
"""

    # the big, fat, less ugly one ;)
    # please be very careful: blanks and # must be escaped with \ !
    scan_rules = r"""
(?P<emph_ibb>
    '''''(?=[^']+''')  # italic on, bold on, ..., bold off
)|(?P<emph_ibi>
    '''''(?=[^']+'')  # italic on, bold on, ..., italic off
)|(?P<emph_ib_or_bi>
    '{5}(?=[^']|$)  # italic and bold or bold and italic
)|(?P<emph>
    '{2,3}  # italic or bold
)|(?P<u>
    __ # underline
)|(?P<small>
    (
     (?P<small_on>\~-\ ?)  # small on (we eat a trailing blank if it is there)
    |
     (?P<small_off>-\~)  # small off
    )
)|(?P<big>
    (
     (?P<big_on>\~\+\ ?)  # big on (eat trailing blank)
    |
     (?P<big_off>\+\~)  # big off
    )
)|(?P<strike>
    (
     (?P<strike_on>--\()  # strike-through on
    |
     (?P<strike_off>\)--)  # strike-through off
    )
)|(?P<remark>
    (
     (^|(?<=\s))  # we require either beginning of line or some whitespace before a remark begin
     (?P<remark_on>/\*\s)  # inline remark on (require and eat whitespace after it)
    )
    |
    (
     (?P<remark_off>\s\*/)  # off (require and eat whitespace before it)
     (?=\s)  # we require some whitespace after a remark end
    )
)|(?P<sup>
    \^  # superscript on
    (?P<sup_text>.*?)  # capture the text
    \^  # off
)|(?P<sub>
    ,,  # subscript on
    (?P<sub_text>.*?)  # capture the text
    ,,  # off
)|(?P<tt>
    \{\{\{  # teletype on
    (?P<tt_text>.*?)  # capture the text
    \}\}\}  # off
)|(?P<tt_bt>
    `  # teletype (using a backtick) on
    (?P<tt_bt_text>.*?)  # capture the text
    `  # off
)|(?P<interwiki>
    %(interwiki_rule)s  # OtherWiki:PageName
)|(?P<word>  # must come AFTER interwiki rule!
    %(word_rule)s  # CamelCase wiki words
)|
%(link_rule)s
|
%(transclude_rule)s
|(?P<url>
    %(url_rule)s
)|(?P<email>
    [-\w._+]+  # name
    \@  # at
    [\w-]+(\.[\w-]+)+  # server/domain
)|(?P<smiley>
    (^|(?<=\s))  # we require either beginning of line or some space before a smiley
    (%(smiley)s)  # one of the smileys
    (?=(\s|\Z))  # we require some space after the smiley
)|(?P<macro>
    <<
    (?P<macro_name>\w+)  # name of the macro
    (?:\((?P<macro_args>.*?)\))?  # optionally macro arguments
    >>
)|(?P<heading>
    ^(?P<hmarker>=+)\s+  # some === at beginning of line, eat trailing blanks
    (?P<heading_text>.*?)  # capture heading text
    \s+(?P=hmarker)\s?$  # some === at end of line (matching amount as we have seen), eat blanks
)|(?P<parser>
    \{\{\{  # parser on
    (?P<parser_unique>(\{*|\w*))  # either some more {{{{ or some chars to solve the nesting problem
    (?P<parser_line>
     (
      \#!  # hash bang
      (?P<parser_name>\w*)  # we have a parser name (can be empty) directly following the {{{
      (
       \s+  # some space ...
       (?P<parser_args>.+?)  # followed by parser args
      )?  # parser args are optional
      \s*  # followed by whitespace (eat it) until EOL
     )
    |
     (?P<parser_nothing>\s*)  # no parser name, only whitespace up to EOL (eat it)
    )$
    # "parser off" detection is done with parser_scan_rule!
)|(?P<comment>
    ^\#\#.*$  # src code comment, rest of line
)|(?P<ol>
    %(ol_rule)s  # ordered list
)|(?P<dl>
    %(dl_rule)s  # definition list
)|(?P<li>
    ^\s+\*\s*  # unordered list
)|(?P<li_none>
    ^\s+\.\s*  # unordered list, no bullets
)|(?P<indent>
    ^\s+  # indented by some spaces
)|(?P<tableZ>
    \|\|\n?$  # the right end of a table row
)|(?P<table>
    (?:\|\|)+(?:<(?!<)[^>]*?>)?(?!\|?\s$) # a table
)|(?P<rule>
    -{4,}  # hor. rule, min. 4 -
)|(?P<sgml_entity>
    &(
      ([a-zA-Z]+)  # symbolic entity, like &uuml;
      |
      (\#(\d{1,5}|x[0-9a-fA-F]+))  # numeric entities, like &#42; or &#x42;
     );
)|(?P<sgml_special_symbol>  # must come AFTER entity rule!
    [<>&]  # needs special treatment for html/xml
)""" % {  # NOQA
        'url_scheme': url_scheme,
        'url_rule': url_rule,
        'punct': punct_pattern,
        'ol_rule': ol_rule,
        'dl_rule': dl_rule,
        'interwiki_rule': interwiki_rule,
        'word_rule': word_rule,
        'link_rule': link_rule,
        'transclude_rule': transclude_rule,
        'u': settings.chars_upper,
        'l': settings.chars_lower,
        'smiley': '|'.join([re.escape(s) for s in settings.smileys])}
    scan_re = re.compile(scan_rules, re.UNICODE | re.VERBOSE)

    available_parsers = ('text', 'highlight')

    def __init__(self, text: str, page_name: str, site_config: Optional[MoinSiteConfig] = None):
        if site_config:
            self.site_config = site_config
        else:
            self.site_config = MoinSiteConfig()
        self.builder = moin2hugo.page_builder.PageBuilder()
        self.lines = text.expandtabs().splitlines(keepends=True)
        self.page_name = page_name
        self.list_indents: List[int] = []  # holds the nesting level (in chars) of open lists

    # Public Method ----------------------------------------------------------
    @classmethod
    def parse(cls, text: str, page_name: str, site_config: Optional[MoinSiteConfig] = None):
        parser = cls(text, page_name, site_config=site_config)
        return parser.run_parse()

    # Private Parsing/Formatting Entrypoint ----------------------------------
    def run_parse(self):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        in_processing_instructions = 1

        for line in self.lines:
            # ignore processing instructions
            processing_instructions = ["##", "#format", "#refresh", "#redirect", "#deprecated",
                                       "#pragma", "#form", "#acl", "#language"]
            if in_processing_instructions:
                if any((line.lower().startswith(pi) for pi in processing_instructions)):
                    self.builder.comment(line, source_text=line)
                    continue
                in_processing_instructions = 0

            if not self.builder.in_pre:
                # Paragraph break on empty lines
                if not line.strip():
                    if self.builder.in_table:
                        self.builder.table_end()
                    if self.builder.in_p:
                        self.builder.paragraph_end()
                    self.builder.feed_src(line)
                    continue

                # Handle Indentation
                indlen, indtype, numtype, numstart = self._parse_indentinfo(line)
                self._indent_to(indlen, indtype, numtype, numstart)

                # Table start / break
                tmp_line = line.strip()
                is_table_line = tmp_line.startswith("||") and tmp_line.endswith("||") \
                    and len(tmp_line) >= 5
                if not self.builder.in_table and is_table_line:
                    # start table
                    if self.builder.in_p:
                        self.builder.paragraph_end()
                    attrs = _getTableAttrs(tmp_line[2:])
                    self.builder.table_start(attrs)
                elif self.builder.in_table and not (is_table_line or line.startswith("##")):
                    # intra-table comments should not break a table
                    self.builder.table_end()

            # Scan and parse line
            self._parse_line(line)

        # Close code displays, paragraphs, tables and open lists
        self._undent()
        if self.builder.in_p:
            self.builder.paragraph_end()
        if self.builder.in_table:
            self.builder.table_end()

        return self.builder.page_root

    def _parse_line(self, line: str):
        lastpos = 0  # absolute position within line
        line_length = len(line)

        while lastpos <= line_length:
            parser_scan_re = re.compile(self.parser_scan_rule % re.escape(self.parser_unique),
                                        re.VERBOSE | re.UNICODE)
            scan_re = parser_scan_re if self.builder.in_pre else self.scan_re
            match = scan_re.search(line, lastpos)
            if not match:
                remainder = line[lastpos:]
                if self.builder.in_pre:
                    # lastpos is more then 0 and result of line slice is empty make useless line
                    if not (lastpos > 0 and remainder == ''):
                        self._parser_content(remainder)
                elif remainder:
                    if not (self.builder.in_pre or self.builder.in_p or
                            self.builder.in_li_of_current_list or
                            self.builder.in_dd_of_current_list or
                            self.builder.in_remark):
                        self.builder.paragraph_start()
                    self.builder.text(remainder, source_text=remainder)
                break

            start = match.start()
            if lastpos < start:
                # process leading text
                if self.builder.in_pre:
                    self._parser_content(line[lastpos:start])
                else:
                    if not (self.builder.in_p or self.builder.in_remark):
                        self.builder.paragraph_start()
                    self.builder.text(line[lastpos:start], source_text=line[lastpos:start])

            # TODO: this makes unneccesary paragraph some cases
            # Replace match with markup
            if not (self.builder.in_pre or self.builder.in_p or self.builder.in_table
                    or self.builder.in_list or self.builder.in_remark):
                self.builder.paragraph_start()
            self._process_markup(match)
            end = match.end()
            lastpos = end
            if start == end:
                # we matched an empty string
                lastpos += 1  # proceed, we don't want to match this again

    def _process_markup(self, match: re.Match):
        """ Replace match using type name """
        no_new_p_before = ("heading", "rule", "table", "tableZ", "tr", "td", "ul", "ol", "dl",
                           "dt", "dd", "li", "li_none", "indent", "macro", "parser")
        dispatcher = {
            # Moinwiki Special Syntax
            'macro': self._macro_handler,
            'macro_name': self._macro_handler,
            'macro_args': self._macro_handler,
            'comment': self._comment_handler,
            'remark': self._remark_handler,
            'remark_on': self._remark_handler,
            'remark_off': self._remark_handler,
            'smiley': self._smiley_handler,

            # Codeblock
            'parser': self._parser_handler,
            'parser_unique': self._parser_handler,
            'parser_line': self._parser_handler,
            'parser_name': self._parser_handler,
            'parser_args': self._parser_handler,
            'parser_nothing': self._parser_handler,
            'parser_end': self._parser_end_handler,

            # Table
            'tableZ': self._tableZ_handler,
            'table': self._table_handler,

            # Heading / Horizontal Rule
            'heading': self._heading_handler,
            'heading_text': self._heading_handler,
            'rule': self._rule_handler,

            # Decorations
            'u': self._u_handler,
            'strike': self._strike_handler,
            'strike_on': self._strike_handler,
            'strike_off': self._strike_handler,
            'small': self._small_handler,
            'small_on': self._small_handler,
            'small_off': self._small_handler,
            'big': self._big_handler,
            'big_on': self._big_handler,
            'big_off': self._big_handler,
            'emph': self._emph_handler,
            'emph_ibb': self._emph_ibb_handler,
            'emph_ibi': self._emph_ibi_handler,
            'emph_ib_or_bi': self._emph_ib_or_bi_handler,
            'sup': self._sup_handler,
            'sup_text': self._sup_handler,
            'sub': self._sub_handler,
            'sub_text': self._sub_handler,
            'tt': self._tt_handler,
            'tt_text': self._tt_handler,
            'tt_bt': self._tt_bt_handler,
            'tt_bt_text': self._tt_bt_handler,

            # Links
            'interwiki': self._interwiki_handler,
            'interwiki_wiki': self._interwiki_handler,
            'interwiki_page': self._interwiki_handler,
            'word': self._word_handler,
            'word_bang': self._word_handler,
            'word_name': self._word_handler,
            'word_anchor': self._word_handler,
            'link': self._link_handler,
            'link_target': self._link_handler,
            'link_desc': self._link_handler,
            'link_params': self._link_handler,
            'url': self._url_handler,
            'url_target': self._url_handler,
            'url_schema': self._url_handler,
            'email': self._email_handler,

            # SGML entities
            'sgml_entity': self._sgml_entity_handler,
            'sgml_special_symbol': self._sgml_special_symbol_handler,

            # Itemlist
            'indent': self._indent_handler,
            'li_none': self._li_handler,
            'li': self._li_handler,
            'ol': self._ol_handler,
            'dl': self._dl_handler,

            # Transclude (Image Embedding)
            'transclude': self._transclude_handler,
            'transclude_target': self._transclude_handler,
            'transclude_desc': self._transclude_handler,
            'transclude_params': self._transclude_handler,
        }

        for _type, hit in match.groupdict().items():
            if hit is None:
                continue
            if self.builder.in_remark and _type not in ["remark"]:
                # original moin-1.9 parser parses even inside inline comments.
                # it breaks tree structure, so we avoid it..
                self.builder.text(hit, source_text=hit)
                return
            if _type not in ["hmarker", ]:
                # Open p for certain types
                if not (self.builder.in_p or self.builder.in_pre or (_type in no_new_p_before)):
                    self.builder.paragraph_start()
                dispatcher[_type](hit, match.groupdict())
                return
        else:
            # We should never get here
            import pprint
            raise Exception("Can't handle match %r\n%s\n%s" % (
                match,
                pprint.pformat(match.groupdict()),
                pprint.pformat(match.groups()),
            ))

    # Private Replace Method ----------------------------------------------------------
    def _remark_handler(self, word: str, groups: Dict[str, str]):
        """Handle remarks: /* ... */"""
        on = groups.get('remark_on')
        off = groups.get('remark_off')
        if (on and self.builder.in_remark) or (off and not self.builder.in_remark):
            self.builder.text(word, source_text=word)
            return
        self.builder.remark_toggle(source_text=word)

    def _u_handler(self, word: str, groups: Dict[str, str]):
        """Handle underline."""
        self.builder.underline_toggle(source_text=word)

    def _strike_handler(self, word: str, groups: Dict[str, str]):
        """Handle strikethrough."""
        on = groups.get('strike_on')
        off = groups.get('strike_off')
        if (on and self.builder.in_strike) or (off and not self.builder.in_strike):
            self.builder.text(word, source_text=word)
            return
        self.builder.strike_toggle(source_text=word)

    def _small_handler(self, word: str, groups: Dict[str, str]):
        """Handle small."""
        on = groups.get('small_on')
        off = groups.get('small_off')
        if (on and self.builder.in_small) or (off and not self.builder.in_small):
            self.builder.text(word, source_text=word)
            return
        self.builder.small_toggle(source_text=word)

    def _big_handler(self, word: str, groups: Dict[str, str]):
        """Handle big."""
        on = groups.get('big_on')
        off = groups.get('big_off')
        if (on and self.builder.in_big) or (off and not self.builder.in_big):
            self.builder.text(word, source_text=word)
            return
        self.builder.big_toggle(source_text=word)

    def _emph_handler(self, word: str, groups: Dict[str, str]):
        """Handle emphasis, i.e. ''(em) and '''(b)."""
        if len(word) == 3:
            self.builder.strong_toggle(source_text=word)
        else:
            self.builder.emphasis_toggle(source_text=word)

    def _emph_ibb_handler(self, word: str, groups: Dict[str, str]):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self.builder.emphasis_toggle(source_text="''")
        self.builder.strong_toggle(source_text="'''")

    def _emph_ibi_handler(self, word: str, groups: Dict[str, str]):
        """Handle mixed emphasis, i.e. ''''' followed by ''."""
        self.builder.strong_toggle(source_text="'''")
        self.builder.emphasis_toggle(source_text="''")

    def _emph_ib_or_bi_handler(self, word: str, groups: Dict[str, str]):
        """Handle mixed emphasis, exactly five '''''."""
        if self.builder.in_emphasis and self.builder.in_strong \
                and self.builder.is_emphasis_before_strong:
            self.builder.strong_toggle(source_text="'''")
            self.builder.emphasis_toggle(source_text="''")
        else:
            self.builder.emphasis_toggle(source_text="''")
            self.builder.strong_toggle(source_text="'''")

    def _sup_handler(self, word: str, groups: Dict[str, str]):
        """Handle superscript."""
        text = groups.get('sup_text', '')
        self.builder.sup(text, source_text=word)

    def _sub_handler(self, word: str, groups: Dict[str, str]):
        """Handle subscript."""
        text = groups.get('sub_text', '')
        self.builder.sub(text, source_text=word)

    def _tt_handler(self, word: str, groups: Dict[str, str]):
        """Handle inline code."""
        tt_text = groups.get('tt_text', '')
        self.builder.code(tt_text, source_text=word)

    def _tt_bt_handler(self, word: str, groups: Dict[str, str]):
        """Handle backticked inline code."""
        tt_bt_text = groups.get('tt_bt_text', '')
        self.builder.code(tt_bt_text, source_text=word)

    def _interwiki_handler(self, word: str, groups: Dict[str, str]):
        """Handle InterWiki links."""
        wikiname = groups.get('interwiki_wiki', '')
        pagename = groups.get('interwiki_page', '')
        pagename, anchor = wikiutil.split_anchor(pagename)
        self.builder.interwikilink_start(wikiname, pagename, anchor=anchor,
                                         source_text=word, freeze_source=True)
        self.builder.text(word, source_text=word)
        self.builder.interwikilink_end()

    def _word_handler(self, word: str, groups: Dict[str, str]):
        """Handle WikiNames."""
        if groups.get('word_bang'):
            if self.site_config.bang_meta:
                self.builder.text(word, source_text=word)
                return
        current_page = self.page_name
        abs_name = wikiutil.abs_page(current_page, groups.get('word_name', ''))
        # if a simple, self-referencing link, emit it as plain text
        if abs_name == current_page:
            self.builder.text(word, source_text=word)
            return
        abs_name, anchor = wikiutil.split_anchor(abs_name)
        self.builder.pagelink_start(abs_name, anchor=anchor)
        self.builder.text(word, source_text=word)
        self.builder.pagelink_end()

    def _url_handler(self, word: str, groups: Dict[str, str]):
        """Handle literal URLs."""
        target = groups.get('url_target', '')
        self.builder.url(target, source_text=word)

    def _link_description(self, desc: str, target: str = '', default_text: str = ''):
        m = self.link_desc_re.match(desc)
        if not m:
            desc = default_text
            if desc:
                self.builder.text(desc, source_text=desc)
            return

        if m.group('simple_text'):
            desc = m.group('simple_text')
            self.builder.text(desc, source_text=desc)
        elif m.group('transclude'):
            groupdict = m.groupdict()
            if groupdict.get('transclude_desc') is None:
                # TODO: is this really necessary?
                # if transcluded obj (image) has no description, use target for it
                groupdict['transclude_desc'] = target
            desc = m.group('transclude')
            desc = self._transclude_handler(desc, groupdict)

    def _link_handler(self, word: str, groups: Dict[str, str]):
        """Handle [[target|text]] links."""
        target = groups.get('link_target', '')
        desc = groups.get('link_desc', '') or ''
        params = groups.get('link_params', '') or ''
        mt = self.link_target_re.match(target)
        if not mt:
            return
        tag_attrs, query_args = _get_link_params(params)

        if mt.group('page_name'):
            page_name_and_anchor = mt.group('page_name')
            page_name, anchor = wikiutil.split_anchor(page_name_and_anchor)
            if ':' in page_name:
                wikiname, pagename = page_name.split(':', 1)
                self.builder.interwikilink_start(wikiname, page_name, queryargs=query_args,
                                                 anchor=anchor, attrs=tag_attrs,
                                                 source_text=word, freeze_source=True)
                self.builder.text(page_name_and_anchor, source_text=word)
                self.builder.interwikilink_end()
                return

            current_page = self.page_name
            if not page_name:
                page_name = current_page
            abs_page_name = wikiutil.abs_page(current_page, page_name)
            self.builder.pagelink_start(abs_page_name, anchor=anchor,
                                        queryargs=query_args, attrs=tag_attrs,
                                        source_text=word, freeze_source=True)
            self._link_description(desc, target, page_name_and_anchor)
            self.builder.pagelink_end()

        elif mt.group('extern_addr'):
            target = mt.group('extern_addr')
            self.builder.link_start(target, attrs=tag_attrs, source_text=word, freeze_source=True)
            self._link_description(desc, target, target)
            self.builder.link_end()

        elif mt.group('attach_scheme'):
            scheme = mt.group('attach_scheme')
            attach_addr = wikiutil.url_unquote(mt.group('attach_addr'))
            pagename, filename = wikiutil.attachment_abs_name(attach_addr, self.page_name)
            if scheme == 'attachment':
                self.builder.attachment_link_start(pagename=pagename, filename=filename,
                                                   queryargs=query_args, attrs=tag_attrs,
                                                   source_text=word, freeze_source=True)
                self._link_description(desc, target, attach_addr)
                self.builder.attachment_link_end()
            elif scheme == 'drawing':
                logger.warning("unsupported: drawing=%s" % word)
                self.builder.text(word, source_text=word)
            else:
                logger.warning("unsupported: scheme=%s" % scheme)
                self.builder.text(word, source_text=word)
        else:
            if desc:
                desc = '|' + desc
            self.builder.text('[[%s%s]]' % (target, desc), source_text=word)

    def _email_handler(self, word: str, groups: Dict[str, str]):
        """Handle email addresses (without a leading mailto:)."""
        self.builder.url(word, source_text=word)

    def _sgml_entity_handler(self, word: str, groups: Dict[str, str]):
        """Handle numeric (decimal and hexadecimal) and symbolic SGML entities."""
        self.builder.sgml_entity(word, source_text=word)

    def _sgml_special_symbol_handler(self, word: str, groups: Dict[str, str]):
        """Handle SGML entities: [<>&]"""
        self.builder.text(word, source_text=word)

    def _indent_handler(self, word: str, groups: Dict[str, str]):
        """Handle pure indentation (no - * 1. markup)."""
        if not (self.builder.in_li_of_current_list or self.builder.in_dd_of_current_list):
            self._close_item()
            self.builder.listitem_start()
        self.builder.feed_src(word)

    def _li_handler(self, word: str, groups: Dict[str, str]):
        """Handle bullet (" *") lists."""
        self._close_item()
        self.builder.listitem_start()
        self.builder.feed_src(word)

    def _ol_handler(self, word: str, groups: Dict[str, str]):
        """Handle numbered lists."""
        self._li_handler(word, groups)

    def _dl_handler(self, word: str, groups: Dict[str, str]):
        """Handle definition lists."""
        self._close_item()
        self.builder.definition_term_start(source_text=word, freeze_source=True)
        term = word[1:-3].lstrip(' ')
        self.builder.text(term, source_text=term)
        self.builder.definition_term_end()
        self.builder.definition_desc_start()

    def _transclude_description(self, desc: str) -> Optional[str]:
        m = self.transclude_desc_re.match(desc)
        if not m:
            return None
        return m.group('simple_text')

    def _transclude_handler(self, word: str, groups: Dict[str, str]):
        """Handles transcluding content, usually embedding images.: {{}}"""
        target = groups.get('transclude_target', '')
        target = wikiutil.url_unquote(target)

        m = self.link_target_re.match(target)
        if not m:
            self.builder.text(word + '???', source_text=word)
            return

        desc = groups.get('transclude_desc', '') or ''
        params = groups.get('transclude_params', '')

        image_tag_attrs: ImageAttrDict = {}
        obj_tag_attrs: ObjectAttrDict = {}

        if m.group('extern_addr'):
            target = m.group('extern_addr')
            trans_desc = self._transclude_description(desc)
            if trans_desc:
                image_tag_attrs['alt'] = trans_desc
                image_tag_attrs['title'] = trans_desc
            tmp_image_tag_attrs, query_args = _get_image_params(params)
            image_tag_attrs.update(tmp_image_tag_attrs)
            self.builder.image(src=target, source_text=word, attrs=image_tag_attrs)

        elif m.group('attach_scheme'):
            scheme = m.group('attach_scheme')
            attach_addr = wikiutil.url_unquote(m.group('attach_addr'))
            pagename, filename = wikiutil.attachment_abs_name(attach_addr, self.page_name)
            if scheme == 'attachment':
                mtype, majortype, subtype = wikiutil.filename2mimetype(filename=filename)
                if majortype == 'text':
                    trans_desc = self._transclude_description(desc)
                    if trans_desc is None:
                        trans_desc = attach_addr
                    self.builder.attachment_inlined(pagename, filename, trans_desc,
                                                    source_text=word)
                elif majortype == 'image' and subtype in settings.browser_supported_images:
                    trans_desc = self._transclude_description(desc)
                    if trans_desc:
                        image_tag_attrs['alt'] = trans_desc
                        image_tag_attrs['title'] = trans_desc
                    tmp_image_tag_attrs, query_args = _get_image_params(params)
                    image_tag_attrs.update(tmp_image_tag_attrs)
                    self.builder.attachment_image(pagename=pagename, filename=filename,
                                                  source_text=word, attrs=image_tag_attrs)
                else:
                    # non-text, unsupported images, or other filetypes
                    obj_tag_attrs['title'] = desc
                    obj_tag_attrs['mimetype'] = mtype
                    tmp_obj_tag_attrs, query_args = _get_object_params(params)
                    obj_tag_attrs.update(tmp_obj_tag_attrs)

                    trans_desc = self._transclude_description(desc)
                    if trans_desc is None:
                        trans_desc = attach_addr

                    self.builder.attachment_transclusion_start(
                        pagename=pagename, filename=filename, attrs=obj_tag_attrs,
                        source_text=word, freeze_source=True)
                    self.builder.text(trans_desc, source_text=desc)
                    self.builder.attachment_transclusion_end()

            elif scheme == 'drawing':
                logger.warning("unsupported: drawing=%s" % word)
                self.builder.text(word, source_text=word)

        elif m.group('page_name'):
            page_name_all = m.group('page_name')
            if ':' in page_name_all:
                logger.warning("unsupported: interwiki_name=%s" % page_name_all)
                self.builder.text(word, source_text=word)
                return

            obj_tag_attrs['mimetype'] = 'text/html'
            obj_tag_attrs['width'] = '100%'
            tmp_obj_tag_attrs, query_args = _get_object_params(params)
            obj_tag_attrs.update(tmp_obj_tag_attrs)
            # TODO
            if 'action' not in query_args:
                query_args['action'] = 'content'

            trans_desc = self._transclude_description(desc)
            if trans_desc is None:
                trans_desc = page_name_all

            self.builder.transclusion_start(pagename=page_name_all, attrs=obj_tag_attrs,
                                            source_text=word, freeze_source=True)
            self.builder.text(trans_desc, source_text=desc)
            self.builder.transclusion_end()

        else:
            trans_desc = self._transclude_description(desc)
            if trans_desc is None:
                trans_desc = target
            self.builder.text('{{%s|%s|%s}}' % (target, trans_desc, params), source_text=word)

    def _tableZ_handler(self, word: str, groups: Dict[str, str]):
        """Handle table row end."""
        if self.builder.in_table:
            self.builder.feed_src(word)
            if self.builder.in_p:
                self.builder.paragraph_end()
            self.builder.table_cell_end()
            self.builder.table_row_end()
        else:
            self.builder.text(word, source_text=word)

    def _table_handler(self, word: str, groups: Dict[str, str]):
        """Handle table cell separator."""
        if self.builder.in_table:
            attrs = _getTableAttrs(word)

            # start the table row?
            if not self.builder.in_table_row:
                self.builder.table_row_start(attrs)
            else:
                # Close table cell, first closing open p
                if self.builder.in_p:
                    self.builder.paragraph_end()
                self.builder.table_cell_end()

            # check for adjacent cell markers
            if word.count("|") > 2:
                if 'align' not in attrs and \
                   not ('style' in attrs and 'text-align' in attrs['style'].lower()):
                    # add center alignment if we don't have some alignment already
                    attrs['align'] = '"center"'
                if 'colspan' not in attrs:
                    attrs['colspan'] = '"%d"' % (word.count("|")/2)

            self.builder.table_cell_start(attrs, source_text=word)
        else:
            self.builder.text(word, source_text=word)

    # Heading / Horizontal Rule
    def _heading_handler(self, word: str, groups: Dict[str, str]):
        """Handle section headings.: == =="""
        heading_text = groups.get('heading_text', '')
        depth = min(len(groups.get('hmarker', '')), 5)
        self._close_paragraph()
        self.builder.heading(depth, heading_text, source_text=word)

    def _rule_handler(self, word: str, groups: Dict[str, str]):
        """Handle sequences of dashes (Horizontal Rule)."""
        self._undent()
        self._close_paragraph()
        self.builder.rule(source_text=word)

    def _parser_handler(self, word: str, groups: Dict[str, str]):
        """Handle parsed code displays."""
        parser_name = groups.get('parser_name', None)
        parser_args = groups.get('parser_args', None)
        parser_nothing = groups.get('parser_nothing', None)

        parser_unique = groups.get('parser_unique', '') or ''
        if set(parser_unique) == set('{'):  # just some more {{{{{{
            parser_unique = '}' * len(parser_unique)  # for symmetry cosmetic reasons
        self.parser_unique = parser_unique

        if parser_name is not None and parser_name == '':
            parser_name = 'text'
        if parser_name is None and parser_nothing is None:
            parser_name = 'text'

        self._close_paragraph()
        self.builder.parsed_text_start(source_text=word)

        if parser_name:
            if parser_name not in self.available_parsers:
                logger.warning("unsupported parser: %s" % parser_name)
                parser_name = 'text'
                parser_args = None
            self.builder.parsed_text_parser(parser_name, parser_args)

    def _parser_content(self, line: str):
        """ handle state and collecting lines for parser in pre/parser sections """
        self.builder.feed_src(line)
        if self.builder.is_found_parser:
            self.builder.add_parsed_text(line)
        elif line.strip():
            bang_line = False
            stripped_line = line.strip()
            parser_name = ''
            parser_args = None

            if stripped_line.startswith("#!"):
                bang_line = True
                tmp = stripped_line[2:].split(None, 2)
                if len(tmp) == 2:
                    parser_name, parser_args = tmp
                elif len(tmp) == 1:
                    parser_name = tmp[0]

            if not parser_name:
                parser_name = 'text'

            if parser_name not in self.available_parsers:
                logger.warning("unsupported parser: %s" % parser_name)
                parser_name = 'text'

            self.builder.parsed_text_parser(parser_name, parser_args)
            if not bang_line:
                self.builder.add_parsed_text(line)

    def _parser_end_handler(self, word: str, groups: Dict[str, str]):
        """ when we reach the end of a parser/pre section,
            we call the parser with the lines we collected
        """
        if not self.builder.is_found_parser:
            self.builder.parsed_text_parser('text')
        self.builder.parsed_text_end(source_text=word)

    def _smiley_handler(self, word: str, groups: Dict[str, str]):
        self.builder.smiley(word, source_text=word)

    def _comment_handler(self, word, groups):
        if self.builder.in_p:
            self.builder.paragraph_end()
        self.builder.comment(word, source_text=word)

    def _macro_handler(self, word: str, groups: Dict[str, str]):
        """Handle macros."""
        macro_name = groups.get('macro_name', '')
        macro_args = groups.get('macro_args')
        self.builder.macro(macro_name, macro_args, markup=groups.get('macro', ''),
                           source_text=word)

    # Private helpers ------------------------------------------------------------
    def _parse_indentinfo(self, line: str) -> Tuple[int, str, Optional[str], Optional[int]]:
        indent = self.indent_re.match(line)
        indlen = 0
        if indent:
            indlen = len(indent.group(0))
        indtype = "ul"
        numtype = None
        numstart = None

        if not indlen:
            return (indlen, indtype, numtype, numstart)

        match = self.ol_re.match(line)
        if match:
            indtype = "ol"
            numtype, tmp_numstart = match.group(0).strip().split('.')
            numtype = numtype[0]
            if tmp_numstart and tmp_numstart[0] == "#":
                numstart = int(tmp_numstart[1:])
        elif self.dl_re.match(line):
            indtype = "dl"

        return (indlen, indtype, numtype, numstart)

    def _indent_level(self):
        """Return current char-wise indent level."""
        if not self.list_indents:
            return 0
        return self.list_indents[-1]

    def _indent_to(self, new_level, list_type, numtype, numstart):
        """Close and open lists."""
        if self._indent_level() != new_level and self.builder.in_table:
            self.builder.table_end()

        while self._indent_level() > new_level:
            if self.builder.in_table:
                self.builder.table_end()

            self._close_item()
            if self.builder.list_types[-1] == 'ol':
                self.builder.number_list_end()
            elif self.builder.list_types[-1] == 'dl':
                self.builder.definition_list_end()
            else:
                self.builder.bullet_list_end()

            del self.list_indents[-1]

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)

            if self.builder.in_table:
                self.builder.table_end()

            if self.builder.in_p:
                self.builder.paragraph_end()

            if list_type == 'ol':
                self.builder.number_list_start(numtype, numstart)
            elif list_type == 'dl':
                self.builder.definition_list_start()
            else:
                self.builder.bullet_list_start()

    def _undent(self):
        """Close all open lists."""
        self._close_item()
        for _type in self.builder.list_types[::-1]:
            if _type == 'ol':
                self.builder.number_list_end()
            elif _type == 'dl':
                self.builder.definition_list_end()
            else:
                self.builder.bullet_list_end()
            self._close_item()
        self.list_indents = []

    def _close_item(self):
        if self.builder.in_table:
            self.builder.table_end()
        if self.builder.in_li_of_current_list:
            self._close_paragraph()
            self.builder.listitem_end()
        elif self.builder.in_dd_of_current_list:
            self._close_paragraph()
            self.builder.definition_desc_end()

    def _close_paragraph(self):
        if self.builder.in_p:
            self.builder.paragraph_end()


def _get_image_params(paramstring: str) -> Tuple[ImageAttrDict, Dict[str, str]]:
    acceptable: List[ImageAttrKey] = ['class', 'title', 'longdesc', 'width', 'height', 'align']
    return _get_params(paramstring, acceptable_attrs=acceptable)


def _get_object_params(paramstring: str) -> Tuple[ObjectAttrDict, Dict[str, str]]:
    acceptable: List[ObjectAttrKey] = ['class', 'title', 'width', 'height', 'mimetype', 'standby']
    tag_attrs, query_args = _get_params(paramstring, acceptable_attrs=acceptable,
                                        mapping={'type': 'mimetype'})
    return tag_attrs, query_args


def _get_link_params(paramstring: str) -> Tuple[LinkAttrDict, Dict[str, str]]:
    acceptable_attrs_link: List[LinkAttrKey] = ['class', 'title', 'target', 'accesskey', 'rel', ]
    return _get_params(paramstring, acceptable_attrs=acceptable_attrs_link)


def _get_params(paramstring: str, acceptable_attrs: List[T] = [], mapping: Dict[str, str] = {},
                ) -> Tuple[Dict[T, str], Dict[str, str]]:
    """ parse the parameters of link/transclusion markup,
        defaults can be a dict with some default key/values
        that will be in the result as given, unless overriden
        by the params.
    """
    tag_attrs: Dict[T, str] = {}
    query_args = {}
    if paramstring:
        _fixed, kw, _trailing = wikiutil.parse_quoted_separated(paramstring)
        for key, val in kw.items():
            if key in mapping:
                key = mapping[key]
            if key in acceptable_attrs:
                tag_attrs[key] = val
            elif key.startswith('&'):
                key = key[1:]
                query_args[key] = val
    return tag_attrs, query_args


def _getTableAttrs(attrdef: str) -> Dict[str, str]:
    attr_rule = r'^(\|\|)*<(?!<)(?P<attrs>[^>]*?)>'
    m = re.match(attr_rule, attrdef, re.U)
    if not m:
        return {}
    attrdef = m.group('attrs')

    # extension for special table markup
    def table_extension(key, parser):
        align_keys = {'(': 'left', ':': 'center', ')': 'right'}
        valign_keys = {'^': 'top', 'v': 'bottom'}

        attrs = {}
        if key[0] in "0123456789":
            token = parser.get_token()
            if token != '%':
                raise ValueError('Expected "%%" after "%(key)s", got "%(token)s"' % {
                    'key': key, 'token': token})
            _ = int(key)
            attrs['width'] = '"%s%%"' % key
        elif key == '-':
            arg = parser.get_token()
            _ = int(arg)
            attrs['colspan'] = '"%s"' % arg
        elif key == '|':
            arg = parser.get_token()
            _ = int(arg)
            attrs['rowspan'] = '"%s"' % arg
        elif key in align_keys:
            attrs['align'] = '"%s"' % align_keys[key]
        elif key in valign_keys:
            attrs['valign'] = '"%s"' % valign_keys[key]
        elif key == '#':
            arg = parser.get_token()
            if len(arg) != 6:
                raise ValueError()
            _ = int(arg, 16)
            attrs['bgcolor'] = '"#%s"' % arg
        return attrs

    # scan attributes
    attr = wikiutil.parseAttributes(attrdef, '>', table_extension)
    return attr
