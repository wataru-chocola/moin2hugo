import urllib.parse
from typing import Optional

from moin2x.path_builder import MarkdownPathBuilder
from moin2x.utils import safe_path_join


class KibunPathBuilder(MarkdownPathBuilder):
    SOURCE_FILE = "_index.md"
    ATTACHMENTS_DIR = "_files"

    def _sanitize_path_segment(self, path: str) -> str:
        # remove leading and trailing spaces
        path = path.lstrip().rstrip()
        # remove leading special characters (., _)
        path = path.lstrip("._")

        path = super()._sanitize_path(path)
        return path

    def _sanitize_pagename(self, pagename: str) -> str:
        pagename = super()._sanitize_pagename(pagename)
        pagename_segments = pagename.split("/")
        new_pagename_segments: list[str] = []
        for segment in pagename_segments:
            if segment == "" or segment == "..":
                new_pagename_segments.append(segment)
                continue
            new_pagename_segments.append(self._sanitize_path_segment(segment))
        return "/".join(new_pagename_segments)

    def _sanitize_attachment_filename(self, filename: str) -> str:
        filename = super()._sanitize_attachment_filename(filename)
        return self._sanitize_path_segment(filename)

    def page_filepath(self, pagename: str) -> str:
        pagename = self._sanitize_pagename(pagename)
        return safe_path_join(self._page_dirpath(pagename), self.SOURCE_FILE)

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        pagename = self._sanitize_pagename(pagename)
        filename = self._sanitize_attachment_filename(filename)
        if pagename == self.page_front_page:
            pagename = ""
        attachfile_name = self._sanitize_path(filename)
        pagedir = self._page_dirpath(pagename)
        filedir = safe_path_join(pagedir, self.ATTACHMENTS_DIR)
        filepath = safe_path_join(filedir, attachfile_name)
        return filepath

    def attachment_url(
        self, pagename: Optional[str], filename: str, relative_base: Optional[str] = None
    ) -> str:
        filename = self._sanitize_attachment_filename(filename)
        if pagename is not None:
            pagename = self._sanitize_pagename(pagename)
            url = self.page_url(pagename, relative_base=relative_base)
            if url:
                url = urllib.parse.urljoin(url + "/", f"_files/{filename}")
            else:
                url = f"./_files/{filename}"
        else:
            url = f"./_files/{filename}"
        if not self.disable_path_to_lower:
            url = url.lower()
        url = self._sanitize_path(url)
        return url
