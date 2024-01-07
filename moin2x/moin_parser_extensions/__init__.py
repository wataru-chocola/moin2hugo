from typing import Optional, Tuple, Type

from .base import ParserExtensionAbstract
from .csv import ParserCSV
from .highlight import ParserHighlight

_parser_extensions: dict[str, Type[ParserExtensionAbstract]] = {}
_ext_to_parser: dict[str, Type[ParserExtensionAbstract]] = {}
_parser_extension_fallback: Type[ParserExtensionAbstract] = ParserHighlight


def get_parser(parser_name: str) -> Optional[Type[ParserExtensionAbstract]]:
    global _parser_extensions
    return _parser_extensions.get(parser_name)


def get_fallback_parser() -> Type[ParserExtensionAbstract]:
    return _parser_extension_fallback


def get_parser_info_from_ext(ext: str) -> Tuple[Optional[str], Optional[str]]:
    global _ext_to_parser
    ext = ext.lower()
    name = None
    args = None
    parser = _ext_to_parser.get(ext)
    if parser:
        name = parser.name
        args = parser.ext_to_args(ext)
    return name, args


def register_parser(parser: Type[ParserExtensionAbstract]):
    global _parser_extensions, _ext_to_parser

    if parser.name in _parser_extensions:
        raise AssertionError("parser name='%s' is already registered" % parser.name)
    _parser_extensions[parser.name] = parser

    for alias_name in parser.aliases:
        if alias_name in _parser_extensions:
            raise AssertionError("parser alias='%s' is already registered" % alias_name)
        _parser_extensions[alias_name] = parser

    for ext in parser.extensions:
        _ext_to_parser[ext] = parser


register_parser(ParserHighlight)
register_parser(ParserCSV)
