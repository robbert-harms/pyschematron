__author__ = 'Robbert Harms'
__date__ = '2020-02-04'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'


from importlib import metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import toml

try:
    __version__ = metadata.version('pyschematron')
except PackageNotFoundError:
    with open(Path(__file__).parent.parent / 'pyproject.toml') as f:
        pyproject = toml.load(f)
        __version__ = pyproject['project']['version']
