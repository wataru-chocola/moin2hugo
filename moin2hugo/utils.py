import urllib.parse
import os.path
from typing import Dict, Union


def page_to_hugo_filepath(pagename: str, disable_path_to_lower: bool = False) -> str:
    # encode punctuation which has special meaining in shell
    punctuation = """ !"#$%&'()*+,;<=>?@[\\]^`{|}~"""
    trans_dict: Dict[str, Union[int, str, None]] = dict([(c, "%%%02x" % ord(c)) for c in punctuation])  # noqa
    filepath = pagename.translate(str.maketrans(trans_dict))
    if not disable_path_to_lower:
        filepath = filepath.lower()
    return filepath


def page_url(pagename: str) -> str:
    # TODO
    return urllib.parse.quote("url/" + pagename)


def attachment_filepath(pagename: str, filename: str) -> str:
    # TODO
    filepath = "filepath/" + pagename + "/" + filename
    return filepath


def attachment_url(pagename: str, filename: str) -> str:
    # TODO
    url = urllib.parse.quote("url/" + pagename + "/" + filename)
    return url


def safe_path_join(basepath: str, path: str):
    basepath = os.path.normpath(basepath)
    joined = os.path.normpath(os.path.join(basepath, path))
    if os.path.commonpath([joined, basepath]) != basepath:
        raise ValueError("not allowed path traversal: path=%s" % path)
    return joined
