import sys
import os.path
import logging

from typing import Optional


def safe_path_join(basepath: str, path: str):
    basepath = os.path.normpath(basepath)
    joined = os.path.normpath(os.path.join(basepath, path))
    if os.path.commonpath([joined, basepath]) != basepath:
        raise ValueError("not allowed path traversal: path=%s" % path)
    return joined


class LogLevelFilter(logging.Filter):
    def __init__(self, min_level: Optional[int] = None, max_level: Optional[int] = None):
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return ((self.min_level is None or (record.levelno >= self.min_level)) and
                (self.max_level is None or (record.levelno <= self.max_level)))


def set_console_handlers(logger: logging.Logger, verbose: bool = False):
    stdout_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        logger.setLevel(logging.DEBUG)
        stdout_handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(LogLevelFilter(max_level=logging.INFO))
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(LogLevelFilter(min_level=logging.WARNING))
    logger.addHandler(stderr_handler)
