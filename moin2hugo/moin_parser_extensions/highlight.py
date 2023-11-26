from typing import List, Optional

import pygments.lexers  # type: ignore

from moin2hugo.page_tree import Codeblock

from .base import ParserExtensionAbstract

_ext_to_syntax_id: dict[str, str] = {}


def build_ext_to_syntax_id_mapping():
    global _ext_to_syntax_id
    for _name, aliases, patterns, _mime in pygments.lexers.get_all_lexers():
        for ptn in patterns:
            if ptn.startswith("*."):
                ext = ptn[1:]
                _ext_to_syntax_id[ext] = aliases[0]


def extensions_from_all_lexers() -> List[str]:
    global _ext_to_syntax_id
    if not _ext_to_syntax_id:
        build_ext_to_syntax_id_mapping()
    return list(_ext_to_syntax_id.keys())


class ParserHighlight(ParserExtensionAbstract):
    name: str = "highlight"
    aliases: List[str] = ["text", "cplusplus", "diff", "python", "java", "pascal", "irssi"]
    extensions: List[str] = extensions_from_all_lexers()

    @classmethod
    def parse(cls, text: str, parser_name: str, parser_arg_string: Optional[str]) -> Codeblock:
        old_parser_mapping = {
            "cplusplus": "cpp",
            "diff": "diff",
            "python": "python",
            "java": "java",
            "pascal": "pascal",
            "irssi": "irc",
        }
        syntax_id: Optional[str]
        if parser_name in old_parser_mapping:
            syntax_id = old_parser_mapping[parser_name]
        else:
            syntax_id = parser_arg_string
        return Codeblock(content=text, syntax_id=syntax_id)

    @classmethod
    def ext_to_args(cls, ext: str) -> Optional[str]:
        syntax_id = _ext_to_syntax_id.get(ext)
        return syntax_id
