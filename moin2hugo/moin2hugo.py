import os
import logging
import shutil
from datetime import datetime
from typing import Iterator, List, Optional

import attr
import yaml
import click

from moin2hugo.config import load_config, Config
from moin2hugo.moin_parser import MoinParser
from moin2hugo.moinutils import unquoteWikiname
from moin2hugo.formatter import HugoFormatter
from moin2hugo.formatter.hugo import encode_hugo_name, page_to_hugo_bundle_path, safe_path_join
from moin2hugo.formatter.hugo import create_frontmatter

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


class Moin2Hugo(object):
    BRANCH_BUNDLE = 1
    LEAF_BUNDLE = 2

    def __init__(self, src_dir: str, dst_dir: str, config: Optional[Config] = None):
        if config:
            self.config = config
        else:
            self.config = Config()
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self._hugo_site_structure = None

    @property
    def hugo_site_structure(self):
        if self._hugo_site_structure is not None:
            return self._hugo_site_structure

        self._hugo_site_structure = {}
        for page in self.scan_pages(self.src_dir):
            elems = page.name.split("/")
            for i in range(len(elems) - 1):
                branch_path = "/".join(elems[:i+1])
                self._hugo_site_structure[branch_path] = self.BRANCH_BUNDLE
            leaf_path = page.name
            if leaf_path not in self._hugo_site_structure:
                self._hugo_site_structure[leaf_path] = self.LEAF_BUNDLE
        return self._hugo_site_structure

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

    def scan_pages(self, page_dir: str) -> Iterator[MoinPageInfo]:
        for entry in os.scandir(page_dir):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue

            logger.debug("+ Page Found: %s" % unquoteWikiname(entry.name))
            page = self._scan_page(entry.name, page_dir)
            if page is not None:
                yield page

    def convert_page(self, page: MoinPageInfo):
        logger.debug("++ filepath: %s" % page.filepath)
        with open(page.filepath, 'r') as f:
            content = f.read()
        page_obj = MoinParser.parse(content, page.name,
                                    site_config=self.config.moin_site_config)

        logger.debug("++ translate")
        converted = HugoFormatter.format(page_obj, pagename=page.name,
                                         config=self.config.hugo_config)

        hugo_bundle_path = page_to_hugo_bundle_path(page.name)
        hugo_bundle_path = safe_path_join(self.dst_dir, hugo_bundle_path)
        os.makedirs(hugo_bundle_path, exist_ok=True)

        if self.hugo_site_structure[page.name] == self.LEAF_BUNDLE:
            dst_filepath = safe_path_join(hugo_bundle_path, "index.md")
        elif self.hugo_site_structure[page.name] == self.BRANCH_BUNDLE:
            dst_filepath = safe_path_join(hugo_bundle_path, "_index.md")

        frontmatter = create_frontmatter(page.name, updated=page.updated)

        logger.info("++ output: %s" % dst_filepath)
        with open(dst_filepath, 'w') as f:
            f.write(frontmatter)
            f.write("\n\n")
            f.write(converted)

        if page.attachments:
            logger.info("++ copy attachments")
            for attachment in page.attachments:
                attachfile_hugo_name = encode_hugo_name(attachment.name)
                dst_path = safe_path_join(hugo_bundle_path, attachfile_hugo_name)
                shutil.copy(attachment.filepath, dst_path)

    def convert(self):
        logger.info("+ Source Moin Dir: %s" % self.src_dir)
        logger.info("+ Dest Dir: %s" % self.dst_dir)

        if os.path.exists(self.dst_dir):
            logger.info("++ destionation path exists")
            if os.path.isdir(self.dst_dir):
                logger.info("++ remove first")
                shutil.rmtree(self.dst_dir)
            else:
                raise ValueError("dst_dir must be non-existing path or directory path")
        logger.info("")

        for page in self.scan_pages(self.src_dir):
            logger.info("+ Convert Page: %s" % page.name)
            self.convert_page(page)
            logger.info("++ done.")


def config_logger(verbose: bool):
    app_logger = logging.getLogger('moin2hugo')
    app_logger.propagate = False
    handler = logging.StreamHandler()
    if verbose:
        app_logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        app_logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    app_logger.addHandler(handler)


@click.command()
@click.argument('src', type=click.Path(exists=True))
@click.argument('dst', type=click.Path())
@click.option('--config', '-c', 'configfile', type=click.Path(exists=True), default=None)
@click.option('--verbose', '-v', 'verbose', type=bool, default=None, is_flag=True)
def convert_site(src: str, dst: str, configfile: Optional[str], verbose: bool):
    '''Convert MoinMoin site directory to Hugo content directory.
    '''
    config_logger(verbose)
    if configfile:
        with open(configfile, 'r') as f:
            config_data = f.read()
        config_dict = yaml.safe_load(config_data)
        config = load_config(config_dict)
    else:
        config = Config()
    moin2hugo = Moin2Hugo(src, dst, config=config)
    moin2hugo.convert()
