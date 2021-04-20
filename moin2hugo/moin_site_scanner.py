import os
import logging

from datetime import datetime
from typing import Iterator, List, Optional

import attr

from moin2hugo.moinutils import unquoteWikiname

logger = logging.getLogger(__name__)


@attr.s(frozen=True)
class MoinAttachment:
    filepath: str = attr.ib()
    name: str = attr.ib()


@attr.s(frozen=True)
class MoinPageInfo:
    filepath: str = attr.ib()
    name: str = attr.ib()
    attachments: List[MoinAttachment] = attr.ib()
    updated: Optional[datetime] = attr.ib(default=None)


class MoinSiteScanner(object):
    def __init__(self, page_dir: str):
        self.page_dir = page_dir

    def _scan_page(self, entryname: str, page_dir: str) -> Optional[MoinPageInfo]:
        ignorable_pages = ['BadContent', 'SideBar']

        pagename = unquoteWikiname(entryname)
        if pagename in ignorable_pages:
            return None

        pagedir = os.path.join(page_dir, entryname)
        current_file = os.path.join(pagedir, 'current')
        try:
            with open(current_file, 'r') as f:
                current_revision = f.read().rstrip()
        except FileNotFoundError:
            logger.debug("++ not content page")
            return None

        edit_log = os.path.join(pagedir, 'edit-log')
        with open(edit_log, 'r') as f:
            edit_log_content = f.read()
        if not edit_log_content:
            logger.debug("++ skip built-in page having no edit history")
            return None
        last_edit_log = edit_log_content.splitlines()[-1]
        updated_us = int(last_edit_log.split()[0])
        updated = datetime.fromtimestamp(updated_us / 1000 ** 2)

        content_file = os.path.join(pagedir, 'revisions', current_revision)
        if not os.path.isfile(content_file):
            logger.debug("++ not found: %s/revisions/%s" % (entryname, current_revision))
            logger.debug("++ already deleted")
            return None

        attachments: List[MoinAttachment] = []
        attachments_dir = os.path.join(pagedir, 'attachments')
        if os.path.isdir(attachments_dir):
            for attachment_entry in os.scandir(attachments_dir):
                if attachment_entry.name.startswith("."):
                    return None
                attachment_file = os.path.join(attachments_dir, attachment_entry.name)
                attachment = MoinAttachment(filepath=attachment_file,
                                            name=attachment_entry.name)
                attachments.append(attachment)

        page = MoinPageInfo(filepath=content_file, name=pagename,
                            updated=updated, attachments=attachments)
        return page

    def scan_pages(self) -> Iterator[MoinPageInfo]:
        for entry in os.scandir(self.page_dir):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue

            logger.debug("+ Page Found: %s" % unquoteWikiname(entry.name))
            page = self._scan_page(entry.name, self.page_dir)
            if page is not None:
                yield page
