import urllib.parse
from typing import Optional

from moin2x.path_builder import MarkdownPathBuilder
from moin2x.utils import safe_path_join


class KibunPathBuilder(MarkdownPathBuilder):
    SOURCE_FILE = "_index.md"
    ATTACHMENTS_DIR = "_files"

    def _sanitize_path(self, path: str) -> str:
        # remove leading and trailing spaces
        path = path.lstrip().rstrip()
        # remove leading special characters (., _)
        path = path.lstrip("._")

        path = super()._sanitize_path(path)
        return path

    def page_filepath(self, pagename: str) -> str:
        return safe_path_join(self._page_dirpath(pagename), self.SOURCE_FILE)

    def attachment_filepath(self, pagename: str, filename: str) -> str:
        if pagename == self.page_front_page:
            pagename = ""
        attachfile_name = self._sanitize_path(filename)
        pagedir = self._page_dirpath(pagename)
        filedir = safe_path_join(pagedir, self.ATTACHMENTS_DIR)
        filepath = safe_path_join(filedir, attachfile_name)
        return filepath

    def attachment_url(
        self, pagename: str, filename: str, relative_base: Optional[str] = None
    ) -> str:
        url = self.page_url(pagename, relative_base=relative_base)
        if url:
            url = urllib.parse.urljoin(url + "/", f"_files/{filename}")
        else:
            url = filename
        if not self.disable_path_to_lower:
            url = url.lower()
        url = self._sanitize_path(url)
        return url
