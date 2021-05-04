import os.path

pytoml = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
if os.path.isfile(pytoml):
    import toml

    __version__ = toml.load(open(pytoml))["tool"]["poetry"]["version"]
else:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("moin2hugo").version
