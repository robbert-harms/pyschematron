__author__ = 'Robbert Harms'
__date__ = '2020-02-04'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@laltoida.com'


from importlib import metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import tomllib

try:
    __version__ = metadata.version('pyschematron')
except PackageNotFoundError:
    with open(Path(__file__).parent.parent / 'pyproject.toml', 'rb') as f:
        pyproject = tomllib.load(f)
        __version__ = pyproject['project']['version']
