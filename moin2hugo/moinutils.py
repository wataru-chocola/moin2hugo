import re
import urllib.parse
import html
import shlex
import logging
import mimetypes

from io import StringIO
from typing import Tuple

logger = logging.getLogger(__name__)

PARENT_PREFIX = "../"
CHILD_PREFIX = "/"


class InvalidFileNameError(Exception):
    pass


def split_anchor(pagename: str) -> Tuple[str, str]:
    parts = pagename.rsplit('#', 1)
    if len(parts) == 2:
        pagename, anchor = parts
        return (pagename, anchor)
    return (pagename, "")


def resolve_wiki(request, wikiurl):
    # TODO
    raise NotImplementedError()


def join_wiki(wikiurl, wikitail):
    # TODO
    raise NotImplementedError()


# TODO: parser like stuff
class BracketError(Exception):
    pass


class BracketUnexpectedCloseError(BracketError):
    def __init__(self, bracket):
        self.bracket = bracket
        BracketError.__init__(self, "Unexpected closing bracket %s" % bracket)


class BracketMissingCloseError(BracketError):
    def __init__(self, bracket):
        self.bracket = bracket
        BracketError.__init__(self, "Missing closing bracket %s" % bracket)


class ParserPrefix:
    """
    Trivial container-class holding a single character for
    the possible prefixes for parse_quoted_separated_ext
    and implementing rich equal comparison.
    """
    def __init__(self, prefix):
        self.prefix = prefix

    def __eq__(self, other):
        return isinstance(other, ParserPrefix) and other.prefix == self.prefix

    def __repr__(self):
        return '<ParserPrefix(%s)>' % self.prefix.encode('utf-8')


def parse_quoted_separated_ext(args, separator=None, name_value_separator=None,
                               brackets=None, seplimit=0, multikey=False,
                               prefixes=None, quotes='"'):
    # TODO
    idx = 0
    assert name_value_separator is None or name_value_separator != separator
    assert name_value_separator is None or len(name_value_separator) == 1
    max = len(args)
    result = []         # result list
    cur = [None]        # current item
    quoted = None       # we're inside quotes, indicates quote character used
    skipquote = 0       # next quote is a quoted quote
    noquote = False     # no quotes expected because word didn't start with one
    seplimit_reached = False # number of separators exhausted
    separator_count = 0 # number of separators encountered
    SPACE = [' ', '\t', ]
    nextitemsep = [separator]   # used for skipping trailing space
    SPACE = [' ', '\t', ]
    if separator is None:
        nextitemsep = SPACE[:]
        separators = SPACE
    else:
        nextitemsep = [separator]   # used for skipping trailing space
        separators = [separator]
    if name_value_separator:
        nextitemsep.append(name_value_separator)

    # bracketing support
    opening = []
    closing = []
    bracketstack = []
    matchingbracket = {}
    if brackets:
        for o, c in brackets:
            assert not o in opening
            opening.append(o)
            assert not c in closing
            closing.append(c)
            matchingbracket[o] = c

    def additem(result, cur, separator_count, nextitemsep):
        if len(cur) == 1:
            result.extend(cur)
        elif cur:
            result.append(tuple(cur))
        cur = [None]
        noquote = False
        separator_count += 1
        seplimit_reached = False
        if seplimit and separator_count >= seplimit:
            seplimit_reached = True
            nextitemsep = [n for n in nextitemsep if n in separators]

        return cur, noquote, separator_count, seplimit_reached, nextitemsep

    while idx < max:
        char = args[idx]
        next = None
        if idx + 1 < max:
            next = args[idx+1]
        if skipquote:
            skipquote -= 1
        if not separator is None and not quoted and char in SPACE:
            spaces = ''
            # accumulate all space
            while char in SPACE and idx < max - 1:
                spaces += char
                idx += 1
                char = args[idx]
            # remove space if args end with it
            if char in SPACE and idx == max - 1:
                break
            # remove space at end of argument
            if char in nextitemsep:
                continue
            idx -= 1
            if len(cur) and cur[-1]:
                cur[-1] = cur[-1] + spaces
        elif not quoted and char == name_value_separator:
            if multikey or len(cur) == 1:
                cur.append(None)
            else:
                if not multikey:
                    if cur[-1] is None:
                        cur[-1] = ''
                    cur[-1] += name_value_separator
                else:
                    cur.append(None)
            noquote = False
        elif not quoted and not seplimit_reached and char in separators:
            (cur, noquote, separator_count, seplimit_reached,
             nextitemsep) = additem(result, cur, separator_count, nextitemsep)
        elif not quoted and not noquote and char in quotes:
            if len(cur) and cur[-1] is None:
                del cur[-1]
            cur.append('')
            quoted = char
        elif char == quoted and not skipquote:
            if next == quoted:
                skipquote = 2 # will be decremented right away
            else:
                quoted = None
        elif not quoted and char in opening:
            while len(cur) and cur[-1] is None:
                del cur[-1]
            (cur, noquote, separator_count, seplimit_reached,
             nextitemsep) = additem(result, cur, separator_count, nextitemsep)
            bracketstack.append((matchingbracket[char], result))
            result = [char]
        elif not quoted and char in closing:
            while len(cur) and cur[-1] is None:
                del cur[-1]
            (cur, noquote, separator_count, seplimit_reached,
             nextitemsep) = additem(result, cur, separator_count, nextitemsep)
            cur = []
            if not bracketstack:
                raise BracketUnexpectedCloseError(char)
            expected, oldresult = bracketstack[-1]
            if not expected == char:
                raise BracketUnexpectedCloseError(char)
            del bracketstack[-1]
            oldresult.append(result)
            result = oldresult
        elif not quoted and prefixes and char in prefixes and cur == [None]:
            cur = [ParserPrefix(char)]
            cur.append(None)
        else:
            if len(cur):
                if cur[-1] is None:
                    cur[-1] = char
                else:
                    cur[-1] += char
            else:
                cur.append(char)
            noquote = True

        idx += 1

    if bracketstack:
        raise BracketMissingCloseError(bracketstack[-1][0])

    if quoted:
        if len(cur):
            if cur[-1] is None:
                cur[-1] = quoted
            else:
                cur[-1] = quoted + cur[-1]
        else:
            cur.append(quoted)

    additem(result, cur, separator_count, nextitemsep)

    return result


