import re
from typing import List

PARENT_PREFIX = "../"
CHILD_PREFIX = "/"


class InvalidFileNameError(Exception):
    pass


def split_anchor(pagename: str) -> List[str]:
    parts = pagename.rsplit('#', 1)
    if len(parts) == 2:
        return parts
    else:
        return [pagename, ""]


def resolve_wiki(request, wikiurl):
    # TODO
    raise NotImplementedError()


def resolve_interwiki(request, wikiname, pagename):
    # TODO
    raise NotImplementedError()


def join_wiki(wikiurl, wikitail):
    # TODO
    raise NotImplementedError()


def parse_quoted_separated(args, separator=',', name_value=True, seplimit=0):
    # TODO
    raise NotImplementedError()


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
