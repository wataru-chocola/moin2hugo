import os.path


def safe_path_join(basepath: str, path: str):
    basepath = os.path.normpath(basepath)
    joined = os.path.normpath(os.path.join(basepath, path))
    if os.path.commonpath([joined, basepath]) != basepath:
        raise ValueError("not allowed path traversal: path=%s" % path)
    return joined
