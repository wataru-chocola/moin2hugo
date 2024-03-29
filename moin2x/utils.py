import inspect
import logging
import os.path
import sys
from typing import Optional


def safe_path_join(basepath: str, path: str):
    basepath = os.path.normpath(basepath)
    if basepath == os.path.curdir:
        return os.path.normpath(path)

    joined = os.path.normpath(os.path.join(basepath, path))
    if os.path.commonpath([joined, basepath]) != basepath:
        raise ValueError("not allowed path traversal: path=%s" % path)
    return joined


class LogLevelFilter(logging.Filter):
    def __init__(self, min_level: Optional[int] = None, max_level: Optional[int] = None):
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return (self.min_level is None or (record.levelno >= self.min_level)) and (
            self.max_level is None or (record.levelno <= self.max_level)
        )


def get_target_pagename() -> Optional[str]:
    stack = inspect.stack()
    for frame_info in stack:
        if frame_info.function in ["convert_page", "convert"]:
            frame = frame_info.frame
            page = frame.f_locals.get("page")
            if page is None:
                return None
            return page.name
    return None


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        pagename = get_target_pagename()
        record.pagename = "-"  # type: ignore
        if pagename:
            record.pagename = pagename  # type: ignore
        return True


def set_console_handlers(logger: logging.Logger, verbose: bool = False, debug: bool = False):
    if verbose:
        stdout_handler = logging.StreamHandler(sys.stdout)
        if debug:
            logger.setLevel(logging.DEBUG)
            stdout_handler.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            stdout_handler.setLevel(logging.INFO)
        stdout_handler.addFilter(LogLevelFilter(max_level=logging.INFO))
        logger.addHandler(stdout_handler)

    error_formmater = logging.Formatter(fmt="%(pagename)s: [%(levelname)s] %(message)s")
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(error_formmater)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(LogLevelFilter(min_level=logging.WARNING))
    stderr_handler.addFilter(ContextFilter())
    logger.addHandler(stderr_handler)
