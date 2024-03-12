__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from pathlib import Path

from pyschematron.direct_mode.lib.ast_visitors import ResolveExtendsVisitor, \
    ResolveAbstractPatternsVisitor, PhaseSelectionVisitor
from pyschematron.direct_mode.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.direct_mode.svrl.svrl_report import DefaultSVRLReportBuilder
from pyschematron.direct_mode.validators.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml_document


'''
cd programming/python/pyschematron/tests/fixtures/full_example/
java -jar ~/programming/java/schxslt-cli.jar -d cargo.xml -s schema.sch -o /tmp/report.xml
'''

example_path = Path('../tests/fixtures/full_example/')
schematron_path = Path(example_path / 'schema.sch')
phase = '#ALL'

schematron_xml = load_xml_document(schematron_path)
parsing_context = ParsingContext(base_path=schematron_path.parent)

schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot(), parsing_context)
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
schema = PhaseSelectionVisitor(schema, phase).apply(schema)

validator = SimpleSchematronXMLValidator(schema, '#ALL', parsing_context.base_path)

xml_document = load_xml_document(example_path / 'cargo.xml')
validation_results = validator.validate_xml(xml_document)

svrl_report = DefaultSVRLReportBuilder().create_svrl(validation_results)
print(svrl_report)

