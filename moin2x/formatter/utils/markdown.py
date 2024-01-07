import re
from typing import Literal, Set, Tuple

from moin2x.page_tree import PageElement, TableCell


class MarkdownEscapedText(str):
    pass


ESCAPABLE_CHAR = Literal[
    "\\", "[", "]", "{", "}", "(", ")", "<", ">", "*", "+", "-", "_", ":", "`", "#", "|", '"', "~"
]

ESCAPABLE_CHARS: Set[ESCAPABLE_CHAR] = set(
    [
        "\\",
        "[",
        "]",
        "{",
        "}",
        "(",
        ")",
        "<",
        ">",
        "*",
        "+",
        "-",
        "_",
        ":",
        "`",
        "#",
        "|",
        '"',
        "~",  # can be escaped at least with commonmark
    ]
)


def escape_markdown_symbols(text: str, symbols: list[ESCAPABLE_CHAR] = []) -> MarkdownEscapedText:
    """escape all occurences of these symbols no matter which context they are on."""
    symbol_re = re.compile("([%s])" % re.escape("".join(symbols)))
    text = re.sub(symbol_re, r"\\\1", text)
    return MarkdownEscapedText(text)


def escape_markdown_all(text: str) -> MarkdownEscapedText:
    """escape all occurences of these symbols no matter which context they are on."""
    return escape_markdown_symbols(text, symbols=list(ESCAPABLE_CHARS))


def escape_markdown_text(
    text: str, e: PageElement, *, at_beginning_of_line: bool
) -> MarkdownEscapedText:
    """escape markdown symbols which are necessary to be escaped on context."""
    # escape backslash at first
    text = escape_markdown_symbols(text, symbols=["\\"])

    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    first_line = True
    for line in lines:
        # remove trailing whitespaces which means line break in markdown
        line = re.sub(r"\s+(?=\n)", "", line)

        # escape '-' | '+' | '=' | '1.'
        if e.in_x([TableCell]):
            # escape `-` in table cell, which means header row in markdown
            line = re.sub(r"([-])", r"\\\1", line)
        elif (first_line and at_beginning_of_line) or not first_line:
            # remove leading whitespaces
            line = line.lstrip()
            # avoid unintended listitem
            line = re.sub(r"^(\d)\.(?=\s)", r"\1\.", line)  # numbered list
            line = re.sub(r"^([-+])(?=\s)", r"\\\1", line)  # bullet list
            # horizontal rule or headling
            m = re.match(r"^([-=])\1*$", line)
            if m:
                symbol = m.group(1)
                line = line.replace(symbol, "\\" + symbol)

        # escape "!"
        line = re.sub(r"\!(?=\[)", r"\!", line)  # image: ![title](image)
        # escape ":"
        line = re.sub(r":(\w+):", r"\:\1\:", line)  # emoji: :emoji:

        # escape other symbols
        line = escape_markdown_symbols(
            line, symbols=["[", "]", "{", "}", "*", "_", "`", "~", "<", ">", "|", "#"]
        )

        new_lines.append(line)
        first_line = False
    return MarkdownEscapedText("".join(new_lines))


def get_codeblock_delimiter(content: str) -> Tuple[str, str]:
    lines = content.splitlines()
    if lines and not lines[0]:
        lines = lines[1:]
    if lines and not lines[-1].strip():
        lines = lines[:-1]

    codeblock_delimiter = "```"
    for line in lines:
        m = re.search(r"^`{3,}", line)
        if m and len(m.group(0)) >= len(codeblock_delimiter):
            codeblock_delimiter = "`" * (len(m.group(0)) + 1)

    formatted_content = "\n".join(lines)
    return (codeblock_delimiter, formatted_content)


def _get_leading_space_of_asterisk_text(text: str, at_begenning_of_line: bool) -> Tuple[str, str]:
    if at_begenning_of_line:
        return ("", text)

    # text starts with unicode spaces
    if m_leading_unicode_spaces := re.search(r"^\s+", text):
        preceding_text = m_leading_unicode_spaces.group(0)
        text = re.sub(r"^\s+", "", text)
        return (preceding_text, text)

    # text starts with symbol except space or asterisk, like -, +, "
    if re.search(r"^[^\w\s*]", text):
        return (" ", text)

    return ("", text)


def _get_trailing_space_of_asterisk_text(text: str) -> Tuple[str, str]:
    # text ends with unicode spaces
    if m_trailing_unicode_spaces := re.search(r"\s+$", text):
        following_text = m_trailing_unicode_spaces.group(0)
        text = re.sub(r"\s+$", "", text)
        return (text, following_text)

    # text ends with symbol except space or escaped asterisk, like -, +, "
    if re.search(r"[^\w\s]$", text) and not re.search(r"(?<!\\)[*]$", text):
        return (text, " ")

    return (text, "")


def adjust_surrounding_space_of_asterisk_text(
    text: str, at_begenning_of_line: bool
) -> Tuple[str, str, str]:
    """adjust surrounding space of **strong** and *emphasis*."""
    preceding_text, text = _get_leading_space_of_asterisk_text(text, at_begenning_of_line)
    text, following_text = _get_trailing_space_of_asterisk_text(text)
    return (preceding_text, text, following_text)