def parse_quoted_separated(args, separator=',', name_value=True, seplimit=0):
    result = []
    positional = result
    if name_value:
        name_value_separator = '='
        trailing = []
        keywords = {}
    else:
        name_value_separator = None

    items = parse_quoted_separated_ext(args, separator=separator,
                                       name_value_separator=name_value_separator,
                                       seplimit=seplimit)
    for item in items:
        if isinstance(item, tuple):
            key, value = item
            if key is None:
                key = ''
            keywords[key] = value
            positional = trailing
        else:
            positional.append(item)

    if name_value:
        return result, keywords, trailing
    return result


def filename2mimetype(filename: str) -> Tuple[str, str, str]:
    moin_mimetype_mapping = {
        'application/docbook+xml': 'text/docbook',
        'application/x-latex': 'text/latex',
        'application/x-tex': 'text/tex',
        'application/javascript': 'text/javascript',
    }
    mtype, _encode = mimetypes.guess_type(filename)
    if mtype is None:
        mtype = 'application/octet-stream'
    tmp_mtype = moin_mimetype_mapping.get(mtype, mtype)
    assert tmp_mtype is not None
    majortype, subtype = tmp_mtype.split('/')
    return (mtype.lower(), majortype.lower(), subtype.lower())


def attachment_abs_name(url, pagename):
    url = abs_page(pagename, url)
    pieces = url.split('/')
    if len(pieces) == 1:
        return pagename, pieces[0]
    else:
        return "/".join(pieces[:-1]), pieces[-1]


def abs_page(base_page: str, target_page: str) -> str:
    pagename = target_page
    if target_page.startswith(PARENT_PREFIX):
        base_path_elems = base_page.split('/')
        while base_path_elems and target_page.startswith(PARENT_PREFIX):
            base_path_elems = base_path_elems[:-1]
            target_page = target_page[len(PARENT_PREFIX):]
        path_elems = base_path_elems + [target_page]
        pagename = '/'.join([elem for elem in path_elems if elem])
    elif target_page.startswith(CHILD_PREFIX):
        if base_page:
            pagename = base_page + '/' + target_page[len(CHILD_PREFIX):]
        else:
            pagename = target_page[len(CHILD_PREFIX):]
    return pagename


def url_unquote(s: str) -> str:
    try:
        # TODO: return urllib.parse.unquote(s, charset=config.charset, errors='strict')
        return urllib.parse.unquote(s, encoding='utf-8', errors='strict')
    except UnicodeDecodeError:
        return urllib.parse.unquote(s, encoding='iso-8859-1', errors='replace')


def unquoteWikiname(filename: str) -> str:
    QUOTED = re.compile(r'\(([a-fA-F0-9]+)\)')

    parts = []
    start = 0
    for needle in QUOTED.finditer(filename):
        # append leading unquoted stuff
        parts.append(filename[start:needle.start()])
        start = needle.end()
        # Append quoted stuff
        group = needle.group(1)
        try:
            parts.append(bytes.fromhex(group).decode('utf-8'))
        except ValueError:
            # byte not in hex, e.g 'xy'
            raise InvalidFileNameError(filename)

    # append rest of string
    if start == 0:
        wikiname = filename
    else:
        parts.append(filename[start:len(filename)])
        wikiname = ''.join(parts)

    return wikiname


def drawing2fname(drawing):
    # TODO
    raise NotImplementedError()


def parseAttributes(attrstring: str, endtoken=None, extension=None):
    parser = shlex.shlex(StringIO(attrstring))
    parser.commenters = ''
    attrs = {}

    try:
        while True:
            key = parser.get_token()
            if not key:
                break
            if endtoken and key == endtoken:
                break

            # call extension function with the current token, the parser, and the dict
            if extension:
                tmp_attrs = extension(key, parser)
                if tmp_attrs:
                    attrs.update(tmp_attrs)
                    continue

            eq = parser.get_token()
            if eq != "=":
                raise ValueError('Expected "=" to follow "%(token)s"' % {'token': key})

            val = parser.get_token()
            if not val:
                raise ValueError('Expected a value for key "%(token)s"' % {'token': key})

            key = html.escape(key, quote=False)  # make sure nobody cheats

            # safely escape and quote value
            if val[0] in ["'", '"']:
                val = html.escape(val, quote=False)
            else:
                val = '"%s"' % html.escape(val)

            attrs[key.lower()] = val
    except ValueError as e:
        logger.info("failed to parse attributes: %s by %s" % (attrstring, repr(e)))

    return attrs
