__author__ = 'Robbert Harms'
__date__ = '2024-04-01'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path

from lxml import etree

from pyschematron.direct_mode.api import DirectModeSchematronValidatorFactory

example_path = Path('../tests/fixtures/full_example/')

validator_factory = DirectModeSchematronValidatorFactory()
validator_factory.set_schema(example_path / 'schema.sch')
validator_factory.set_phase('#ALL')

validator = validator_factory.build()
validation_result = validator.validate(example_path / 'cargo.xml')

svrl = validation_result.get_svrl()

report_str = etree.tostring(svrl, pretty_print=True).decode('utf-8')
print(report_str)
print(validation_result.is_valid())
