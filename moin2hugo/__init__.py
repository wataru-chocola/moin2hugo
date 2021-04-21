import toml
import os.path

pytoml = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
__version__ = toml.load(open(pytoml))['tool']['poetry']['version']
