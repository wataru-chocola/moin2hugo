import unicodedata
import urllib.parse
from typing import Optional

from moin2x.moinutils import (
    CHILD_PREFIX,
    is_relative_pagename_to_curdir,
    is_relative_pagename_to_parent,
)
from moin2x.path_builder import MarkdownPathBuilder
from moin2x.utils import safe_path_join


def pagename_abs2rel(pagename: str, base: str) -> Optional[str]:
    target_path_elems = pagename.split("/")
    base_elems = base.split("/")
    if len(target_path_elems) >= len(base_elems):
        for elem in base_elems:
            if target_path_elems[0] != elem:
                break
            target_path_elems.pop(0)
        else:
            rel_pagename = "/".join(target_path_elems)
            return rel_pagename


class HugoPathBuilder(MarkdownPathBuilder):
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

    def _sanitize_pagename(self, pagename: str) -> str:
        if self.remove_path_accents:
            pagename = self._remove_accents(pagename)
        return pagename

    def _sanitize_attachment_filename(self, filename: str) -> str:
        if self.remove_path_accents:
            filename = self._remove_accents(filename)
        return filename

    def _sanitize_path(self, path: str) -> str:
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
            elif len(sanitized_path) > 0 and (c in ["-", ":"] or code_category == "Zs"):
                prepend_hyphen = True
        return sanitized_path

    def page_filepath(self, pagename: str) -> str:
        pagename = self._sanitize_pagename(pagename)
        if pagename == self.page_front_page:
            pagename = ""
        return self._sanitize_path(pagename)

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        pagename = self._sanitize_pagename(pagename)
        filename = self._sanitize_attachment_filename(filename)
        if pagename == self.page_front_page:
            pagename = ""
        attachfile_hugo_name = self._sanitize_path(filename)
        hugo_bundle_path = self.page_filepath(pagename)
        filepath = safe_path_join(hugo_bundle_path, attachfile_hugo_name)
        return filepath

    def page_url(self, pagename: str, relative_base: Optional[str] = None) -> str:
        pagename = self._sanitize_pagename(pagename)
        if is_relative_pagename_to_parent(pagename):
            url = pagename
        elif is_relative_pagename_to_curdir(pagename):
            url = f"{pagename.removeprefix(CHILD_PREFIX)}"
        else:
            rel_pagename = None
            if relative_base is not None:
                rel_pagename = pagename_abs2rel(pagename, relative_base)

            if rel_pagename is None or rel_pagename == "":
                url = urllib.parse.urljoin(self.root_path + "/", pagename)
            else:
                url = rel_pagename

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
            page_url = self.page_url(pagename, relative_base=relative_base)
            cur_url = urllib.parse.urljoin(self.root_path + "/", relative_base)
            if page_url == "" or page_url == cur_url:
                attachment_url = filename
            else:
                attachment_url = urllib.parse.urljoin(page_url + "/", filename)
        else:
            attachment_url = filename

        if not self.disable_path_to_lower:
            attachment_url = attachment_url.lower()
        attachment_url = self._sanitize_path(attachment_url)
        return attachment_url
