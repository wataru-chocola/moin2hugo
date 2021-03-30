from moin2hugo.page_tree import PageElement
from .csv import ParserCSV
from .highlight import ParserHighlight

from typing import Dict, Callable, Optional

CALLABLE_PARSE = Callable[[str, str, Optional[str]], PageElement]


parser_extensions: Dict[str, CALLABLE_PARSE] = {
    'highlight': ParserHighlight.parse,
    'text': ParserHighlight.parse,
    '': ParserHighlight.parse,

    'cplusplus': ParserHighlight.parse,
    'diff': ParserHighlight.parse,
    'python': ParserHighlight.parse,
    'java': ParserHighlight.parse,
    'pascal': ParserHighlight.parse,
    'irssi': ParserHighlight.parse,

    'csv': ParserCSV.parse,
}

parser_extension_fallback: CALLABLE_PARSE = ParserHighlight.parse
