import logging
import mimetypes
import re
import shlex
import urllib.parse
from io import StringIO
from typing import Any, Callable, Optional, Tuple, Union

import attr

logger = logging.getLogger(__name__)

PARENT_PREFIX = "../"
CHILD_PREFIX = "/"


class InvalidFileNameError(Exception):
    pass


def split_anchor(pagename: str) -> Tuple[str, str]:
    parts = pagename.rsplit("#", 1)
    if len(parts) == 2:
        pagename, anchor = parts
        return (pagename, anchor)
    return (pagename, "")


def filename2mimetype(filename: str) -> Tuple[str, str, str]:
    moin_mimetype_mapping = {
        "application/docbook+xml": "text/docbook",
        "application/x-latex": "text/latex",
        "application/x-tex": "text/tex",
        "application/javascript": "text/javascript",
    }
    mtype, _encode = mimetypes.guess_type(filename)
    if mtype is None:
        mtype = "application/octet-stream"
    tmp_mtype = moin_mimetype_mapping.get(mtype, mtype)
    assert tmp_mtype is not None
    majortype, subtype = tmp_mtype.split("/")
    return (mtype.lower(), majortype.lower(), subtype.lower())


def parse_attachment_name(attachment_name: str) -> Tuple[Optional[str], str]:
    seps = attachment_name.split("/")
    filename = seps.pop()
    target_pagename = None
    if len(seps) > 0:
        target_pagename = "/".join(seps)
    return (target_pagename, filename)


def attachment_abs_name(url: str, pagename: str):
    url = abs_page(pagename, url)
    pieces = url.split("/")
    if len(pieces) == 1:
        return pagename, pieces[0]
    else:
        return "/".join(pieces[:-1]), pieces[-1]


def is_relative_pagename_to_parent(pagename: str) -> bool:
    return pagename.startswith(PARENT_PREFIX)


def is_relative_pagename_to_curdir(pagename: str) -> bool:
    return pagename.startswith(CHILD_PREFIX)


def abs_page(base_page: str, target_page: str) -> str:
    pagename = target_page
    if is_relative_pagename_to_parent(target_page):
        base_path_elems = base_page.split("/")
        while base_path_elems and target_page.startswith(PARENT_PREFIX):
            base_path_elems = base_path_elems[:-1]
            target_page = target_page[len(PARENT_PREFIX) :]
        path_elems = base_path_elems + [target_page]
        pagename = "/".join([elem for elem in path_elems if elem])
    elif is_relative_pagename_to_curdir(target_page):
        if base_page:
            pagename = base_page + "/" + target_page[len(CHILD_PREFIX) :]
        else:
            pagename = target_page[len(CHILD_PREFIX) :]
    return pagename


def url_unquote(s: str) -> str:
    try:
        return urllib.parse.unquote(s, encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return urllib.parse.unquote(s, encoding="iso-8859-1", errors="replace")


def unquoteWikiname(filename: str) -> str:
    QUOTED = re.compile(r"\(([a-fA-F0-9]+)\)")

    parts: list[str] = []
    start = 0
    for needle in QUOTED.finditer(filename):
        parts.append(filename[start : needle.start()])
        start = needle.end()
        group = needle.group(1)
        try:
            parts.append(bytes.fromhex(group).decode("utf-8"))
        except ValueError:
            raise InvalidFileNameError(filename)

    # append rest of string
    parts.append(filename[start : len(filename)])
    wikiname = "".join(parts)

    return wikiname


def resolve_interwiki(wikiname: str, pagename: str) -> bool:
    """Not implemented."""
    return False


#
# Argument or Attribute parsers
#
@attr.s
class MoinKV(object):
    k: str = ""
    v: str = ""
    is_value_started = False

    @property
    def cur(self):
        if self.is_value_started:
            return self.v
        else:
            return self.k

    @cur.setter
    def cur(self, s: str):
        if self.is_value_started:
            self.v = s
        else:
            self.k = s

    def start_value(self):
        self.is_value_started = True


def parse_quoted_separated_ext(
    argstring: str, separator: str = ",", quotes: str = '"'
) -> list[Union[Tuple[str, str], str]]:
    name_value_separator = "="
    SPACE = [
        " ",
        "\t",
    ]

    len_argstring = len(argstring)
    result: list[str | Tuple[str, str]] = []  # result list
    cur = MoinKV()
    quoted = None  # we're inside quotes, indicates quote character used
    noquote = False  # no quotes expected because word didn't start with one
    nextitemsep = [separator, name_value_separator]
    separators = [separator]

    def add_cur_item():
        nonlocal result, cur, noquote
        if cur.is_value_started:
            result.append((cur.k, cur.v))
        else:
            result.append(cur.k)
        cur = MoinKV()
        noquote = False

    idx = 0
    while idx < len_argstring:
        cur_char = argstring[idx]

        if not quoted and cur_char in SPACE:
            spaces = ""
            while idx < len_argstring - 1:
                spaces += cur_char
                idx += 1
                cur_char = argstring[idx]
                if cur_char not in SPACE:
                    break
            else:
                break  # end of argstring
            if cur_char in nextitemsep:
                continue
            if cur.cur:
                cur.cur += spaces
            continue

        elif not quoted and cur_char == name_value_separator:
            if not cur.is_value_started:
                cur.start_value()
            else:
                cur.v += name_value_separator
            noquote = False

        elif not quoted and cur_char in separators:
            add_cur_item()

        elif not quoted and not noquote and cur_char in quotes:
            quoted = cur_char

        elif cur_char == quoted:
            if idx + 1 < len_argstring and argstring[idx + 1] == quoted:
                # quoted quote (e.g. "")
                cur.cur += argstring[idx + 1]
                idx += 1
                noquote = True
            else:
                quoted = None
        else:
            cur.cur += cur_char
            noquote = True
        idx += 1

    if quoted:
        cur.cur = quoted + cur.cur

    add_cur_item()
    return result


def parse_quoted_separated(argstring: str) -> Tuple[list[str], dict[str, str], list[str]]:
    leading: list[str] = []
    positional = leading
    trailing: list[str] = []
    keywords: dict[str, str] = {}

    items = parse_quoted_separated_ext(argstring)
    for item in items:
        if isinstance(item, tuple):
            key, value = item
            keywords[key] = value
            positional = trailing
        else:
            positional.append(item)
    return leading, keywords, trailing


def parseAttributes(
    attrstring: str,
    endtoken: Optional[str] = None,
    extension: Optional[Callable[[str, shlex.shlex], dict[str, Any]]] = None,
) -> dict[str, str]:
    parser = shlex.shlex(StringIO(attrstring))
    parser.commenters = ""
    attrs: dict[str, Any] = {}

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
                raise ValueError('Expected "=" to follow "%(token)s"' % {"token": key})

            val = parser.get_token()
            if not val:
                raise ValueError('Expected a value for key "%(token)s"' % {"token": key})

            val = shlex.split(val)[0]  # unquote shell quotation
            attrs[key.lower()] = val
    except ValueError as e:
        logger.warning("failed to parse attributes: %s by %s" % (attrstring, repr(e)))

    return attrs
