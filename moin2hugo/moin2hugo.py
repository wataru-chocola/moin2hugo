import os
import logging
from dataclasses import dataclass
from typing import Iterator, List, Optional

import yaml
import click

from moin2hugo.config import load_config, Config
from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter import Formatter
from moin2hugo.moinutils import unquoteWikiname

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MoinAttachment:
    filepath: str
    name: str


@dataclass(frozen=True)
class MoinPageInfo:
    filepath: str
    name: str
    attachments: List[MoinAttachment]


class Moin2Hugo(object):
    def __init__(self, src_dir: str, dst_dir: str, config: Optional[Config] = None):
        if config:
            self.config = config
        else:
            self.config = Config()
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def scan_pages(self, page_dir: str) -> Iterator[MoinPageInfo]:
        for entry in os.scandir(page_dir):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue

            logger.debug("+ Page Found: %s" % unquoteWikiname(entry.name))
            pagedir = os.path.join(page_dir, entry.name)
            try:
                current_file = os.path.join(pagedir, 'current')
                with open(current_file, 'r') as f:
                    current_revision = f.read().rstrip()
            except FileNotFoundError:
                continue

            content_file = os.path.join(pagedir, 'revisions', current_revision)
            if not os.path.isfile(content_file):
                # TODO: page deleted?
                logger.error("+ Not found: %s/revisions/%s" % (entry.name, current_revision))
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
        formatter = Formatter(config=self.config.hugo_config)
        for page in self.scan_pages(self.src_dir):
            with open(page.filepath, 'r') as f:
                content = f.read()
            page_obj = MoinParser.parse(content, page.name,
                                        site_config=self.config.moin_site_config)
            logger.info("+ Convert Page: %s" % page.name)
            logger.debug("+ Filepath: %s" % page.filepath)
            converted = formatter.format(page_obj)
            # TODO: do something
            # TODO: page.attachments
            logger.info("+ Done.")
            logger.info("")


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
    '''Convert moinmoin site directory into hugo's content directory.
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
