import logging
import os
import shutil
from datetime import datetime
from typing import List, Optional

import attr
import click
import jinja2
import yaml

from moin2hugo import __version__
from moin2hugo.config import Config, load_config
from moin2hugo.formatter import HugoFormatter
from moin2hugo.moin_parser import MoinParser
from moin2hugo.moin_site_scanner import MoinAttachment, MoinPageInfo, MoinSiteScanner
from moin2hugo.path_builder import HugoPathBuilder
from moin2hugo.utils import safe_path_join, set_console_handlers

logger = logging.getLogger(__name__)


@attr.s(frozen=True)
class HugoPageInfo:
    filepath: str = attr.ib()
    name: str = attr.ib()
    title: str = attr.ib()
    attachments: List[MoinAttachment] = attr.ib()
    is_branch: bool = attr.ib(default=False)
    updated: Optional[datetime] = attr.ib(default=None)


class Moin2Hugo(object):
    BRANCH_BUNDLE = 1
    LEAF_BUNDLE = 2

    def __init__(self, src_dir: str, dst_dir: str, config: Optional[Config] = None):
        if config is not None:
            self.config = config
        else:
            self.config = Config()
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self._hugo_site_structure = None

        self.moin_site_scanner = MoinSiteScanner(self.src_dir)
        self.path_builder = HugoPathBuilder(
            page_front_page=self.config.moin_site_config.page_front_page,
            root_path=self.config.hugo_config.root_path,
            disable_path_to_lower=self.config.hugo_config.disable_path_to_lower,
            remove_path_accents=self.config.hugo_config.remove_path_accents,
        )

    @property
    def hugo_site_structure(self):
        if self._hugo_site_structure is not None:
            return self._hugo_site_structure

        self._hugo_site_structure = {}
        for page in self.moin_site_scanner.scan_pages():
            hugo_bundle_path = self.path_builder.page_to_hugo_bundle_path(page.name)
            elems = hugo_bundle_path.split("/")
            for i in range(len(elems) - 1):
                branch_path = "/".join(elems[: i + 1])
                self._hugo_site_structure[branch_path] = self.BRANCH_BUNDLE
            if hugo_bundle_path not in self._hugo_site_structure:
                self._hugo_site_structure[hugo_bundle_path] = self.LEAF_BUNDLE

        if "" in self._hugo_site_structure:
            # make top page into branch bandle
            self._hugo_site_structure[""] = self.BRANCH_BUNDLE
        return self._hugo_site_structure

    def render_page(self, page: HugoPageInfo, content: str) -> str:
        if self.config.template_file:
            tmpl_dir, tmpl_file = os.path.split(self.config.template_file)
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(tmpl_dir))
        else:
            tmpl_file = "page.tmpl"
            env = jinja2.Environment(loader=jinja2.PackageLoader("moin2hugo", "templates"))

        tmpl = env.get_template(tmpl_file)
        ret = tmpl.render(page=page, content=content)
        return ret

    def convert_page(self, page: MoinPageInfo):
        logger.debug("++ filepath: %s" % page.filepath)
        with open(page.filepath, "r") as f:
            content = f.read()
        page_obj = MoinParser.parse(
            content,
            page.name,
            site_config=self.config.moin_site_config,
            strict_mode=self.config.strict_mode,
        )

        logger.debug("++ translate")
        converted = HugoFormatter.format(
            page_obj,
            pagename=page.name,
            path_builder=self.path_builder,
            config=self.config.hugo_config,
        )

        hugo_bundle_path = self.path_builder.page_to_hugo_bundle_path(page.name)
        dst_bundle_path = safe_path_join(self.dst_dir, hugo_bundle_path)
        os.makedirs(dst_bundle_path, exist_ok=True)

        is_branch = False
        if self.hugo_site_structure[hugo_bundle_path] == self.LEAF_BUNDLE:
            dst_filepath = safe_path_join(dst_bundle_path, "index.md")
        elif self.hugo_site_structure[hugo_bundle_path] == self.BRANCH_BUNDLE:
            dst_filepath = safe_path_join(dst_bundle_path, "_index.md")
            is_branch = True

        title = page.name.split("/")[-1]
        hugo_page = HugoPageInfo(
            filepath=dst_filepath,
            name=page.name,
            title=title,
            attachments=page.attachments,
            updated=page.updated,
            is_branch=is_branch,
        )

        logger.info("++ output: %s" % dst_filepath)
        with open(dst_filepath, "w") as f:
            f.write(self.render_page(hugo_page, converted))

        if page.attachments:
            logger.info("++ copy attachments")
            for attachment in page.attachments:
                attach_filepath = self.path_builder.attachment_filepath(page.name, attachment.name)
                dst_path = safe_path_join(self.dst_dir, attach_filepath)
                shutil.copy(attachment.filepath, dst_path)

    def convert(self, pagename: Optional[str] = None):
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

        for page in self.moin_site_scanner.scan_pages():
            if pagename and page.name != pagename:
                continue
            logger.info("+ Convert Page: %s" % page.name)
            try:
                self.convert_page(page)
            except AssertionError as e:
                logger.error("fail to convert.")
                logger.exception(e)
                continue
            logger.info("++ done.")


def config_logger(verbose: bool, debug: bool):
    app_logger = logging.getLogger("moin2hugo")
    app_logger.propagate = False
    for handler in app_logger.handlers:
        app_logger.removeHandler(handler)
    set_console_handlers(app_logger, verbose, debug)

    cssutils_logger = logging.getLogger("CSSUTILS")
    cssutils_logger.propagate = False
    for handler in cssutils_logger.handlers:
        cssutils_logger.removeHandler(handler)
    set_console_handlers(cssutils_logger, verbose, debug)


def print_version():
    click.echo(__version__)


def cmd_print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    print_version()
    ctx.exit()


@click.command()
@click.argument("src", type=click.Path(exists=True))
@click.argument("dst", type=click.Path())
@click.option(
    "--pagename",
    "-p",
    "pagename",
    metavar="PAGENAME",
    help="Pagename to be converted",
    default=None,
)
@click.option("--config", "-c", "configfile", type=click.Path(exists=True), default=None)
@click.option("--verbose", "-v", "verbose", type=bool, default=False, is_flag=True)
@click.option("--debug", "-d", "debug", type=bool, default=False, is_flag=True)
@click.option(
    "--version",
    "-V",
    "version",
    help="Show version and exit.",
    is_flag=True,
    callback=cmd_print_version,
    is_eager=True,
    expose_value=False,
)
def convert_site(
    src: str,
    dst: str,
    configfile: Optional[str],
    pagename: Optional[str],
    verbose: bool,
    debug: bool,
):
    """Convert MoinMoin pages directory to Hugo content directory.

    \b
    SRC is the MoinMoin pages directory to convert (e.g. yourwiki/data/pages)
    DST is the output directory
    """
    if debug:
        verbose = True
    config_logger(verbose, debug)
    if configfile:
        with open(configfile, "r") as f:
            config_data = f.read()
        config_dict = yaml.safe_load(config_data)
        config = load_config(config_dict)
    else:
        config = Config()
    moin2hugo = Moin2Hugo(src, dst, config=config)
    moin2hugo.convert(pagename=pagename)
