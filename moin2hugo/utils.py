import urllib.parse
import os.path
from typing import Dict, Union, Optional


def escape_hugo_name(name: str) -> str:
    # encode punctuation which has special meaining in shell
    punctuation = """ !"#$%&'()*+,;<=>?@[\\]^`{|}~:"""
    trans_dict: Dict[str, Union[int, str, None]] = dict([(c, "%%%02x" % ord(c)) for c in punctuation])  # noqa
    escaped_name = name.translate(str.maketrans(trans_dict))
    return escaped_name


def page_to_hugo_bundle_path(pagename: str) -> str:
    return escape_hugo_name(pagename)


def attachment_filepath(pagename: str, filename: str) -> str:
    attachfile_hugo_name = escape_hugo_name(filename)
    hugo_bundle_path = page_to_hugo_bundle_path(pagename)
    filepath = safe_path_join(hugo_bundle_path, attachfile_hugo_name)
    return filepath


def page_url(pagename: str, relative_base: Optional[str] = None,
             disable_path_to_lower: bool = False) -> str:
    url = pagename
    if relative_base:
        target_path_elems = pagename.split("/")
        relative_base_elems = relative_base.split("/")
        if len(target_path_elems) >= len(relative_base_elems):
            for elem in relative_base_elems:
                if target_path_elems[0] != elem:
                    break
                target_path_elems.pop(0)
            else:
                url = "/".join(target_path_elems)

    if not disable_path_to_lower:
        url = url.lower()
    return url


def attachment_url(pagename: str, filename: str, disable_path_to_lower: bool = False) -> str:
    # TODO
    url = urllib.parse.quote("url/" + pagename + "/" + filename)
    if not disable_path_to_lower:
        url = url.lower()
    return url


def safe_path_join(basepath: str, path: str):
    basepath = os.path.normpath(basepath)
    joined = os.path.normpath(os.path.join(basepath, path))
    if os.path.commonpath([joined, basepath]) != basepath:
        raise ValueError("not allowed path traversal: path=%s" % path)
    return joined
