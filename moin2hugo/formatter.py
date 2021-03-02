import re

from typing import Optional


class Formatter(object):
    def __init__(self):
        self.in_p = False

    def paragraph(self, _open):
        return ''

    # Heading / Horizontal Rule
    def heading(self, depth: int, text: str, _id: Optional[str] = None) -> str:
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

    def text(self, text: str) -> str:
        # TODO: escape, etc
        return text
