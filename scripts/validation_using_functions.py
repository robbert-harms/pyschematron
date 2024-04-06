__author__ = 'Robbert Harms'
__date__ = '2024-04-01'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path
from pyschematron import validate_document

example_path = Path('../tests/fixtures/full_example/')
result = validate_document(example_path / 'cargo.xml', example_path / 'schema.sch')

svrl = result.get_svrl()
is_valid = result.is_valid()
