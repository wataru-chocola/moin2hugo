import os

from dataclasses import dataclass
from typing import Iterator, List

from moin2hugo.moinutils import unquoteWikiname


@dataclass
class MoinAttachment:
    filepath: str
    name: str


@dataclass
class MoinPageInfo:
    filepath: str
    name: str
    attachments: List[MoinAttachment]


class Moin2Hugo(object):
    def __init__(self, src_dir: str, dst_dir: str):
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def scan_pages(self, page_dir: str) -> Iterator[MoinPageInfo]:
        for entry in os.scandir(page_dir):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue

            pagedir = os.path.join(page_dir, entry.name)
            try:
                current_file = os.path.join(pagedir, 'current')
                with open(current_file, 'r') as f:
                    current_revision = f.read().rstrip()
            except FileNotFoundError:
                continue

            content_file = os.path.join(pagedir, 'revisions', current_revision)
            if not os.path.isfile(content_file):
                # TODO: say something
                continue

            attachments: List[MoinAttachment] = []
            attachments_dir = os.path.join(pagedir, 'attachments')
            if os.path.isdir(attachments_dir):
                for attachment_entry in os.scandir(attachments_dir):
                    if attachment_entry.name.startswith("."):
                        continue
                    attachment_file = os.path.join(attachments_dir, attachment_entry.name)
                    attachment = MoinAttachment(filepath=attachment_file,
                                                name=attachment_entry.name)
                    attachments.append(attachment)

            page = MoinPageInfo(filepath=content_file, name=unquoteWikiname(entry.name),
                                attachments=attachments)
            yield page

    def convert(self):
        pass
