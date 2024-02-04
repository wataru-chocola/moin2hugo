import unicodedata
import urllib.parse
from abc import ABCMeta, abstractmethod
from typing import Optional

from moin2x.moinutils import (
    CHILD_PREFIX,
    is_relative_pagename_to_curdir,
    is_relative_pagename_to_parent,
)
from moin2x.utils import safe_path_join


class PathBuilder(metaclass=ABCMeta):
    @abstractmethod
    def _sanitize_pagename(self, pagename: str) -> str:
        pass

    @abstractmethod
    def _sanitize_attachment_filename(self, filename: str) -> str:
        pass

    @abstractmethod
    def _sanitize_path(self, path: str) -> str:
        pass

    @abstractmethod
    def page_filepath(self, pagename: str) -> str:
        pass

    @abstractmethod
    def attachment_filepath(self, pagename: str, filename: str) -> str:
        pass

    @abstractmethod
    def page_url(self, pagename: str, relative_base: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def attachment_url(
        self, pagename: Optional[str], filename: str, relative_base: Optional[str] = None
    ) -> str:
        pass


class MarkdownPathBuilder(PathBuilder):
    def __init__(
        self,
        page_front_page: str = "FrontPage",
        root_path: str = "/",
        disable_path_to_lower: bool = True,
        remove_path_accents: bool = False,
    ):
        self.page_front_page = page_front_page
        self.root_path = root_path
        self.disable_path_to_lower = disable_path_to_lower
        self.remove_path_accents = remove_path_accents

    def _remove_accents(self, s: str):
        # noqa refer: https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
        return "".join(
            c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
        )

    def _sanitize_pagename(self, pagename: str) -> str:
        if self.remove_path_accents:
            pagename = self._remove_accents(pagename)

        pagename = pagename.replace(":", "-")
        return pagename

    def _sanitize_attachment_filename(self, filename: str) -> str:
        if self.remove_path_accents:
            filename = self._remove_accents(filename)

        filename = filename.replace(":", "-")
        return filename

    def _sanitize_path(self, path: str) -> str:
        return path

    def _page_dirpath(self, pagename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        return self._sanitize_path(pagename)

    def page_filepath(self, pagename: str) -> str:
        pagename = self._sanitize_pagename(pagename)
        return safe_path_join(self._page_dirpath(pagename), "index.md")

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        pagename = self._sanitize_pagename(pagename)
        attachfile_name = self._sanitize_attachment_filename(filename)
        pagedir = self._page_dirpath(pagename)
        filepath = safe_path_join(pagedir, attachfile_name)
        return filepath

    def page_url(self, pagename: str, relative_base: Optional[str] = None) -> str:
        pagename = self._sanitize_pagename(pagename)
        if is_relative_pagename_to_parent(pagename):
            url = pagename
        elif is_relative_pagename_to_curdir(pagename):
            url = f"./{pagename.removeprefix(CHILD_PREFIX)}"
        else:
            url = urllib.parse.urljoin(self.root_path + "/", pagename)

        if not self.disable_path_to_lower:
            url = url.lower()
        url = self._sanitize_path(url)
        return url

    def attachment_url(
        self, pagename: Optional[str], filename: str, relative_base: Optional[str] = None
    ) -> str:
        filename = self._sanitize_attachment_filename(filename)
        if pagename is not None:
            pagename = self._sanitize_pagename(pagename)
            url = self.page_url(pagename, relative_base=relative_base)
            attachment_url = urllib.parse.urljoin(url + "/", filename)
        else:
            attachment_url = f"./{filename}"

        if not self.disable_path_to_lower:
            attachment_url = attachment_url.lower()
        attachment_url = self._sanitize_path(attachment_url)
        return attachment_url
