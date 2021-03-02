import re

from typing import Optional, Dict


class Formatter(object):
    def __init__(self):
        self.in_p = False

    def paragraph(self, _open):
        return ''

    # Heading / Horizontal Rule
    def heading(self, depth: int, text: str) -> str:
        # TODO: support _id ?
        assert depth >= 1 and depth <= 6
        return '#' * depth + ' ' + text + "\n\n"

    def rule(self) -> str:
        return '-' * 4 + "\n\n"

    # Decoration (can be multilined)
    def underline(self, on: bool) -> str:
        return "__"

    def strike(self, on: bool) -> str:
        return "~~"

    def small(self, on: bool) -> str:
        # TODO: unsafe option?
        if on:
            return "<small>"
        else:
            return "</small>"

    def big(self, on: bool) -> str:
        # TODO: unsafe option?
        if on:
            return "<big>"
        else:
            return "</big>"

    def strong(self, on: bool) -> str:
        # TODO: want to handle _ or *, but how?
        return "**"

    def emphasis(self, on: bool) -> str:
        # TODO: want to handle _ or *, but how?
        return "*"

    # Decoration (cannot be multilined)
    def sup(self, text: str) -> str:
        # TODO: unsafe option?
        return "<sup>%s</sup>" % text

    def sub(self, text: str) -> str:
        # TODO: unsafe option?
        return "<sub>%s</sub>" % text

    def code(self, text: str) -> str:
        # noqa: refer: https://meta.stackexchange.com/questions/82718/how-do-i-escape-a-backtick-within-in-line-code-in-markdown
        if text.startswith("`"):
            text = " " + text
        if text.endswith("`"):
            text = text + " "

        len_of_longest_backticks = 0
        if "`" in text:
            len_of_longest_backticks = max([len(s) for s in re.findall(r"`+", text)])
        delimiter = "`" * (len_of_longest_backticks + 1)
        return "%s%s%s" % (delimiter, text, delimiter)

    # Links
    def url(self, target: str) -> str:
        return "<%s>" % (target)

    def link(self, target: str, description: str, title: Optional[str] = None) -> str:
        if title is not None:
            return '[%s](%s "%s")' % (description, target, title)
        else:
            return "[%s](%s)" % (description, target)

    def pagelink(self, page_name: str, description: str,
                 queryargs: Optional[Dict[str, str]] = None, anchor: Optional[str] = None) -> str:
        # TODO: convert page_name to link path
        link_path = page_name
        if queryargs:
            # TODO: maybe useless
            pass
        if anchor:
            link_path += "#%s" % anchor
        return self.link(link_path, description)

    def attachment_link(self, attach_name: str, description: str, title: Optional[str] = None,
                        queryargs: Optional[Dict[str, str]] = None) -> str:
        # TODO: convert attach_name to link path
        link_path = attach_name
        if queryargs:
            # TODO: maybe useless
            pass
        return self.link(link_path, description, title)

    # Itemlist
    def bullet_list(self):
        # TODO
        return "dummy"

    def number_list(self):
        # TODO
        return "dummy"

    def definition_list(self):
        # TODO
        return "dummy"

    def listitem(self, css_class, style):
        # TODO
        return "dummy"

    # Image Embedding
    def image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"

    def attachment_image(self, src: str, alt: str, title: str) -> str:
        # TODO
        return "dummy"

    def text(self, text: str) -> str:
        # TODO: escape markdown special characters, etc
        return text

    def raw(self, text: str) -> str:
        return text
