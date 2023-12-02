import logging
import os
import shutil
from datetime import datetime
from typing import Literal, Optional, assert_never

import attr
import jinja2

from moin2hugo.config import Config
from moin2hugo.formatter import HugoFormatter
from moin2hugo.path_builder import HugoPathBuilder
from moin2x.moin2x import Moin2XConverter
from moin2x.moin_parser import MoinParser
from moin2x.moin_site_scanner import MoinAttachment, MoinPageInfo, MoinSiteScanner
from moin2x.utils import safe_path_join

logger = logging.getLogger(__name__)


@attr.s(frozen=True)
class HugoPageInfo:
    filepath: str = attr.ib()
    name: str = attr.ib()
    title: str = attr.ib()
    attachments: set[MoinAttachment] = attr.ib()
    is_branch: bool = attr.ib(default=False)
    updated: Optional[datetime] = attr.ib(default=None)


PAGE_TYPE = Literal[1] | Literal[2]


class Moin2Hugo(Moin2XConverter, object):
    BRANCH_BUNDLE = 1
    LEAF_BUNDLE = 2

    def __init__(self, src_dir: str, dst_dir: str, config: Optional[Config] = None):
        if config is not None:
            self.config = config
        else:
            self.config = Config()
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self._hugo_site_structure: Optional[dict[str, PAGE_TYPE]] = None

        self.path_builder = HugoPathBuilder(
            page_front_page=self.config.moin_site_config.page_front_page,
            root_path=self.config.hugo_config.root_path,
            disable_path_to_lower=self.config.hugo_config.disable_path_to_lower,
            remove_path_accents=self.config.hugo_config.remove_path_accents,
        )

        if self.config.template_file:
            tmpl_dir, tmpl_file = os.path.split(self.config.template_file)
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(tmpl_dir))
        else:
            tmpl_file = "page.tmpl"
            env = jinja2.Environment(loader=jinja2.PackageLoader("moin2hugo", "templates"))

        self.page_tmpl = env.get_template(tmpl_file)

    @property
    def hugo_site_structure(self) -> dict[str, PAGE_TYPE]:
        if self._hugo_site_structure is not None:
            return self._hugo_site_structure

        self._hugo_site_structure = {}
        moin_site_scanner = MoinSiteScanner(self.src_dir)
        for page in moin_site_scanner.scan_pages():
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
        ret = self.page_tmpl.render(page=page, content=content)
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
        match self.hugo_site_structure[hugo_bundle_path]:
            case self.LEAF_BUNDLE:
                dst_filepath = safe_path_join(dst_bundle_path, "index.md")
            case self.BRANCH_BUNDLE:
                dst_filepath = safe_path_join(dst_bundle_path, "_index.md")
                is_branch = True
            case _ as unreachable:  # type: ignore
                assert_never(unreachable)

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
