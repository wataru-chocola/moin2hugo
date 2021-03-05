import sys
import re
import logging
import copy
from typing import List, Dict, Tuple, Any, TextIO, Optional

import moin2hugo.moinutils as wikiutil
import moin2hugo.moin_config as config
import moin2hugo.moin_site_config as site_config

logger = logging.getLogger(__name__)


class AttachFile(object):
    # stub
    pass


class MoinParser(object):
    CHILD_PREFIX = wikiutil.CHILD_PREFIX
    PARENT_PREFIX = wikiutil.PARENT_PREFIX

    punct_pattern = re.escape('''"\'}]|:,.)?!''')
    url_scheme = '|'.join(config.url_schemas)

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
         (?=[^ ]*[%(u)s%(l)s0..9][^ ]*\ )  # make sure there is something non-blank with at least one alphanum letter following
         [^\s%(punct)s]+  # we take all until we hit some blank or punctuation char ...
        )
    ''' % {  # NOQA
        'u': config.chars_upper,
        'l': config.chars_lower,
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
        'u': config.chars_upper,
        'l': config.chars_lower,
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
    indent_re = re.compile(r"^\s*", re.UNICODE)

    # this is used inside parser/pre sections (we just want to know when it's over):
    parser_unique = ''
    parser_scan_rule = r"""
(?P<parser_end>
    %s\}\}\}  # in parser/pre, we only look for the end of the parser/pre
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
    '{5}(?=[^'])  # italic and bold or bold and italic
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
    (?=\s)  # we require some space after the smiley
)|(?P<macro>
    <<
    (?P<macro_name>\w+)  # name of the macro
    (?:\((?P<macro_args>.*?)\))?  # optionally macro arguments
    >>
)|(?P<heading>
    ^(?P<hmarker>=+)\s+  # some === at beginning of line, eat trailing blanks
    (?P<heading_text>.*?)  # capture heading text
    \s+(?P=hmarker)\s$  # some === at end of line (matching amount as we have seen), eat blanks
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
    \|\|\ $  # the right end of a table row
)|(?P<table>
    (?:\|\|)+(?:<(?!<)[^>]*?>)?(?!\|?\s$) # a table
)|(?P<rule>
    -{4,}  # hor. rule, min. 4 -
)|(?P<entity>
    &(
      ([a-zA-Z]+)  # symbolic entity, like &uuml;
      |
      (\#(\d{1,5}|x[0-9a-fA-F]+))  # numeric entities, like &#42; or &#x42;
     );
)|(?P<sgml_entity>  # must come AFTER entity rule!
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
        'u': config.chars_upper,
        'l': config.chars_lower,
        'smiley': '|'.join([re.escape(s) for s in config.smileys])}
    scan_re = re.compile(scan_rules, re.UNICODE | re.VERBOSE)

    def __init__(self, text: str, page_name: str, formatter, writer: Optional[TextIO] = None):
        self.lines = text.expandtabs().splitlines()
        self.page_name = page_name
        self.formatter = formatter

        if writer:
            self.writer = writer
        else:
            self.writer = sys.stdout
        self.macro = None
        self.parser_name = None
        self.parser_args = None
        self.parser_lines = []

        self.line_is_empty = False
        self.line_was_empty = False

        self.is_em = 0  # must be int
        self.is_b = 0  # must be int
        self.is_u = False
        self.is_strike = False
        self.is_big = False
        self.is_small = False
        self.is_remark = False

        self.in_list = False  # between <ul/ol/dl> and </ul/ol/dl>
        self.in_li = False  # between <li> and </li>
        self.in_dd = False  # between <dd> and </dd>

        # states of the parser concerning being inside/outside of some "pre" section:
        # None == we are not in any kind of pre section (was: 0)
        # 'search_parser' == we didn't get a parser yet, still searching for it (was: 1)
        # 'found_parser' == we found a valid parser (was: 2)
        self.in_pre = None

        self.in_table = 0

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []

    # Public Method ----------------------------------------------------------
    @classmethod
    def format(cls, text: str, page_name: str, formatter, writer: Optional[TextIO] = None):
        parser = cls(text, page_name, formatter, writer=writer)
        return parser._format()

    # Private Parsing/Formatting Entrypoint ----------------------------------
    def _format(self):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.line_is_empty = False
        in_processing_instructions = 1

        for line in self.lines:
            self.table_rowstart = 1
            self.line_was_empty = self.line_is_empty
            self.line_is_empty = False
            self.first_list_item = 0

            # ignore processing instructions
            processing_instructions = ["##", "#format", "#refresh", "#redirect", "#deprecated",
                                       "#pragma", "#form", "#acl", "#language"]
            if in_processing_instructions:
                if any((line.lower().startswith(pi) for pi in processing_instructions)):
                    continue
                else:
                    in_processing_instructions = 0

            if not self.in_pre:
                # TODO: we don't have \n as whitespace any more
                # This is the space between lines we join to one paragraph
                line += ' '

                # Paragraph break on empty lines
                if not line.strip():
                    if self.in_table:
                        self.writer.write(self.formatter.table(0))
                        self.in_table = 0
                    # TODO: p should close on every empty line
                    if self.formatter.in_p:
                        self.writer.write(self.formatter.paragraph(0))
                    self.line_is_empty = True
                    continue

                # Handle Indentation
                indlen, indtype, numtype, numstart = self._parse_indentinfo(line)
                self.writer.write(self._indent_to(indlen, indtype, numtype, numstart))

                # Table start / break
                tmp_line = line.lstrip()
                is_table_line = tmp_line.startswith("||") and tmp_line.endswith("|| ") \
                    and len(tmp_line) >= 5
                if not self.in_table and is_table_line:
                    # start table
                    if self.list_types and not self.in_li:
                        self.writer.write(self.formatter.listitem(1, style="list-style-type:none"))
                        self.in_li = True

                    if self.formatter.in_p:
                        self.writer.write(self.formatter.paragraph(0))
                    attrs, attrerr = self._getTableAttrs(line[indlen+2:])
                    self.writer.write(self.formatter.table(1, attrs) + attrerr)
                    self.in_table = True
                elif self.in_table and (not is_table_line) and (not line.startswith("##")):
                    # close table
                    # intra-table comments should not break a table
                    self.writer.write(self.formatter.table(0))
                    self.in_table = False

            # Scan line, format and write
            self._format_line(line)

        # Close code displays, paragraphs, tables and open lists
        self.writer.write(self._undent())
        if self.in_pre: self.writer.write(self.formatter.preformatted(0))
        if self.formatter.in_p: self.writer.write(self.formatter.paragraph(0))
        if self.in_table: self.writer.write(self.formatter.table(0))

    def _format_line(self, line: str):
        lastpos = 0  # absolute position within line
        line_length = len(line)

        while lastpos <= line_length:
            parser_scan_re = re.compile(self.parser_scan_rule % re.escape(self.parser_unique),
                                        re.VERBOSE | re.UNICODE)
            scan_re = parser_scan_re if self.in_pre else self.scan_re
            match = scan_re.search(line, lastpos)
            if not match:
                remainder = line[lastpos:]
                if self.in_pre:
                    # lastpos is more then 0 and result of line slice is empty make useless line
                    if not (lastpos > 0 and remainder == ''):
                        self._parser_content(remainder)
                elif remainder:
                    if not (self.in_pre or self.formatter.in_p or self.in_li or self.in_dd):
                        self.writer.write(self.formatter.paragraph(1))
                    self.writer.write(self.formatter.text(remainder))
                break

            start = match.start()
            if lastpos < start:
                # process leading text
                if self.in_pre:
                    self._parser_content(line[lastpos:start])
                else:
                    if not (self.in_pre or self.formatter.in_p):
                        self.writer.write(self.formatter.paragraph(1))
                    self.writer.write(self.formatter.text(line[lastpos:start]))

            # Replace match with markup
            if not (self.in_pre or self.formatter.in_p or self.in_table or self.in_list):
                self.writer.write(self.formatter.paragraph(1))
            self.writer.write(self._replace(match))
            end = match.end()
            lastpos = end
            if start == end:
                # we matched an empty string
                lastpos += 1  # proceed, we don't want to match this again

    def _replace(self, match: re.Match):
        """ Replace match using type name """
        no_new_p_before = ("heading", "rule", "table", "tableZ", "tr", "td", "ul", "ol", "dl",
                           "dt", "dd", "li", "li_none", "indent", "macro", "parser")
        dispatcher = {
            # Moinwiki Special Syntax
            'macro': self._macro_repl,
            'macro_name': self._macro_repl,
            'macro_args': self._macro_repl,
            'comment': self._comment_repl,
            'remark': self._remark_repl,
            'remark_on': self._remark_repl,
            'remark_off': self._remark_repl,
            'smiley': self._smiley_repl,

            # Codeblock
            'parser': self._parser_repl,
            'parser_unique': self._parser_repl,
            'parser_line': self._parser_repl,
            'parser_name': self._parser_repl,
            'parser_args': self._parser_repl,
            'parser_nothing': self._parser_repl,
            'parser_end': self._parser_end_repl,

            # Table
            'tableZ': self._tableZ_repl,
            'table': self._table_repl,

            # Heading / Horizontal Rule
            'heading': self._heading_repl,
            'heading_text': self._heading_repl,
            'rule': self._rule_repl,

            # Decorations
            'u': self._u_repl,
            'strike': self._strike_repl,
            'strike_on': self._strike_repl,
            'strike_off': self._strike_repl,
            'small': self._small_repl,
            'small_on': self._small_repl,
            'small_off': self._small_repl,
            'big': self._big_repl,
            'big_on': self._big_repl,
            'big_off': self._big_repl,
            'emph': self._emph_repl,
            'emph_ibb': self._emph_ibb_repl,
            'emph_ibi': self._emph_ibi_repl,
            'emph_ib_or_bi': self._emph_ib_or_bi_repl,
            'sup': self._sup_repl,
            'sup_text': self._sup_repl,
            'sub': self._sub_repl,
            'sub_text': self._sub_repl,
            'tt': self._tt_repl,
            'tt_text': self._tt_repl,
            'tt_bt': self._tt_bt_repl,
            'tt_bt_text': self._tt_bt_repl,

            # Links
            'interwiki': self._interwiki_repl,
            'interwiki_wiki': self._interwiki_repl,
            'interwiki_page': self._interwiki_repl,
            'word': self._word_repl,
            'word_bang': self._word_repl,
            'word_name': self._word_repl,
            'word_anchor': self._word_repl,
            'url': self._url_repl,
            'url_target': self._url_repl,
            'url_schema': self._url_repl,
            'link': self._link_repl,
            'link_target': self._link_repl,
            'link_desc': self._link_repl,
            'link_params': self._link_repl,
            'email': self._email_repl,

            # SGML entities
            'entity': self._entity_repl,
            'sgml_entity': self._sgml_entity_repl,

            # List
            'indent': self._indent_repl,
            'li_none': self._li_repl,
            'li': self._li_repl,
            'ol': self._ol_repl,
            'dl': self._dl_repl,

            # Transclude (Image Embedding)
            'transclude': self._transclude_repl,
            'transclude_target': self._transclude_repl,
            'transclude_desc': self._transclude_repl,
            'transclude_params': self._transclude_repl,
        }

        result = []
        for _type, hit in match.groupdict().items():
            if hit is not None and _type not in ["hmarker", ]:
                # Open p for certain types
                if not (self.formatter.in_p or self.in_pre or (_type in no_new_p_before)):
                    result.append(self.formatter.paragraph(1))

                result.append(dispatcher[_type](hit, match.groupdict()))
                return ''.join(result)
        else:
            # We should never get here
            import pprint
            raise Exception("Can't handle match %r\n%s\n%s" % (
                match,
                pprint.pformat(match.groupdict()),
                pprint.pformat(match.groups()),
            ))

        return ""

    # Private Replace Method ----------------------------------------------------------
    def _u_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle underline."""
        self.is_u = not self.is_u
        return self.formatter.underline(self.is_u)

    def _remark_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle remarks: /* ... */"""
        on = groups.get('remark_on')
        if on and self.is_remark:
            return self.formatter.text(word)
        off = groups.get('remark_off')
        if off and not self.is_remark:
            return self.formatter.text(word)
        self.is_remark = not self.is_remark
        return self.formatter.span(self.is_remark)

    def _strike_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle strikethrough."""
        on = groups.get('strike_on')
        if on and self.is_strike:
            return self.formatter.text(word)
        off = groups.get('strike_off')
        if off and not self.is_strike:
            return self.formatter.text(word)
        self.is_strike = not self.is_strike
        return self.formatter.strike(self.is_strike)

    def _small_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle small."""
        on = groups.get('small_on')
        if on and self.is_small:
            return self.formatter.text(word)
        off = groups.get('small_off')
        if off and not self.is_small:
            return self.formatter.text(word)
        self.is_small = not self.is_small
        return self.formatter.small(self.is_small)

    def _big_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle big."""
        on = groups.get('big_on')
        if on and self.is_big:
            return self.formatter.text(word)
        off = groups.get('big_off')
        if off and not self.is_big:
            return self.formatter.text(word)
        self.is_big = not self.is_big
        return self.formatter.big(self.is_big)

    def _emph_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle emphasis, i.e. '' and '''."""
        # ''': b
        # '': em
        if len(word) == 3:
            self.is_b = not self.is_b
            if self.is_em and self.is_b:
                self.is_b = 2
            return self.formatter.strong(self.is_b)
        else:
            self.is_em = not self.is_em
            if self.is_em and self.is_b:
                self.is_em = 2
            return self.formatter.emphasis(self.is_em)

    def _emph_ibb_repl(self, word, groups):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_b = 2
        return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)

    def _emph_ibi_repl(self, word, groups):
        """Handle mixed emphasis, i.e. ''''' followed by ''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_em = 2
        return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)

    def _emph_ib_or_bi_repl(self, word, groups):
        """Handle mixed emphasis, exactly five '''''."""
        b_before_em = False
        if self.is_b and self.is_em:
            # TODO: the following code use a trick that `True` is treated as `1` in math context.
            b_before_em = self.is_b > self.is_em
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if b_before_em:
            return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)
        else:
            return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)

    def _sup_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle superscript."""
        text = groups.get('sup_text', '')
        return self.formatter.sup(text)

    def _sub_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle subscript."""
        text = groups.get('sub_text', '')
        return self.formatter.sub(text)

    def _tt_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle inline code."""
        tt_text = groups.get('tt_text', '')
        return self.formatter.code(tt_text)

    def _tt_bt_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle backticked inline code."""
        tt_bt_text = groups.get('tt_bt_text', '')
        return self.formatter.code(tt_bt_text)

    def _interwiki_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle InterWiki links."""
        text = groups.get('interwiki')
        logger.info("unsupported: interwiki_name=%s" % text)
        return self.formatter.text(text)

    def _word_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle WikiNames."""
        bang = ''
        if groups.get('word_bang'):
            if site_config.bang_meta:
                return self.formatter.text(word)
            bang = self.formatter.text('!')
        current_page = self.page_name
        abs_name = wikiutil.AbsPageName(current_page, groups.get('word_name'))
        # if a simple, self-referencing link, emit it as plain text
        if abs_name == current_page:
            return self.formatter.text(word)

        abs_name, anchor = wikiutil.split_anchor(abs_name)
        return (bang + self.formatter.pagelink(abs_name, word, anchor=anchor))

    def _url_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle literal URLs."""
        target = groups.get('url_target', '')
        return self.formatter.url(target)

    def _link_description(self, desc: str, target: str = '', default_text: str = '') -> str:
        m = self.link_desc_re.match(desc)
        if not m:
            desc = default_text
            if desc:
                desc = self.formatter.text(desc)
            return desc

        if m.group('simple_text'):
            desc = m.group('simple_text')
            desc = self.formatter.text(desc)
        elif m.group('transclude'):
            groupdict = m.groupdict()
            if groupdict.get('transclude_desc') is None:
                # TODO: is this really necessary?
                # if transcluded obj (image) has no description, use target for it
                groupdict['transclude_desc'] = target
            desc = m.group('transclude')
            desc = self._transclude_repl(desc, groupdict)
        return desc

    def _link_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle [[target|text]] links."""
        target = groups.get('link_target', '')
        desc = groups.get('link_desc', '') or ''
        params = groups.get('link_params', '') or ''
        mt = self.link_target_re.match(target)
        if not mt:
            return

        # TODO: don't support all attrs actually
        acceptable_attrs = ['class', 'title', 'target', 'accesskey', 'rel', ]
        tag_attrs, query_args = self._get_params(params, acceptable_attrs=acceptable_attrs)

        if mt.group('page_name'):
            page_name_and_anchor = mt.group('page_name')
            if ':' in page_name_and_anchor:
                # interwiki
                logger.info("unsupported: interwiki_name=%s" % page_name_and_anchor)
                return self.formatter.text(page_name_and_anchor)

            page_name, anchor = wikiutil.split_anchor(page_name_and_anchor)
            current_page = self.page_name
            if not page_name:
                page_name = current_page
            abs_page_name = wikiutil.AbsPageName(current_page, page_name)
            description = self._link_description(desc, target, page_name_and_anchor)
            return self.formatter.pagelink(abs_page_name, description, anchor=anchor,
                                           queryargs=query_args, **tag_attrs)

        elif mt.group('extern_addr'):
            target = mt.group('extern_addr')
            description = self._link_description(desc, target, target)
            return self.formatter.link(target, description, **tag_attrs)

        elif mt.group('attach_scheme'):
            scheme = mt.group('attach_scheme')
            attach_addr = wikiutil.url_unquote(mt.group('attach_addr'))
            if scheme == 'attachment':
                link_description = self._link_description(desc, target, attach_addr)
                return self.formatter.attachment_link(attach_addr, link_description,
                                                      queryargs=query_args, **tag_attrs)
            elif scheme == 'drawing':
                logger.info("unsupported: drawing=%s" % word)
                return self.formatter.text(word)

        else:
            if desc:
                desc = '|' + desc
            return self.formatter.text('[[%s%s]]' % (target, desc))

    def _email_repl(self, word, groups):
        """Handle email addresses (without a leading mailto:)."""
        return self.formatter.url(word)

    def _entity_repl(self, word, groups):
        """Handle numeric (decimal and hexadecimal) and symbolic SGML entities."""
        return self.formatter.raw(word)

    def _sgml_entity_repl(self, word, groups):
        """Handle SGML entities: [<>&]"""
        return self.formatter.text(word)

    def _indent_repl(self, match, groups):
        """Handle pure indentation (no - * 1. markup)."""
        result = []
        if not (self.in_li or self.in_dd):
            self._close_item(result)
            self.in_li = True
            css_class = None
            if self.line_was_empty and not self.first_list_item:
                css_class = 'gap'
            result.append(self.formatter.listitem(1, css_class=css_class, style="list-style-type:none"))
        return ''.join(result)

    def _li_repl(self, match, groups):
        """Handle bullet (" *") lists."""
        result = []
        self._close_item(result)
        self.in_li = True
        css_class = None
        if self.line_was_empty and not self.first_list_item:
            css_class = 'gap'
        result.append(self.formatter.listitem(1, css_class=css_class))
        return ''.join(result)

    def _ol_repl(self, match, groups):
        """Handle numbered lists."""
        return self._li_repl(match, groups)

    def _dl_repl(self, match, groups):
        """Handle definition lists."""
        result = []
        self._close_item(result)
        self.in_dd = 1
        result.extend([
            self.formatter.definition_term(1),
            self.formatter.text(match[1:-3].lstrip(' ')),
            self.formatter.definition_term(0),
            self.formatter.definition_desc(1),
        ])
        return ''.join(result)

    def _transclude_description(self, desc: str, default_text: str = '') -> str:
        """ parse a string <desc> valid as transclude description (text, ...)
            and return the description.

            We do NOT use wikiutil.escape here because it is html specific (the
            html formatter, if used, does this for all html attributes).

            We do NOT call formatter.text here because it sometimes is just used
            for some alt and/or title attribute, but not emitted as text.
        """
        m = self.transclude_desc_re.match(desc)
        if not m:
            return default_text

        if m.group('simple_text'):
            return m.group('simple_text')

    def _transclude_repl(self, word, groups):
        """Handles transcluding content, usually embedding images.: {{}}"""
        target = groups.get('transclude_target', '')
        target = wikiutil.url_unquote(target)

        m = self.link_target_re.match(target)
        if not m:
            # TODO: logging
            return self.formatter.text(word + '???')

        desc = groups.get('transclude_desc', '')
        params = groups.get('transclude_params', '')
        acceptable_attrs_img = ['class', 'title', 'longdesc', 'width', 'height', 'align', ]
        acceptable_attrs_object = ['class', 'title', 'width', 'height', 'type', 'standby', ]

        if m.group('extern_addr'):
            target = m.group('extern_addr')
            desc = self._transclude_description(desc, target)
            tag_attrs = {'alt': desc, 'title': desc, },
            tmp_tag_attrs, query_args = self._get_params(params,
                                                         acceptable_attrs=acceptable_attrs_img)
            tag_attrs.update(tmp_tag_attrs)
            return self.formatter.image(src=target, **tag_attrs)

        elif m.group('attach_scheme'):
            scheme = m.group('attach_scheme')
            url = wikiutil.url_unquote(m.group('attach_addr'))
            if scheme == 'attachment':
                mt = wikiutil.MimeType(filename=url)
                if mt.major == 'text':
                    # TODO:
                    desc = self._transclude_description(desc, url)
                    return self.formatter.attachment_inlined(url, desc)

                if mt.major == 'image' and mt.minor in config.browser_supported_images:
                    desc = self._transclude_description(desc, url)
                    tag_attrs = {'alt': desc, 'title': desc, },
                    tmp_tag_attrs, query_args = \
                        self._get_params(params, acceptable_attrs=acceptable_attrs_img)
                    tag_attrs.update(tmp_tag_attrs)
                    return self.formatter.attachment_image(url, **tag_attrs)

                # non-text, unsupported images, or other filetypes
                pagename, filename = AttachFile.absoluteName(url, self.page_name)
                if AttachFile.exists(pagename, filename):
                    href = AttachFile.getAttachUrl(pagename, filename)
                    tag_attrs = {'title': desc, },
                    tmp_tag_attrs, query_args = \
                        self._get_params(params, acceptable_attrs=acceptable_attrs_object)
                    tag_attrs.update(tmp_tag_attrs)
                    return (self.formatter.transclusion(1, data=href, type=mt.spoil(), **tag_attrs) +
                            self.formatter.text(self._transclude_description(desc, url)) +
                            self.formatter.transclusion(0))
                else:
                    description = self.formatter.text(self._transclude_description(desc, url))
                    return self.formatter.attachment_link(url, description)

            elif scheme == 'drawing':
                logger.info("unsupported: drawing=%s" % word)
                return self.formatter.text(word)

        elif m.group('page_name'):
            page_name_all = m.group('page_name')
            if ':' in page_name_all:
                logger.info("unsupported: interwiki_name=%s" % page_name_all)
                return self.formatter.text(word)

            tag_attrs = {'type': 'text/html', 'width': '100%', },
            tmp_tag_attrs, query_args = \
                self._get_params(params, acceptable_attrs=acceptable_attrs_object)
            tag_attrs.update(tmp_tag_attrs)
            if 'action' not in query_args:
                query_args['action'] = 'content'
            url = Page(page_name_all).url(queryargs=query_args)
            return (self.formatter.transclusion(1, data=url, **tag_attrs) +
                    self.formatter.text(self._transclude_description(desc, page_name_all)) +
                    self.formatter.transclusion(0))

        else:
            desc = self._transclude_description(desc, target)
            return self.formatter.text('{{%s|%s|%s}}' % (target, desc, params))

    def _getTableAttrs(self, attrdef):
        attr_rule = r'^(\|\|)*<(?!<)(?P<attrs>[^>]*?)>'
        m = re.match(attr_rule, attrdef, re.U)
        if not m:
            return {}, ''
        attrdef = m.group('attrs')

        # extension for special table markup
        def table_extension(key, parser, attrs, wiki_parser=self):
            """ returns: tuple (found_flag, msg)
                found_flag: whether we found something and were able to process it here
                  true for special stuff like 100% or - or #AABBCC
                  false for style xxx="yyy" attributes
                msg: "" or an error msg
            """
            _ = wiki_parser._
            found = False
            msg = ''
            if key[0] in "0123456789":
                token = parser.get_token()
                if token != '%':
                    wanted = '%'
                    msg = _('Expected "%(wanted)s" after "%(key)s", got "%(token)s"') % {
                        'wanted': wanted, 'key': key, 'token': token}
                else:
                    try:
                        _ = int(key)
                    except ValueError:
                        msg = _('Expected an integer "%(key)s" before "%(token)s"') % {
                            'key': key, 'token': token}
                    else:
                        found = True
                        attrs['width'] = '"%s%%"' % key
            elif key == '-':
                arg = parser.get_token()
                try:
                    _ = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['colspan'] = '"%s"' % arg
            elif key == '|':
                arg = parser.get_token()
                try:
                    _ = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['rowspan'] = '"%s"' % arg
            elif key == '(':
                found = True
                attrs['align'] = '"left"'
            elif key == ':':
                found = True
                attrs['align'] = '"center"'
            elif key == ')':
                found = True
                attrs['align'] = '"right"'
            elif key == '^':
                found = True
                attrs['valign'] = '"top"'
            elif key == 'v':
                found = True
                attrs['valign'] = '"bottom"'
            elif key == '#':
                arg = parser.get_token()
                try:
                    if len(arg) != 6:
                        raise ValueError
                    _ = int(arg, 16)
                except ValueError:
                    msg = _('Expected a color value "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['bgcolor'] = '"#%s"' % arg
            return found, self.formatter.rawHTML(msg)

        # scan attributes
        attr, msg = wikiutil.parseAttributes(attrdef, '>', table_extension)
        if msg:
            msg = '<strong class="highlight">%s</strong>' % msg
        return attr, msg

    def _tableZ_repl(self, word, groups):
        """Handle table row end."""
        if self.in_table:
            result = ''
            if self.formatter.in_p:
                result = self.formatter.paragraph(0)
            result += self.formatter.table_cell(0) + self.formatter.table_row(0)
            return result
        else:
            return self.formatter.text(word)

    def _table_repl(self, word, groups):
        """Handle table cell separator."""
        if self.in_table:
            result = []
            attrs, attrerr = self._getTableAttrs(word)

            # start the table row?
            if self.table_rowstart:
                self.table_rowstart = 0
                result.append(self.formatter.table_row(1, attrs))
            else:
                # Close table cell, first closing open p
                # REMOVED check for self.in_li, paragraph should close always!
                if self.formatter.in_p:
                    result.append(self.formatter.paragraph(0))
                result.append(self.formatter.table_cell(0))

            # check for adjacent cell markers
            if word.count("|") > 2:
                if 'align' not in attrs and \
                   not ('style' in attrs and 'text-align' in attrs['style'].lower()):
                    # add center alignment if we don't have some alignment already
                    attrs['align'] = '"center"'
                if 'colspan' not in attrs:
                    attrs['colspan'] = '"%d"' % (word.count("|")/2)

            # return the complete cell markup
            result.append(self.formatter.table_cell(1, attrs) + attrerr)
            return ''.join(result)
        else:
            return self.formatter.text(word)

    # Heading / Horizontal Rule
    def _heading_repl(self, word: str, groups: Dict[str, str]):
        """Handle section headings.: == =="""
        heading_text = groups.get('heading_text', '')
        depth = min(len(groups.get('hmarker')), 5)
        return ''.join([
            self._closeP(),
            self.formatter.heading(depth, heading_text),
        ])

    def _rule_repl(self, word: str, groups: Dict[str, str]):
        """Handle sequences of dashes (Horizontal Rule)."""
        result = self._undent() + self._closeP()
        result += self.formatter.rule()
        return result

    def _parser_repl(self, word: str, groups: Dict[str, str]) -> str:
        """Handle parsed code displays."""
        self.parser_name = None
        self.parser_args = None
        self.parser_lines = []
        self.in_pre = 'search_parser'

        parser_name = groups.get('parser_name', None)
        parser_args = groups.get('parser_args', None)
        parser_nothing = groups.get('parser_nothing', None)

        parser_unique = groups.get('parser_unique', '') or ''
        if set(parser_unique) == set('{'):  # just some more {{{{{{
            parser_unique = '}' * len(parser_unique)  # for symmetry cosmetic reasons
        self.parser_unique = parser_unique

        if parser_name is not None:
            if parser_name == '':
                parser_name = 'text'
                word = ''
        elif parser_nothing is None:
            parser_name = 'text'

        if parser_name:
            if self._set_parser(parser_name):
                self.parser_args = parser_args
                word = ''
            else:
                # loading the desired parser didn't work, retry a safe option:
                self._set_parser('text')
                word = ''

        if self.parser_name:
            self.in_pre = 'found_parser'
            if word:
                self.parser_lines.append(word)

        return ''

    def _parser_content(self, line):
        """ handle state and collecting lines for parser in pre/parser sections """
        if self.in_pre == 'search_parser' and line.strip():
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

            if parser_name:
                parser_name = 'text'

            if self._set_parser(parser_name):
                self.parser_args = parser_args
            else:
                self._set_parser('text')

            self.in_pre = 'found_parser'
            if not bang_line:
                self.parser_lines.append(line)

        elif self.in_pre == 'found_parser':
            self.parser_lines.append(line)

        return ''

    def _parser_end_repl(self, word, groups):
        """ when we reach the end of a parser/pre section,
            we call the parser with the lines we collected
        """
        self.in_pre = None
        self.writer.write(self._closeP())
        parser_name = self.parser_name
        if parser_name is None:
            parser_name = 'text'
        result = self.formatter.parser(parser_name, self.parser_args, self.parser_lines)

        self.parser_lines = []
        self.in_pre = None
        self.parser_name = None
        self.parser_args = None
        return result

    def _smiley_repl(self, word: str, groups: Dict[str, str]) -> str:
        return self.formatter.smiley(word)

    def _comment_repl(self, word, groups):
        # if we are in a paragraph, we must close it so that normal text following
        # in the line below the comment will reopen a new paragraph.
        if self.formatter.in_p:
            self.formatter.paragraph(0)
        self.line_is_empty = True  # markup following comment lines treats them as if they were empty
        return self.formatter.comment(word)

    def _macro_repl(self, word: str, groups: Dict[str, str]):
        """Handle macros."""
        macro_name = groups.get('macro_name')
        macro_args = groups.get('macro_args')

        if self.macro is None:
            self.macro = macro.Macro(self)
        return self.formatter.macro(self.macro, macro_name, macro_args, markup=groups.get('macro'))

    # Private helpers ------------------------------------------------------------
    def _parse_indentinfo(self, line: str) -> Tuple[int, str, Optional[str], Optional[int]]:
        indent = self.indent_re.match(line)
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
        else:
            return self.list_indents[-1]

    def _indent_to(self, new_level, list_type, numtype, numstart):
        """Close and open lists."""
        openlist = []   # don't make one out of these two statements!
        closelist = []

        if self._indent_level() != new_level and self.in_table:
            closelist.append(self.formatter.table(0))
            self.in_table = 0

        while self._indent_level() > new_level:
            self._close_item(closelist)
            if self.list_types[-1] == 'ol':
                tag = self.formatter.number_list(0)
            elif self.list_types[-1] == 'dl':
                tag = self.formatter.definition_list(0)
            else:
                tag = self.formatter.bullet_list(0)
            closelist.append(tag)

            del self.list_indents[-1]
            del self.list_types[-1]

            if self.list_types:  # we are still in a list
                if self.list_types[-1] == 'dl':
                    self.in_dd = True
                else:
                    self.in_li = True

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)

            if self.formatter.in_p:
                closelist.append(self.formatter.paragraph(0))

            if list_type == 'ol':
                tag = self.formatter.number_list(1, numtype, numstart)
            elif list_type == 'dl':
                tag = self.formatter.definition_list(1)
            else:
                tag = self.formatter.bullet_list(1)
            openlist.append(tag)

            self.first_list_item = 1
            self.in_li = False
            self.in_dd = False

        # If list level changes, close an open table
        if self.in_table and (openlist or closelist):
            closelist[0:0] = [self.formatter.table(0)]
            self.in_table = 0

        self.in_list = self.list_types != []
        return ''.join(closelist) + ''.join(openlist)

    def _undent(self):
        """Close all open lists."""
        result = []
        self._close_item(result)
        for _type in self.list_types[::-1]:
            if _type == 'ol':
                result.append(self.formatter.number_list(0))
            elif _type == 'dl':
                result.append(self.formatter.definition_list(0))
            else:
                result.append(self.formatter.bullet_list(0))
        self.list_indents = []
        self.list_types = []
        return ''.join(result)

    def _close_item(self, result):
        if self.in_table:
            result.append(self.formatter.table(0))
            self.in_table = 0
        if self.in_li:
            self.in_li = 0
            if self.formatter.in_p:
                result.append(self.formatter.paragraph(0))
            result.append(self.formatter.listitem(0))
        if self.in_dd:
            self.in_dd = 0
            if self.formatter.in_p:
                result.append(self.formatter.paragraph(0))
            result.append(self.formatter.definition_desc(0))

    def _closeP(self):
        if self.formatter.in_p:
            return self.formatter.paragraph(0)
        return ''

    def _get_params(self, params: Dict[str, Any], acceptable_attrs: List[str] = []
                    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """ parse the parameters of link/transclusion markup,
            defaults can be a dict with some default key/values
            that will be in the result as given, unless overriden
            by the params.
        """
        tag_attrs = {}
        query_args = {}
        if params:
            fixed, kw, trailing = wikiutil.parse_quoted_separated(params)
            # we ignore fixed and trailing args and only use kw args:
            for key, val in kw.items():
                if key in acceptable_attrs:
                    # tag attributes must be string type
                    tag_attrs[str(key)] = val
                elif key.startswith('&'):
                    key = key[1:]
                    query_args[key] = val
        return tag_attrs, query_args

    def _set_parser(self, name: str) -> bool:
        available_parsers = ('text', 'highlight')
        if name in available_parsers:
            self.parser_name = name
            return True
        else:
            logger.warning("unsupported parser: %s" % name)
            return False
