import logging
import os
import shutil
from datetime import datetime
from typing import Optional

import attr
import jinja2

from moin2kibun.config import Config
from moin2kibun.formatter import KibunFormatter
from moin2kibun.path_builder import KibunPathBuilder
from moin2x.moin2x import Moin2XConverter
from moin2x.moin_parser import MoinParser
from moin2x.moin_site_scanner import MoinAttachment, MoinPageInfo
from moin2x.utils import safe_path_join

logger = logging.getLogger(__name__)


@attr.s(frozen=True)
class KibunPageInfo:
    filepath: str = attr.ib()
    name: str = attr.ib()
    title: str = attr.ib()
    attachments: set[MoinAttachment] = attr.ib()
    updated: Optional[datetime] = attr.ib(default=None)


class Moin2Kibun(Moin2XConverter, object):
    def __init__(self, src_dir: str, dst_dir: str, config: Optional[Config] = None):
        if config is not None:
            self.config = config
        else:
            self.config = Config()
        self.src_dir = src_dir
        self.dst_dir = dst_dir

        self.path_builder = KibunPathBuilder(
            page_front_page=self.config.moin_site_config.page_front_page,
            root_path=self.config.format_config.root_path,
            disable_path_to_lower=self.config.format_config.disable_path_to_lower,
            remove_path_accents=self.config.format_config.remove_path_accents,
        )

        if self.config.template_file:
            tmpl_dir, tmpl_file = os.path.split(self.config.template_file)
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(tmpl_dir))
        else:
            tmpl_file = "page.tmpl"
            env = jinja2.Environment(loader=jinja2.PackageLoader("moin2kibun", "templates"))

        self.page_tmpl = env.get_template(tmpl_file)

    def render_page(self, page: KibunPageInfo, content: str) -> str:
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
        converted = KibunFormatter.format(
            page_obj,
            pagename=page.name,
            path_builder=self.path_builder,
            config=self.config.format_config,
        )

        page_filepath = self.path_builder.page_filepath(page.name)
        dst_filepath = safe_path_join(self.dst_dir, page_filepath)
        os.makedirs(os.path.dirname(dst_filepath), exist_ok=True)

        title = page.name.split("/")[-1]
        kibun_page = KibunPageInfo(
            filepath=dst_filepath,
            name=page.name,
            title=title,
            attachments=page.attachments,
            updated=page.updated,
        )

        logger.info("++ output: %s" % dst_filepath)
        with open(dst_filepath, "w") as f:
            f.write(self.render_page(kibun_page, converted))

        if page.attachments:
            logger.info("++ copy attachments")
            for attachment in page.attachments:
                attach_filepath = self.path_builder.attachment_filepath(page.name, attachment.name)
                dst_path = safe_path_join(self.dst_dir, attach_filepath)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy(attachment.filepath, dst_path)
