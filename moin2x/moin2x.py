import logging
import os
import shutil
from typing import Optional, Protocol

from moin2x.moin_site_scanner import MoinPageInfo, MoinSiteScanner

logger = logging.getLogger(__name__)


class Moin2XConverter(Protocol):
    def convert_page(self, page: MoinPageInfo):
        ...


def convert_site(
    src_dir: str, dst_dir: str, converter: Moin2XConverter, pagename: Optional[str] = None
):
    logger.info("+ Source Moin Dir: %s" % src_dir)
    logger.info("+ Dest Dir: %s" % dst_dir)

    if os.path.exists(dst_dir):
        logger.info("++ destionation path exists")
        if os.path.isdir(dst_dir):
            logger.info("++ remove first")
            shutil.rmtree(dst_dir)
        else:
            raise ValueError("dst_dir must be non-existing path or directory path")
    logger.info("")

    moin_site_scanner = MoinSiteScanner(src_dir)

    for page in moin_site_scanner.scan_pages():
        if pagename and page.name != pagename:
            continue
        logger.info("+ Convert Page: %s" % page.name)
        try:
            converter.convert_page(page)
        except AssertionError as e:
            logger.error("fail to convert: %s." % page.name)
            logger.exception(e)
            continue
        except Exception:
            logger.error("fail to convert: %s." % page.name)
            raise
        logger.info("++ done.")
