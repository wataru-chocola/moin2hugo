from .base import ParserExtensionAbstract
from moin2hugo.page_tree import Codeblock

from typing import Optional


class ParserHighlight(ParserExtensionAbstract):
    @classmethod
    def parse(cls, text: str, parser_name: str, parser_arg_string: Optional[str]) -> Codeblock:
        old_parser_mapping = {
            'cplusplus': 'cpp',
            'diff': 'diff',
            'python': 'python',
            'java': 'java',
            'pascal': 'pascal',
            'irssi': 'irc'
        }
        syntax_id: Optional[str]
        if parser_name in old_parser_mapping:
            syntax_id = old_parser_mapping[parser_name]
        else:
            syntax_id = parser_arg_string
        return Codeblock(content=text, syntax_id=syntax_id)
