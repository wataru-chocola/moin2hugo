from abc import ABCMeta, abstractclassmethod

from moin2hugo.page_tree import PageElement
from typing import Optional


class ParserExtensionAbstract(metaclass=ABCMeta):
    @abstractclassmethod
    def parse(cls, text: str, parser_name: str, parser_arg_string: Optional[str]) -> PageElement:
        pass
