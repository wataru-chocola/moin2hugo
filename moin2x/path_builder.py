import unicodedata
import urllib.parse
from abc import ABCMeta, abstractmethod
from typing import Optional

from moin2x.utils import safe_path_join


class PathBuilder(metaclass=ABCMeta):
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
        self, pagename: str, filename: str, relative_base: Optional[str] = None
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

    def _sanitize_path(self, path: str) -> str:
        if self.remove_path_accents:
            path = self._remove_accents(path)
        return path

    def _page_dirpath(self, pagename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        return self._sanitize_path(pagename)

    def page_filepath(self, pagename: str) -> str:
        return safe_path_join(self._page_dirpath(pagename), "index.md")

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        attachfile_name = self._sanitize_path(filename)
        pagedir = self._page_dirpath(pagename)
        filepath = safe_path_join(pagedir, attachfile_name)
        return filepath

    def page_url(self, pagename: str, relative_base: Optional[str] = None) -> str:
        url = urllib.parse.urljoin(self.root_path + "/", pagename)
        if relative_base:
            target_path_elems = pagename.split("/")
            relative_base_elems = relative_base.split("/")
            if len(target_path_elems) >= len(relative_base_elems):
                for elem in relative_base_elems:
                    if target_path_elems[0] != elem:
                        break
                    target_path_elems.pop(0)
                else:
                    url = "/".join(target_path_elems)

        if not self.disable_path_to_lower:
            url = url.lower()
        url = self._sanitize_path(url)
        return url

    def attachment_url(
        self, pagename: str, filename: str, relative_base: Optional[str] = None
    ) -> str:
        url = self.page_url(pagename, relative_base=relative_base)
        if url:
            url = urllib.parse.urljoin(url + "/", filename)
        else:
            url = filename
        if not self.disable_path_to_lower:
            url = url.lower()
        url = self._sanitize_path(url)
        return url
