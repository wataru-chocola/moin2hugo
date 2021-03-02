from typing import Optional


class Formatter(object):
    def __init__(self):
        self.in_p = False

    def paragraph(self, _open):
        return ''

    def heading(self, depth: int, text: str, _id: Optional[str] = None) -> str:
        # TODO: support _id ?
        assert depth >= 1 and depth <= 6
        return '#' * depth + ' ' + text + "\n\n"

    # Decoration
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

    def text(self, text: str) -> str:
        return text
