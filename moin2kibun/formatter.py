import logging
from typing import List, Optional

import attr

from moin2kibun.path_builder import KibunPathBuilder
from moin2x.formatter.markdown import MarkdownFormatter, MarkdownFormatterConfig

logger = logging.getLogger(__name__)


@attr.define
class TableProperty:
    num_of_columns: int = attr.ib(default=0)
    has_extended_attributes: bool = attr.ib(default=False)
    col_alignments: List[str] = attr.field(factory=list)


class KibunFormatter(MarkdownFormatter):
    def __init__(
        self,
        *,
        config: Optional[MarkdownFormatterConfig] = None,
        pagename: Optional[str] = None,
        path_builder: Optional[KibunPathBuilder] = None,
    ):
        self._formatted: dict[int, str] = {}

        self.pagename = pagename
        self.config = config if config is not None else MarkdownFormatterConfig()

        if path_builder:
            self.path_builder = path_builder
        else:
            self.path_builder = KibunPathBuilder()
