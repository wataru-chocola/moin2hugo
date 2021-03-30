from abc import ABCMeta, abstractmethod

from moin2hugo.page_tree import PageElement
from typing import List, Optional


class ParserExtensionAbstract(metaclass=ABCMeta):
    name: str = ""
    aliases: List[str] = []
    extensions: List[str] = []

    @classmethod
    @abstractmethod
    def parse(cls, text: str, parser_name: str, parser_arg_string: Optional[str]) -> PageElement:
        pass

    @classmethod
    def ext_to_args(cls, ext: str) -> Optional[str]:
        return None
