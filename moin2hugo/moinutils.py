import re
from typing import Tuple

PARENT_PREFIX = "../"
CHILD_PREFIX = "/"


class InvalidFileNameError(Exception):
    pass


def split_anchor(pagename: str) -> Tuple[str]:
    parts = pagename.rsplit('#', 1)
    if len(parts) == 2:
        return tuple(parts)
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

    l = parse_quoted_separated_ext(args, separator=separator,
                                   name_value_separator=name_value_separator,
                                   seplimit=seplimit)
    for item in l:
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


def makeQueryString(qstr=None, want_unicode=None, **kw):
    # TODO
    raise NotImplementedError()


class MimeType(object):
    # TODO
    def __init__(self, mimestr=None, filename=None):
        # TODO
        raise NotImplementedError()


def AbsPageName(context, pagename):
    # TODO
    """
    Return the absolute pagename for a (possibly) relative pagename.
    @param context: name of the page where "pagename" appears on
    @param pagename: the (possibly relative) page name
    @rtype: string
    @return: the absolute page name
    """
    if pagename.startswith(PARENT_PREFIX):
        while context and pagename.startswith(PARENT_PREFIX):
            context = '/'.join(context.split('/')[:-1])
            pagename = pagename[len(PARENT_PREFIX):]
        pagename = '/'.join(filter(None, [context, pagename, ]))
    elif pagename.startswith(CHILD_PREFIX):
        if context:
            pagename = context + '/' + pagename[len(CHILD_PREFIX):]
        else:
            pagename = pagename[len(CHILD_PREFIX):]
    return pagename


def url_unquote(s, want_unicode=None):
    # TODO
    raise NotImplementedError()


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


def parseAttributes(attrstring, endtoken=None, extension=None):
    # TODO
    """
    Parse a list of attributes and return a dict plus a possible
    error message.
    If extension is passed, it has to be a callable that returns
    a tuple (found_flag, msg). found_flag is whether it did find and process
    something, msg is '' when all was OK or any other string to return an error
    message.
    @param attrstring: string containing the attributes to be parsed
    @param endtoken: token terminating parsing
    @param extension: extension function -
                      gets called with the current token, the parser and the dict
    @rtype: dict, msg
    @return: a dict plus a possible error message
    """
    import shlex
    import StringIO

    parser = shlex.shlex(StringIO.StringIO(attrstring))
    parser.commenters = ''
    msg = None
    attrs = {}

    while not msg:
        try:
            key = parser.get_token()
        except ValueError as err:
            msg = str(err)
            break
        if not key:
            break
        if endtoken and key == endtoken:
            break

        # call extension function with the current token, the parser, and the dict
        if extension:
            found_flag, msg = extension(key, parser, attrs)
            if found_flag:
                continue
            elif msg:
                break

        try:
            eq = parser.get_token()
        except ValueError as err:
            msg = str(err)
            break
        if eq != "=":
            msg = _('Expected "=" to follow "%(token)s"') % {'token': key}
            break

        try:
            val = parser.get_token()
        except ValueError as err:
            msg = str(err)
            break
        if not val:
            msg = _('Expected a value for key "%(token)s"') % {'token': key}
            break

        key = escape(key)  # make sure nobody cheats

        # safely escape and quote value
        if val[0] in ["'", '"']:
            val = escape(val)
        else:
            val = '"%s"' % escape(val, 1)

        attrs[key.lower()] = val

    return attrs, msg or ''
