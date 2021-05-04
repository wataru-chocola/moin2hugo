import unicodedata
import urllib.parse
from typing import Optional

from moin2hugo.utils import safe_path_join


class HugoPathBuilder(object):
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
        # noqa refer: https://github.com/gohugoio/hugo/blob/ba1d0051b44fdd242b20899e195e37ab26501516/helpers/path.go#L134
        if self.remove_path_accents:
            path = self._remove_accents(path)

        sanitized_path = ""
        prepend_hyphen = False
        for i, c in enumerate(path):

            def is_allowed(r: str) -> bool:
                if r in "./\\_#+~":
                    return True
                code_category = unicodedata.category(r)
                if "L" in code_category or "N" in code_category or "M" in code_category:
                    # https://www.unicode.org/reports/tr44/#General_Category_Values
                    return True
                if r == "%" and len(path) > i + 2:
                    try:
                        int(path[i + 1 : i + 3], 8)
                        return True
                    except ValueError:
                        return False
                return False

            code_category = unicodedata.category(c)
            if is_allowed(c):
                if prepend_hyphen:
                    sanitized_path += "-"
                    prepend_hyphen = False
                sanitized_path += c
            elif len(sanitized_path) > 0 and (c == "-" or code_category == "Zs"):
                prepend_hyphen = True
        return sanitized_path

    def page_to_hugo_bundle_path(self, pagename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        return self._sanitize_path(pagename)

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        attachfile_hugo_name = self._sanitize_path(filename)
        hugo_bundle_path = self.page_to_hugo_bundle_path(pagename)
        filepath = safe_path_join(hugo_bundle_path, attachfile_hugo_name)
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
