import re


class InvalidFileNameError(Exception):
    pass


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
